# BOLSABR API

API read-only para snapshots EOD precomputados.

## Regra principal

A API **não consulta B3 durante requests de usuários**.

Fluxo:

```text
ingestion + analytics
        ↓
Option Chain API JSON
        ↓
publish_snapshot.py
        ↓
/data/serving/options/{ticker}/
        ↓
FastAPI
        ↓
Next.js
```

## Layout do store

```text
/data/serving/
└── options/
    └── PETR4/
        ├── 2026-09-23.json
        ├── 2026-09-24.json
        └── latest.json
```

Snapshots datados são imutáveis.

`latest.json` é atualizado atomicamente.

## Publicar snapshot

```bash
python scripts/publish_snapshot.py \
  artifacts/petr4-option-chain-v0.json \
  --snapshot-dir data/serving
```

## Executar localmente

```bash
pip install -e ".[dev]"
BOLSABR_SNAPSHOT_DIR=data/serving \
  uvicorn bolsabr.api.app:app --reload --port 8000
```

## Endpoints

### Catálogo de ativos publicados

```text
GET /v1/assets
GET /v1/assets?q=VALE
```

Retorna somente ativos com `latest.json` válido no serving store.

Campos V1:

- ticker
- ref_date
- spot
- expiration_count
- market_data_source

A busca da Web usa este catálogo; não existe lista de tickers hardcoded no frontend.

### Health

```text
GET /healthz
```

Não depende de B3 nem da existência de snapshots.

### Option Chain atual

```text
GET /v1/assets/PETR4/options
```

### Um vencimento

```text
GET /v1/assets/PETR4/options?expiration=2026-10-16
```

O filtro preserva o schema v0.1 e apenas reduz `expirations`.

## Cache

Respostas EOD enviam:

```text
Cache-Control: public, max-age=300, stale-while-revalidate=3600
ETag: "..."
```

`If-None-Match` compatível retorna HTTP 304.

## Docker / Coolify

Dockerfile:

`deploy/api/Dockerfile`

Build context:

raiz do repositório.

Porta:

`8000`

Variáveis:

```text
BOLSABR_SNAPSHOT_DIR=/data/serving
PORT=8000
```

Montar volume persistente em:

`/data/serving`

O job de ingestão/publisher e o container do API devem enxergar o mesmo volume, ou o publisher deve promover os arquivos para object storage em uma evolução posterior.

## Frontend

No container Next.js:

```text
BOLSABR_API_BASE_URL=http://bolsabr-api:8000
```

A leitura acontece no servidor Next.js, portanto CORS não é necessário nessa topologia.


---

## Contratos individuais de opções

### Detalhe de um contrato

```text
GET /v1/options/PETRJ510
```

Resposta conceitual:

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
  "contract": {
    "ticker": "PETRJ510",
    "type": "CALL",
    "exercise_style": "AMERICAN",
    "pricing_model": "BSM_AMERICAN_CALL_NO_DIVIDEND",
    "strike": 49.86,
    "expiration": "2026-10-16",
    "expiration_type": "MONTHLY",
    "dte_calendar": 23,
    "dte_business": 16,
    "market": {},
    "analytics_input": {},
    "analytics": {}
  }
}
```

O detalhe é derivado diretamente do snapshot publicado. Não recalcula IV/Greeks durante o request.

Contrato inexistente:

`HTTP 404`

### Catálogo paginado de contratos

```text
GET /v1/options
GET /v1/options?underlying=PETR4
GET /v1/options?q=PETRJ
GET /v1/options?offset=500&limit=500
```

Campos do resumo:

- ticker;
- underlying;
- ref_date;
- expiration;
- expiration_type;
- strike;
- type;
- exercise_style;
- quote_state;
- last;
- bid;
- ask;
- open_interest;
- volume;
- iv.

Resposta:

```json
{
  "contracts": [],
  "offset": 0,
  "limit": 500,
  "total": 3534,
  "next_offset": 500
}
```

O catálogo alimenta sitemap/SEO e futuras superfícies de busca por contrato.

### Cache

Detalhe e catálogo seguem a política EOD:

- `Cache-Control: public, max-age=300, stale-while-revalidate=3600`;
- ETag por payload;
- suporte a `If-None-Match`.

---

## SEO público

Rotas Web:

```text
/acoes/PETR4/opcoes
/opcoes/PETRJ510
```

A página individual de contrato é server-rendered e contém:

- contrato;
- underlying;
- strike;
- vencimento;
- Bid/Ask/Last;
- volume/OI;
- IV/Greeks;
- intrínseco/extrínseco;
- quote quality;
- modelo e inputs do cálculo;
- link de volta à Option Chain.

O sitemap é gerado apenas a partir de ativos e contratos presentes no serving store.

Variável obrigatória em staging/produção para URLs canônicas:

```text
BOLSABR_SITE_URL=https://<dominio-publico>
```

Sem configuração explícita, o ambiente local usa `http://localhost:3000`.


---

## Histórico EOD de um contrato

Endpoint:

```text
GET /v1/options/PETRJ510/history
GET /v1/options/PETRJ510/history?start=2026-09-01&end=2026-09-24&limit=100
```

A série é projetada diretamente dos snapshots datados imutáveis.

Não existe interpolação de dias ausentes.

Resposta conceitual:

```json
{
  "schema_version": "0.1",
  "contract": "PETRJ510",
  "underlying": "PETR4",
  "start_date": "2026-09-22",
  "end_date": "2026-09-24",
  "observations": 3,
  "points": [
    {
      "ref_date": "2026-09-22",
      "underlying_spot": 49.10,
      "last": 2.00,
      "bid": 1.90,
      "ask": 2.10,
      "quote_state": "TWO_SIDED",
      "volume": 100,
      "open_interest": 1000,
      "price_for_model": 2.00,
      "price_basis": "MID",
      "risk_free_rate": 0.125,
      "iv": 0.40,
      "delta": 0.55
    }
  ]
}
```

Campos históricos preservados quando disponíveis:

- underlying spot;
- Last/Bid/Ask;
- spread;
- quote_state/quality_flags;
- negócios;
- volume/volume financeiro;
- open interest;
- preço/base/taxa usados no analytics;
- IV;
- Delta/Gamma/Theta/Vega/Rho;
- intrínseco/extrínseco.

### Gaps

Se o contrato não aparece em um snapshot, a data não gera ponto.

Exemplo:

```text
22/09 observado
23/09 ausente
24/09 observado
```

Resposta:

```text
22/09 → 24/09
```

Não criamos um valor artificial para 23/09.

### Limit

`limit` preserva as N observações mais recentes, devolvidas em ordem cronológica.

### Cache

O histórico segue ETag e a política EOD de cache da API.
