# CLAUDE.md — Projeto SP — Data advanced

Este arquivo passa o contexto de uma conversa anterior (Claude no app, 20/10/2026) para o Claude Code. Leia inteiro antes de agir.

## Quem é o usuário
Marcelo Santos, 23 anos. Analista Fiscal/Financeiro na Assecon (contabilidade), cuidando de 22 empresas. Estuda Ciência da Computação na FIAP (PBL) e ADS na UNITAU.

Stack já demonstrada: SQL/PostgreSQL, Python (pandas, Matplotlib), Power BI (DAX), Tableau e Excel. Interesse principal: **engenharia de dados + AI engineering** (automação, ML, agentes). Programar por horas o cansa: prefere entender fundamentos e arquitetura. Escreva o código, mas **explique cada parte de forma metódica**, para que ele consiga explicar numa entrevista.

Preferências:
- Responder em português.
- Explicar o porquê de cada decisão.
- Separar o que foi testado do que é hipótese.
- Nunca inflar resultados nem prometer "perfeito" sem evidência.

## Documentação obrigatória
**Registre cada decisão e cada avanço** na nota do Obsidian, para auditoria por outras IAs:
`~/Library/CloudStorage/OneDrive-Pessoal/Obsidian/Documentação/Projetos/Projeto SP - Data advanced/Projeto SP - Data advanced.md`

Siga o formato da nota: tabela de Decisões (data, decisão, motivo), seções por etapa e Histórico. O vault inteiro está em `.../Obsidian/Documentação`; comece pela nota `Início.md`. Preserve o estilo das outras notas.

## O projeto
Proposta de Teo (amigo sênior): uma plataforma de dados ponta a ponta.
1. Ingestão automatizada.
2. Modelagem.
3. Camada semântica: regras de negócio e descrição dos dados, consumidas por uma IA que calcula as métricas conforme essas regras.
4. Agente de IA consultando os dados.
5. Machine learning.
6. Dashboard.

Divulgação: dividir o projeto em vários posts no LinkedIn, um por etapa.

Domínio: **financeiro**, aproveitando a experiência contábil de Marcelo.

Base: **ainda não decidida.**
- **CVM:** ITR/DFP de companhias abertas, em ZIP/CSV, atualização semanal com reapresentações. Recomendada: contabilidade societária, que ele domina.
- **IF.data (Banco Central):** dados trimestrais de bancos via API OData, desde 2000.
- Enriquecimento possível: API SGS do Banco Central (Selic, IPCA, câmbio).

Tempo: manhãs dedicadas até 28/10/2026, mas isso não é prazo final.

## Estado do ambiente (Mac Apple Silicon)
- Instalados: Python 3.13 (python.org), PostgreSQL 18 local na porta 5432, VS Code, DBeaver Community e Command Line Tools da Apple (Git).
- **Não instalados:** Docker e Homebrew.
- Pasta do projeto: `~/Library/CloudStorage/OneDrive-Pessoal/Estudo/Projetos/Projeto SP - Data advanced`. Ela fica no OneDrive por escolha de Marcelo, junto dos outros projetos. O ambiente Python fica em `~/.venvs/projeto-sp-data`, fora do OneDrive. Cuidado: o OneDrive sincroniza a pasta `.git`. Use o GitHub como backup e evite editar o projeto em dois computadores ao mesmo tempo.
- Esta pasta já tem: `docker-compose.yml` (PostgreSQL 17 na porta **5433**), `.env.example`, `.gitignore`, `requirements.txt`, `scripts/check_env.py`, `setup.sh` e `README.md`.
- O `.env` ainda não existe: o `setup.sh` cria, com senha aleatória. **Nunca commitar o `.env`.**
- A pasta antiga `~/Projetos` (versão anterior deste projeto) foi removida, ou deve ser, se ainda existir.

## Próximas tarefas
1. Instalar o Docker Desktop (Apple Silicon): `https://desktop.docker.com/mac/main/arm64/Docker.dmg` → montar com `hdiutil` → copiar para /Applications → abrir. Marcelo precisa aceitar os termos e digitar a senha do Mac na primeira execução; avise-o quando chegar nesse ponto.
2. Rodar `./setup.sh` e confirmar a mensagem "Tudo pronto!".
3. Criar `.vscode/settings.json` apontando o interpretador para `~/.venvs/projeto-sp-data/bin/python` e recomendar as extensões `ms-python.python` e `ms-azuretools.vscode-docker`. Abrir a pasta no VS Code (`code .`, se o comando estiver disponível).
4. Configurar no DBeaver a conexão "SP Data" (localhost:5433, banco/usuário `sp_data`, senha do `.env`). Marcelo digita a senha.
5. Criar o repositório no GitHub (usuário `MRC888`) só com confirmação dele.
6. Fechar com Marcelo a escolha da base (CVM ou IF.data) e começar o desenho da arquitetura e do MVP.
7. Registrar tudo no Obsidian.

## Outros projetos dele (para referência)
Foods and Goods (Kaggle, logística, SQL + Python), análise de honorários (caso real), TCC Barcelona e FIAP Aurora. Detalhes no vault. Observação: o CV de 20/10 diz MySQL para o Foods and Goods, mas o README registra PostgreSQL. Confirmar com ele.
