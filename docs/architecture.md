# Arquitetura inicial — BOLSABR

## Objetivo

Separar ingestão, normalização, analytics, carteira e produto para evitar dependência de um único fornecedor.

## Visão

```text
B3 / BCB / CVM / Providers
          |
          v
   INGESTION LAYER
          |
          v
      RAW STORAGE
          |
          v
    NORMALIZATION
          |
          v
     DOMAIN MODEL
          |
    +-----+------+
    |            |
    v            v
ANALYTICS     PORTFOLIO
 ENGINE         ENGINE
    |            |
    +------┬-----+
           v
          API
           |
           v
        WEB APP
```

## 1. Ingestion Layer

Responsável por:
- download
- parsing
- retry
- checksum
- timestamp
- metadata de origem

Cada job registra:
- provider
- dataset
- data de referência
- horário de ingestão
- status
- versão/layout
- hash do arquivo

## 2. Raw Storage

Guardar arquivos originais de forma imutável.

Sugestão inicial:
- object storage compatível com S3

Estrutura conceitual:

```text
/raw/b3/instruments/YYYY/MM/DD/
/raw/b3/quotes/YYYY/MM/DD/
/raw/b3/open-interest/YYYY/MM/DD/
/raw/bcb/...
/raw/cvm/...
```

Nunca depender somente de dados já transformados.

## 3. Normalization Layer

Transformar fontes diferentes em um schema interno único.

Entidades:
- Asset
- Underlying
- OptionContract
- Quote
- OptionQuote
- OpenInterest
- CorporateAction
- Dividend
- TradingCalendar

O domínio não deve conhecer detalhes específicos de CSV/XML/JSON de cada provider.

## 4. Analytics Engine

Responsável por:
- IV
- Greeks
- HV
- moneyness
- intrínseco/extrínseco
- IV Rank
- IV Percentile
- probability metrics
- strategy analytics
- payoff

Inputs dos cálculos devem ser reproduzíveis:
- spot
- strike
- expiration
- rate
- dividend assumptions
- model
- option price
- timestamp

## 5. Portfolio Engine

Fonte de verdade:

**Transaction/Event Ledger**

Entidades:
- User
- Portfolio
- Account
- Transaction
- Position (derivada)
- Strategy
- StrategyLeg
- CorporateAction
- CashFlow

Eventos iniciais:
- BUY
- SELL
- OPTION_BUY
- OPTION_SELL
- DIVIDEND
- JCP
- EXERCISE
- ASSIGNMENT
- SPLIT
- REVERSE_SPLIT
- BONUS
- SUBSCRIPTION
- ROLLOVER_LINK

Posições devem poder ser reconstruídas do ledger.

## 6. Strategy Engine

Reconhecer inicialmente:
- Long Call
- Long Put
- Covered Call
- Cash Secured Put
- Bull Call Spread
- Bear Put Spread
- Bull Put Spread
- Bear Call Spread
- Straddle
- Strangle

Depois ampliar.

## 7. Calendar Engine

Unifica:
- option expiration
- data COM
- data EX
- payment date
- corporate events
- earnings futuramente

Serve dashboard e alertas.

## 8. API

A API deve expor conceitos do domínio, não detalhes do provider.

Exemplos futuros:

```text
GET /assets/PETR4
GET /assets/PETR4/options
GET /options/PETRJ400
GET /options/PETRJ400/history
GET /portfolios/:id
GET /portfolios/:id/events
GET /calendar
POST /strategies/simulate
```

## 9. Banco de dados

PostgreSQL é suficiente para o MVP.

Possível evolução:
- PostgreSQL para domínio e ledger
- TimescaleDB/particionamento temporal se snapshots crescerem
- object storage para arquivos raw

Não introduzir infraestrutura distribuída sem necessidade real.

## 10. Frontend

Web-first.

Princípios:
- desktop excelente para Option Chain
- responsivo para carteira/calendário
- densidade somente onde necessária
- presets em vez de dezenas de colunas sempre abertas

Stack final será decidido depois do Proof of Data.

## 11. Observabilidade

Desde o início:
- freshness por dataset
- última ingestão bem-sucedida
- registros rejeitados
- contratos sem underlying
- inconsistências de strike/vencimento
- diferenças entre providers
- erros de analytics

Nenhum preço deve ser apresentado sem timestamp/freshness identificável.

## 12. Segurança e compliance

- sem credenciais de corretora no MVP
- sem execução de ordens na V1
- separar analytics de recomendação financeira
- respeitar licenciamento de market data
- registrar provenance dos dados
