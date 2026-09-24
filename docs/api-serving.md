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
