# Option Chain API v0.1

## Objetivo

Definir uma fronteira estável entre o pipeline de dados/analytics e o frontend do BOLSABR.

O frontend não deve conhecer:
- nomes de colunas B3;
- layouts COTAHIST;
- convenções internas de DI1;
- detalhes do solver de IV.

Ele recebe um domínio normalizado, auditável e versionado.

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
      "type": "MONTHLY",
      "dte_calendar": 23,
      "dte_business": 16,
      "risk_free_rate": 0.1252,
      "rows": []
    }
  ]
}
```

## Vencimento

Cada expiration possui:

- `date`
- `type`: `WEEKLY` ou `MONTHLY`
- `dte_calendar`
- `dte_business`
- `risk_free_rate`
- `rows`

### WEEKLY / MONTHLY

A classificação não depende de heurística de data.

As séries semanais da B3 utilizam o sufixo `W1...W5` no ticker.

Se os contratos do vencimento possuem esse sufixo, o API retorna:

`WEEKLY`.

Caso contrário:

`MONTHLY`.

Isso também cobre vencimentos mensais deslocados por feriado.

## Contrato por opção

Cada CALL/PUT possui quatro grupos conceituais.

### Identidade

- `ticker`
- `type`
- `exercise_style`
- `pricing_model`

Valores atuais de `pricing_model`:

- `BSM_EUROPEAN`
- `BSM_AMERICAN_CALL_NO_DIVIDEND`
- `CRR_AMERICAN`

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

### quote_state

- `TWO_SIDED`
- `ONE_SIDED`
- `LAST_ONLY`
- `NO_PRICE`

### quality_flags

Os flags são fatos transparentes, não um score proprietário.

Exemplos:

- `WIDE_SPREAD_GT_30PCT`
- `ONE_SIDED`
- `LAST_ONLY`
- `NO_TRADES`
- `NO_OPEN_INTEREST`
- `NO_PRICE`

## analytics_input

Inputs auditáveis do cálculo:

- `price`
- `price_basis`: `MID` ou `LAST`
- `risk_free_rate`

O frontend deve conseguir explicar de onde veio uma IV.

## analytics

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

Não fabricar analytics para preencher a tabela.

## Fontes

### Market Data

B3 EOD:
- InstrumentsConsolidated
- TradeInformationConsolidated
- DerivativesOpenPosition
- COTAHIST

### Taxa

B3 DI1 por vencimento.

### Corporate Actions

B3 `GetListedSupplementCompany`, identificado por ISIN.

## Artifact CI

O workflow gera:

- `b3-petr4-smoke.json`
- `petr4-option-chain-v0.json`

O segundo é a payload que alimentará o primeiro frontend.

## Tamanho observado

Snapshot PETR4 de 23/09/2026:

- 3.534 legs
- 30 vencimentos
- 1.767 strikes
- ~3,8 MB em JSON formatado
- ~1,94 MB minificado
- ~117 KB estimados com gzip

Vencimento 16/10/2026 isolado:

- 448 legs
- 224 strikes
- ~26 KB gzip

## Estratégia de transporte

### V1 simples

Pode servir a payload completa com HTTP compression:

- gzip obrigatório;
- Brotli quando suportado;
- cache por `ref_date`.

A payload completa comprimida é pequena o suficiente para um MVP web.

### Evolução recomendada

Endpoints conceituais:

```text
GET /v1/assets/PETR4/options
GET /v1/assets/PETR4/options?expiration=2026-10-16
```

O segundo endpoint permite reduzir parsing/memória quando ampliarmos para mais ativos e intraday.

### Regra de frontend

Mesmo quando a payload completa estiver em memória:

- renderizar somente o vencimento selecionado;
- virtualizar linhas quando necessário;
- começar em uma janela ao redor do ATM;
- carregar/mostrar outras regiões sob demanda.

## Seleção inicial de vencimento

Não escolher simplesmente o vencimento mais próximo.

No snapshot de 23/09/2026:

### 25/09 — WEEKLY

- 170 legs
- 19 TWO_SIDED
- spread mediano bilateral ~66,7%
- volume ~13,2 milhões de unidades
- OI ~22,6 milhões

### 16/10 — MONTHLY

- 448 legs
- 130 TWO_SIDED
- 193 com IV
- volume ~53,0 milhões de unidades
- OI ~239,7 milhões

Portanto, para um usuário sem preferência anterior, a recomendação de UX é:

> selecionar o próximo vencimento MONTHLY com liquidez material.

Os vencimentos WEEKLY continuam visíveis na mesma barra.

Essa é uma regra de apresentação, não uma recomendação de investimento.

## Compatibilidade

Mudanças incompatíveis exigem incremento de `schema_version`.

A camada web nunca deve consumir arquivos B3 diretamente.
