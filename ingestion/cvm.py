"""Ingestão dos dados abertos da CVM (DFP, ITR e cadastro) para o schema raw do PostgreSQL.

Rode (com o venv ativo, na raiz do projeto):
    python ingestion/cvm.py                         # tudo
    python ingestion/cvm.py --docs dfp --anos 2025  # só um pedaço

Pode rodar quantas vezes quiser: arquivo que não mudou na CVM não é baixado nem carregado de novo.
"""
import argparse
import csv
import hashlib
import io
import os
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import psycopg
import requests
from dotenv import load_dotenv

BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA"
PASTAS = {"dfp": f"{BASE}/DOC/DFP/DADOS/", "itr": f"{BASE}/DOC/ITR/DADOS/"}
URL_CAD = f"{BASE}/CAD/DADOS/cad_cia_aberta.csv"

# Demonstrações do MVP. DMPL, DRA, DVA e parecer ficam de fora por enquanto: muito volume e pouco uso nas métricas.
DEMONSTRACOES = {"BPA", "BPP", "DRE", "DFC_MD", "DFC_MI"}

# Só dados da empresa. Nome, e-mail e telefone dos responsáveis ficam de fora (dados pessoais, sem uso no projeto).
COLUNAS_CAD = [
    "CNPJ_CIA", "DENOM_SOCIAL", "DENOM_COMERC", "DT_REG", "DT_CONST", "DT_CANCEL", "MOTIVO_CANCEL",
    "SIT", "DT_INI_SIT", "CD_CVM", "SETOR_ATIV", "TP_MERC", "CATEG_REG", "DT_INI_CATEG",
    "SIT_EMISSOR", "DT_INI_SIT_EMISSOR", "CONTROLE_ACIONARIO", "MUN", "UF", "PAIS", "CNPJ_AUDITOR", "AUDITOR",
]

# Os ZIPs ficam fora do OneDrive, como o venv, para não sincronizar centenas de MB.
RAW_DIR = Path(os.getenv("RAW_DIR", "~/.local/share/projeto-sp-data/raw")).expanduser()

http = requests.Session()


def conectar():
    load_dotenv()
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB"),
    )


def preparar_banco(conn):
    """Cria o schema raw e a tabela de controle, que lembra o que já foi carregado."""
    conn.execute("create schema if not exists raw")
    conn.execute("""
        create table if not exists raw._controle_cargas (
            arquivo        text primary key,
            url            text not null,
            last_modified  text,          -- data de alteração informada pelo servidor da CVM
            sha256         text,          -- impressão digital do arquivo; muda se o conteúdo mudar
            linhas         bigint,
            carregado_em   timestamptz
        )""")
    conn.commit()


def listar_zips(tipo, anos):
    """Lê a página da CVM e devolve [(nome, url)] dos ZIPs anuais disponíveis."""
    html = http.get(PASTAS[tipo], timeout=60).text
    nomes = sorted(set(re.findall(rf'href="({tipo}_cia_aberta_(\d{{4}})\.zip)"', html)))
    return [(nome, PASTAS[tipo] + nome) for nome, ano in nomes if not anos or int(ano) in anos]


def baixar_se_mudou(conn, nome, url):
    """Baixa o arquivo só se ele mudou na CVM. Devolve (caminho, sha256, last_modified) ou None se nada mudou."""
    controle = conn.execute(
        "select last_modified, sha256 from raw._controle_cargas where arquivo = %s", (nome,)
    ).fetchone()
    caminho = RAW_DIR / nome

    # 1ª checagem, barata: o servidor diz quando o arquivo mudou (HEAD não baixa o conteúdo).
    last_modified = http.head(url, timeout=60).headers.get("Last-Modified")
    if controle and last_modified and controle[0] == last_modified and caminho.exists():
        return None

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".parcial")
    with http.get(url, stream=True, timeout=300) as resp:
        resp.raise_for_status()
        with open(temporario, "wb") as f:
            for bloco in resp.iter_content(1 << 20):
                f.write(bloco)
    temporario.replace(caminho)  # só troca o arquivo quando o download terminou inteiro

    # 2ª checagem: a data pode mudar sem o conteúdo mudar. O hash compara o conteúdo de fato.
    sha256 = hashlib.sha256(caminho.read_bytes()).hexdigest()
    if controle and controle[1] == sha256:
        conn.execute("update raw._controle_cargas set last_modified = %s where arquivo = %s", (last_modified, nome))
        conn.commit()
        return None
    return caminho, sha256, last_modified


def garantir_tabela(conn, tabela, colunas):
    """Cria a tabela (tudo como texto, igual à fonte) e acrescenta colunas novas se a CVM mudar o layout."""
    conn.execute(f"create table if not exists raw.{tabela} (_arquivo text not null, _carregado_em timestamptz not null)")
    for coluna in colunas:
        conn.execute(f"alter table raw.{tabela} add column if not exists {coluna} text")
    conn.execute(f"create index if not exists {tabela}_arquivo_idx on raw.{tabela} (_arquivo)")


