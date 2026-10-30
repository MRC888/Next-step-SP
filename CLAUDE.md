# CLAUDE.md — Next Step SP

Este arquivo passa o contexto de uma conversa anterior (Claude no app, 20/10/2026) para o Claude Code. Leia inteiro antes de agir.

## Quem é o usuário
Marcelo Santos, 23 anos. Analista Fiscal/Financeiro na Assecon (contabilidade), cuidando de 22 empresas. Experiência **fiscal** (apuração de impostos, regimes tributários); pouca familiaridade com fechamento de balanço e DRE. Estuda Ciência da Computação na FIAP (PBL) e ADS na UNITAU.

Stack já demonstrada: SQL/PostgreSQL, Python (pandas, Matplotlib), Power BI (DAX), Tableau e Excel. Interesse principal: **engenharia de dados + AI engineering** (automação, ML, agentes). Programar por horas o cansa: prefere entender fundamentos e arquitetura. Escreva o código, mas **explique cada parte de forma metódica**, para que ele consiga explicar numa entrevista.

Preferências:
- Responder em português, de forma **simples e direta** (pedido de 21/10/2026): ler menos, entender mais.
- Explicar o porquê de cada decisão.
- Separar o que foi testado do que é hipótese.
- Nunca inflar resultados nem prometer "perfeito" sem evidência.
- **Regra fixa:** em toda tarefa, checar e avisar sobre agentes, plugins, MCPs, extensões ou ferramentas que melhorem o trabalho. Código sempre limpo, com boas práticas e de alto nível. Fundamentar em referências reais.
- ~~Um passo por vez, com pausa para Marcelo participar.~~ Substituído em 30/10/2026 pelo **modo automático** (abaixo).

## Modo automático (Marcelo, 30/10/2026)
"Automático" aqui quer dizer **sem pedir permissão a cada comando**, não fazer tudo de uma vez. O ritmo continua **bloco a bloco** (regra geral, 30/10/2026).
- Marcelo aprova o **plano de cada marco** (etapa 2 do método). Dentro do marco, faça **um bloco por vez**: editar, rodar, testar e corrigir até passar; mostrar o resultado; só então o próximo bloco.
- Pause só para: decisão de produto ou escopo, algo destrutivo (apagar dados ou volume do banco), push para o GitHub e qualquer coisa fora do plano.
- No fim de cada marco: resumo curto (o que mudou, o que foi testado e o que é hipótese) e o porquê das decisões principais, em linguagem de entrevista. Depois, `/fim-de-sessao`.
- As permissões ficam em `.claude/settings.json`: dbt, Python, Ruff, SQLFluff, Docker e Git local são liberados; push pergunta; `rm -rf`, `reset --hard` e leitura do `.env` são bloqueados.

## Documentação obrigatória
**Registre cada decisão e cada avanço** na nota do Obsidian, para auditoria por outras IAs:
`~/Library/CloudStorage/OneDrive-Pessoal/Obsidian/Documentação/Projetos/Next Step SP/Next Step SP.md`

Siga o formato da nota: tabela de Decisões (data, decisão, motivo), seções por etapa e Histórico. O vault inteiro está em `.../Obsidian/Documentação`; comece pela nota `Início.md`. Preserve o estilo das outras notas.

## O projeto
Proposta de Teo (amigo sênior): uma plataforma de dados ponta a ponta.
1. Ingestão automatizada.
2. Modelagem.
3. Camada semântica: regras de negócio e descrição dos dados, consumidas por uma IA que calcula as métricas conforme essas regras.
4. Agente de IA consultando os dados.
5. Machine learning.
6. Dashboard.

Divulgação: 6 posts do processo no LinkedIn, um por marco (plano na nota do Obsidian); o último é impulsionado, com portfólio e GitHub público. Todo post começa pelo problema em linguagem de leigo. Na imagem, a barra das 9 etapas mostra o progresso real e destaca a etapa do post ("▲ este post"). Roadmap: `~/Desktop/Roadmap - Next Step SP.html`.

Domínio: **financeiro**, aproveitando a experiência contábil de Marcelo.

Base: **CVM** (decidido em 21/10/2026). IF.data descartado.
- **CVM:** ITR/DFP de companhias abertas, em ZIP/CSV, atualização semanal com reapresentações. Escolhida: dinâmica, multissetorial, boa para ML.
- **IF.data (Banco Central):** dados trimestrais de bancos via API OData, desde 2000.
- Enriquecimento possível: API SGS do Banco Central (Selic, IPCA, câmbio).

Tempo: manhãs dedicadas até 28/10/2026, mas isso não é prazo final.

