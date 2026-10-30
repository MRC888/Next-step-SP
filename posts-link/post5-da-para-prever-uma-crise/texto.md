# Post 5 — Dá para prever uma crise?
Status: rascunho v1 (30/10/2026), aguardando revisão de Marcelo. Imagem: `imagem.png` (barra com "▲ este post" no ML).
Números: `ml/resultados/metricas.json` (avaliação walk-forward 2013–2024, 30/10/2026).

---

Dá para prever, pelo balanço, que uma empresa vai entrar em recuperação judicial?

Treinei um modelo com 15 anos de balanços de companhias abertas para responder a uma pergunta de analista de crédito: dado o balanço que a empresa acabou de publicar, qual o risco de ela entrar em recuperação judicial, falência ou liquidação nos 24 meses seguintes?

Três cuidados fizeram mais diferença do que o algoritmo:

1. Não ver o futuro. O modelo só usa o balanço depois da data em que ele ficou público. E foi avaliado ano a ano: para prever 2018, ele só conhecia o que se sabia antes de 2018.

2. Desconfiar dos dados. O nome da empresa nos arquivos da CVM é o nome atual, não o da época. A DFP de 2011 da Americanas já aparece "em recuperação judicial". Usar o nome teria vazado o futuro para o modelo.

3. Comparar com uma régua conhecida. O Z-score de Altman é usado há décadas. Se o modelo não ganha dele, não serve.

Resultado, em 6.702 balanços e 50 empresas que de fato entraram em dificuldade:
• Acaso: acertaria 1,3% dos alertas
• Z-score de Altman: AUC 0,66 · precisão média 2,9%
• Modelo (gradient boosting): AUC 0,69 · precisão média 6,0%, 4,5 vezes o acaso
• Entre os 10% de maior risco apontados pelo modelo estavam 34% dos casos reais

É um ganho real, mas modesto, e eu prefiro mostrar isso a vender milagre. Com poucos casos e um cadastro que só guarda a situação atual das empresas, o modelo é um alerta para investigar, não um veredito.

Os sinais que mais pesaram: patrimônio em relação às dívidas, lucros acumulados, rentabilidade dos ativos e margem líquida. Ou seja, o básico da análise de balanço, agora em escala.

Para quem trabalha com crédito: qual sinal de balanço você olha primeiro?

#MachineLearning #CienciaDeDados #AnaliseDeCredito #Python #DadosAbertos