def copiar(conn, tabela, nome, agora, cabecalho, linhas):
    """Grava as linhas com COPY, o jeito mais rápido de inserir em massa no PostgreSQL."""
    colunas = [c.lower() for c in cabecalho]
    garantir_tabela(conn, tabela, colunas)
    total = 0
    with conn.cursor().copy(f"copy raw.{tabela} (_arquivo, _carregado_em, {', '.join(colunas)}) from stdin") as cp:
        for numero, linha in enumerate(linhas, start=2):
            if len(linha) != len(cabecalho):
                raise ValueError(f"{nome}/{tabela}: linha {numero} tem {len(linha)} campos, esperado {len(cabecalho)}")
            cp.write_row((nome, agora, *linha))
            total += 1
    return total


def tabela_do_csv(tipo, membro):
    """dfp_cia_aberta_BPA_con_2025.csv -> dfp_bpa_con; dfp_cia_aberta_2025.csv -> dfp_documentos. None = ignorar."""
    m = re.fullmatch(rf"{tipo}_cia_aberta_(?:(.+)_)?\d{{4}}\.csv", membro)
    if not m:
        return None
    parte = m.group(1)
    if parte is None:
        return f"{tipo}_documentos"  # índice dos documentos entregues (versão, data de entrega etc.)
    demonstracao, _, escopo = parte.rpartition("_")
    if demonstracao in DEMONSTRACOES and escopo in ("con", "ind"):
        return f"{tipo}_{demonstracao.lower()}_{escopo}"
    return None


def carregar_zip(conn, tipo, nome, caminho):
    """Substitui no banco tudo o que veio deste ZIP. Numa transação só: ou carrega tudo, ou nada."""
    agora = datetime.now(timezone.utc)
    total = 0
    with zipfile.ZipFile(caminho) as z:
        for membro in z.namelist():
            tabela = tabela_do_csv(tipo, membro)
            if not tabela:
                continue
            conn.execute(f"create table if not exists raw.{tabela} (_arquivo text not null, _carregado_em timestamptz not null)")
            conn.execute(f"delete from raw.{tabela} where _arquivo = %s", (nome,))
            # A CVM publica em latin-1 com ";" como separador.
            leitor = csv.reader(io.TextIOWrapper(z.open(membro), encoding="latin-1", newline=""), delimiter=";")
            total += copiar(conn, tabela, nome, agora, next(leitor), leitor)
    return total, agora


def carregar_cadastro(conn, nome, caminho):
    """O cadastro é uma foto do dia. Guardamos cada foto nova (não apagamos as antigas) para ter o histórico de situação."""
    agora = datetime.now(timezone.utc)
    with open(caminho, encoding="latin-1", newline="") as f:
        leitor = csv.DictReader(f, delimiter=";")
        linhas = ([linha[c] for c in COLUNAS_CAD] for linha in leitor)
        return copiar(conn, "cad_cia_aberta", nome, agora, COLUNAS_CAD, linhas), agora


def registrar(conn, nome, url, sha256, last_modified, linhas, agora):
    conn.execute("""
        insert into raw._controle_cargas (arquivo, url, last_modified, sha256, linhas, carregado_em)
        values (%s, %s, %s, %s, %s, %s)
        on conflict (arquivo) do update set url = excluded.url, last_modified = excluded.last_modified,
            sha256 = excluded.sha256, linhas = excluded.linhas, carregado_em = excluded.carregado_em""",
        (nome, url, last_modified, sha256, linhas, agora))


def processar(conn, nome, url, carregar):
    try:
        baixado = baixar_se_mudou(conn, nome, url)
        if baixado is None:
            print(f"  {nome}: sem mudança")
            return
        caminho, sha256, last_modified = baixado
        linhas, agora = carregar(caminho)
        registrar(conn, nome, url, sha256, last_modified, linhas, agora)
        conn.commit()
        print(f"  {nome}: {linhas:,} linhas carregadas".replace(",", "."))
    except Exception:
        conn.rollback()  # o banco volta ao estado anterior; nada fica pela metade
        raise


def main():
    parser = argparse.ArgumentParser(description="Ingestão dos dados abertos da CVM")
    parser.add_argument("--docs", nargs="+", choices=["dfp", "itr", "cad"], default=["dfp", "itr", "cad"])
    parser.add_argument("--anos", nargs="+", type=int, help="padrão: todos os anos disponíveis")
    args = parser.parse_args()

    with conectar() as conn:
        preparar_banco(conn)
        for tipo in ("dfp", "itr"):
            if tipo in args.docs:
                print(f"==> {tipo.upper()}")
                for nome, url in listar_zips(tipo, args.anos):
                    processar(conn, nome, url, lambda caminho, t=tipo, n=nome: carregar_zip(conn, t, n, caminho))
        if "cad" in args.docs:
            print("==> Cadastro")
            processar(conn, "cad_cia_aberta.csv", URL_CAD, lambda caminho: carregar_cadastro(conn, "cad_cia_aberta.csv", caminho))


if __name__ == "__main__":
    main()