## Estado do ambiente (Mac Apple Silicon)
- Instalados: Python 3.13 (python.org), PostgreSQL 18 local na porta 5432, VS Code, DBeaver Community e Command Line Tools da Apple (Git).
- **Não instalados:** Docker e Homebrew.
- Pasta do projeto: `~/Library/CloudStorage/OneDrive-Pessoal/Estudo/Projetos/Next Step SP`. Ela fica no OneDrive por escolha de Marcelo, junto dos outros projetos. O ambiente Python fica em `~/.venvs/projeto-sp-data`, fora do OneDrive. Cuidado: o OneDrive sincroniza a pasta `.git`. Use o GitHub como backup e evite editar o projeto em dois computadores ao mesmo tempo.
- Esta pasta já tem: `docker-compose.yml` (PostgreSQL 17 na porta **5433**), `.env.example`, `.gitignore`, `requirements.txt`, `scripts/check_env.py`, `setup.sh` e `README.md`.
- O `.env` ainda não existe: o `setup.sh` cria, com senha aleatória. **Nunca commitar o `.env`.**
- A pasta antiga `~/Projetos` (versão anterior deste projeto) foi removida, ou deve ser, se ainda existir.

## Estado do ambiente (21/10/2026): pronto
- Docker Desktop instalado; CLI em `~/.docker/bin` (no PATH via `~/.zprofile`).
- Banco no ar: container `sp_data_postgres`, PostgreSQL 17, porta 5433.
- O `docker-compose.yml` fixa o nome do projeto Docker em `projetosp-dataadvanced` (nome antigo da pasta). Não mudar: é dele que sai o nome do volume com os dados. Sem ele, renomear a pasta criaria um banco vazio. `./setup.sh` → "Tudo pronto!".
- VS Code configurado (`.vscode/`). DBeaver "SP Data" autentica via `~/.pgpass`.
- Ingestão pronta: `ingestion/cvm.py` carrega DFP, ITR e cadastro no schema `raw` (35 mi linhas, ~9,7 GB). ZIPs em `~/.local/share/projeto-sp-data/raw`.
- GitHub: `MRC888/Next-step-SP`, privado. No Mac, o `gh` (`~/.local/bin`) está logado com a permissão `workflow`, e o Git usa esse login (`gh auth setup-git`); o Claude pode fazer push (com confirmação). O GitHub Desktop também funciona.
- CI: `.github/workflows/qualidade.yml` (pre-commit + `dbt parse`), verde desde 30/10/2026.

## Onde rodar (decisão de 30/10/2026)
**O Next Step SP roda só no Mac.** O banco (Docker, 2 a 9 GB, muda o tempo todo) fica só lá, com DFP, ITR e cadastro carregados. O PC fica como reserva: tem tudo instalado e a fatia fina DFP testada, mas sem ITR. Se um dia trabalhar no PC: pull antes, commit + push depois.

## Estado do ambiente (Windows, 30/10/2026)
Marcelo alterna entre o Mac e um PC Windows. A pasta sincroniza pelo OneDrive; as sessões do Claude não.
- OneDrive: `C:\Users\marce\OneDrive` (no Mac: `~/Library/CloudStorage/OneDrive-Pessoal`). Obsidian em `<OneDrive>/Obsidian/Documentação`.
- Instalados: Python 3.13, Git (`autocrlf=false`), VS Code com as extensões do projeto, GitHub CLI (**sem login**), DBeaver, pre-commit global e Docker Desktop (WSL2; VT-x ligado na BIOS).
- Venv: `~/.venvs/projeto-sp-data`, ativar com `~/.venvs/projeto-sp-data/Scripts/Activate.ps1`. No VS Code, escolher esse interpretador à mão (o `.vscode/settings.json` aponta para o do Mac).
- `bash setup.sh` pelo Git Bash → "Tudo pronto!". Banco do PC é separado do Mac: carregados DFP + cadastro (8,63 mi linhas, 2,3 GB). ITR ainda não carregado no PC.
- dbt: as variáveis do `.env` precisam estar no ambiente antes do `dbt build --profiles-dir .` (rodar dentro de `modeling/`).
- **Regra de troca de computador:** commit + push antes de sair de uma máquina; pull antes de começar na outra. Nunca editar nos dois ao mesmo tempo (o OneDrive sincroniza a `.git`).

## Próximas tarefas
Feito (30/10/2026): Marcos A, B, C (parcial), D, E e F. Guia completo em `docs/guia-de-estudo.md` e no Obsidian ("Next Step SP — Guia de estudo"). Comandos: `make`.
1. ~~Chave da API e prova do agente~~ feitas em 30/10/2026: **20/20, 4/4 pegadinhas** (US$ 1,03). Post 4 em rascunho; post 5 pronto.
2. **Nada roda automaticamente** (decisão de 30/10/2026): projeto de portfólio. Não ativar `make agendar`. Para usar: `make banco` e depois `make dashboard` ou `make pipeline`.
3. Revisar o `CLAUDE.md` (dados pessoais) antes de tornar o GitHub público; portfólio; post 6 (impulsionar).
4. Evoluções: métricas trimestrais (ITR), bancos, Selic/IPCA (SGS), calibrar a nota de risco, orquestrador, painel publicado.

## Outros projetos dele (para referência)
Foods and Goods (Kaggle, logística, SQL + Python), análise de honorários (caso real), TCC Barcelona e FIAP Aurora. Detalhes no vault. Observação: o CV de 20/10 diz MySQL para o Foods and Goods, mas o README registra PostgreSQL. Confirmar com ele.
