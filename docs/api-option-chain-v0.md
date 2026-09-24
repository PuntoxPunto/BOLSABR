# Option Chain API v0.1

## Objetivo

Definir uma fronteira estável entre o pipeline de dados/analytics e o frontend do BOLSABR.

O frontend não deve conhecer:
- nomes de colunas B3;
- layouts COTAHIST;
- convenções internas de DI1;
- detalhes do solver de IV.

Ele recebe um domínio já normalizado e auditável.

## Exemplo conceitual

```json
{
  "schema_version": "0.1",
  "ref_date": "2026-09-23",
  "market_data_source": "B3_EOD",
  "rate_source": "B3_DI1",
  "underlying": {
    "ticker": "PETR4",
    "spot": 49.60
  },
  "expirations": [
    {
      "date": "2026-10-16",
      "dte_calendar": 23,
      "dte_business": 16,
      "risk_free_rate": 0.1252,
      "rows": [
        {
          "strike": 50.00,
          "call": {},
          "put": {}
        }
      ]
    }
  ]
}
```

## Contrato por opção

Cada CALL/PUT possui quatro grupos conceituais.

### Identidade

- `ticker`
- `type`
- `exercise_style`
- `pricing_model`

### market

Dados observados:

- `last`
- `bid`
- `ask`
- `spread_pct`
- `quote_state`
- `quality_flags`
- `trade_count`
- `volume`
- `financial_volume`
- `open_interest`

Estados de book:

- `TWO_SIDED`
- `ONE_SIDED`
- `LAST_ONLY`
- `NO_PRICE`

Os flags não são um score proprietário; são fatos transparentes, por exemplo:

- `WIDE_SPREAD_GT_30PCT`
- `LAST_ONLY`
- `NO_TRADES`
- `NO_OPEN_INTEREST`
- `NO_PRICE`

### analytics_input

Inputs auditáveis do cálculo:

- `price`
- `price_basis`: `MID` ou `LAST`
- `risk_free_rate`

O frontend deve conseguir explicar de onde veio a IV.

### analytics

Resultados derivados:

- `intrinsic`
- `extrinsic`
- `iv`
- `delta`
- `gamma`
- `theta`
- `vega`
- `rho`

Valores podem ser `null` quando a observação de mercado é insuficiente ou incompatível com o modelo.

Isso é preferível a fabricar uma métrica.

## Modelos

Valores atuais de `pricing_model`:

- `BSM_EUROPEAN`
- `BSM_AMERICAN_CALL_NO_DIVIDEND`
- `CRR_AMERICAN`

Uma CALL americana sem dividendos futuros relevantes tem equivalência econômica com a opção europeia e não precisa de árvore CRR.

## Fontes

### Market data
B3 EOD:
- InstrumentsConsolidated
- TradeInformationConsolidated
- DerivativesOpenPosition
- COTAHIST

### Taxa
Curva DI1 B3 por vencimento.

### Corporate Actions
B3 GetListedSupplementCompany, identificado por ISIN.

## Artifact de CI

O workflow `Phase 0 - PETR4 Proof of Data` gera:

- `b3-petr4-smoke.json`
- `petr4-option-chain-v0.json`

O segundo arquivo é a payload completa que pode alimentar diretamente o protótipo frontend.

## Evolução

Mudanças incompatíveis exigem incrementar `schema_version`.

A camada web não deve consumir diretamente arquivos B3.
