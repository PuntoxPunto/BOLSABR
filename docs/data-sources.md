# Estratégia de dados — BOLSABR

## Objetivo

Construir o produto sem depender de scraping de concorrentes e mantendo um pipeline próprio, auditável e substituível.

## Princípio

Prioridade de fontes:

1. **B3** — instrumentos, séries, cotações, vencimentos, volume, open interest e históricos.
2. **BCB** — taxas e séries macro necessárias aos modelos.
3. **CVM / RI** — fundamentos e eventos corporativos.
4. **Provedores terceiros** — apenas como aceleradores, fallback ou validação.
5. **Concorrentes** — benchmarking visual/funcional, nunca datasource primário.

---

## B3

### Instrument Registry / Cadastro de Instrumentos
Arquivo relevante para opções:
- BVBG.028.02
- código do instrumento
- underlying
- tipo
- strike
- vencimento
- características do contrato

### BDI / dados de mercado
Usar os dados públicos atuais disponibilizados pela B3 para preços e negociação.

### COTAHIST
Importante para histórico e validação.

Campos relevantes incluem:
- preço de abertura
- máxima
- mínima
- média
- último
- melhor compra
- melhor venda
- número de negócios
- quantidade
- volume
- preço de exercício
- vencimento

### Open Interest
Identificar e ingerir a fonte oficial adequada para posições em aberto por instrumento.

### Licenciamento
Hipótese operacional atual:
- EOD / histórico D-1 como camada Free
- delay/real-time somente após validar necessidade e licenciamento aplicável

Não assumir que qualquer dado intraday pode ser redistribuído gratuitamente.

---

## Banco Central do Brasil

Usos:
- Selic
- curvas/taxas auxiliares
- séries macroeconômicas

No MVP, Selic/DI pode ser usada como aproximação inicial de taxa livre de risco, mas o motor deve permitir curva por prazo posteriormente.

---

## CVM / RI

Usos:
- cadastro de companhias
- demonstrações financeiras
- eventos corporativos
- proventos
- informações de emissores

Investidor10 serve como referência de UX, mas os dados fundamentais devem vir de CVM/B3/RI ou de fornecedor licenciado.

---

## brapi.dev

Uso sugerido:
- acelerar protótipos
- validar normalização
- comparar Greeks/IV
- fallback temporário

Não criar dependência estrutural.

A arquitetura deve permitir trocar o provider sem alterar o domínio do produto.

---

## Concorrentes

### Opções.Net.Br
Usar para:
- benchmark de cobertura
- histórico
- SEO
- comparação de resultados

Não usar como fonte automática.

### Profit / Nelogica
Usar para:
- benchmark da grade
- ergonomia
- fluxo de estratégias
- seleção de colunas

Não usar seus dados proprietários.

### OpLab
Usar para:
- comparação de IV/Greeks
- estratégias
- scanners
- payoff

### Investidor10
Usar para:
- carteira
- proventos
- calendário
- navegação

Não usar como datasource.

---

## Dados brutos vs calculados

### Brutos
Devem ser armazenados com provenance:
- instrument_id
- ticker
- underlying
- call/put
- strike
- expiration
- exercise style
- last
- bid
- ask
- OHLC
- trades
- quantity
- financial volume
- open interest
- timestamp
- source

### Calculados
Produzidos pelo nosso analytics engine:
- spread
- moneyness
- ITM/ATM/OTM
- valor intrínseco
- valor extrínseco
- IV
- Delta
- Gamma
- Theta
- Vega
- Rho
- IV Rank
- IV Percentile
- HV
- probabilidades aproximadas
- yields

Nunca sobrescrever dado bruto com cálculo derivado.

---

## Modelos de opções

### Europeias
Base inicial:
- Black-Scholes / Black-Scholes-Merton

### Americanas
Planejar:
- binomial CRR
ou
- Bjerksund-Stensland

Incluir dividendos/carry quando aplicável.

---

## Histórico próprio

Guardar snapshots desde o primeiro dia.

Objetivo:
- IV histórica
- IV Rank
- IV Percentile
- evolução de OI
- evolução de spreads
- volatility surface
- backtests posteriores

Esse histórico é um ativo estratégico do produto.

---

## Proof of Data — PETR4

Antes do frontend definitivo:

1. Ingerir instrumentos PETR4.
2. Identificar todas as opções válidas.
3. Agrupar por vencimento.
4. Recuperar preços/volume/OI.
5. Calcular moneyness.
6. Calcular IV.
7. Calcular Greeks.
8. Comparar com Profit, OpLab, Opções.Net.Br e brapi.
9. Registrar divergências e tolerâncias.
10. Só então estabilizar o schema da API.

Critérios de sucesso:
- strikes corretos
- vencimentos corretos
- CALL/PUT corretos
- estilo de exercício correto
- preços/volume/OI coerentes com a fonte
- IV e Greeks dentro de tolerância definida
