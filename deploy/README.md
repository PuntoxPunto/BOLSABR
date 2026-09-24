# Deploy BOLSABR — Docker / Coolify

## Topologia EOD V1

```text
                  ┌──────────────────┐
B3 / BCB / CVM →  │ publisher worker │
                  └────────┬─────────┘
                           │ RW
                           v
                  bolsabr_snapshots
                           │ RO
                           v
                  ┌──────────────────┐
                  │ FastAPI          │
                  │ api:8000         │
                  └────────┬─────────┘
                           │ HTTP interno
                           v
                  ┌──────────────────┐
Internet ───────→ │ Next.js Web      │
                  │ :3000            │
                  └──────────────────┘
```

O API não precisa ser exposto diretamente à internet no MVP.

## Arquivos

- `deploy/compose.yml`
- `deploy/api/Dockerfile`
- `deploy/worker/Dockerfile`
- `apps/web/Dockerfile`

## Primeiro snapshot

Antes de abrir PETR4 em um ambiente onde o API está configurado, publicar um snapshot:

```bash
docker compose -f deploy/compose.yml --profile jobs run --rm publisher
```

O worker executa:

```text
B3/BCB ingestion
→ analytics
→ artifacts/petr4-option-chain-v0.json
→ publish_snapshot.py
→ volume persistente
```

Por padrão publica PETR4.

Para publicar mais ativos:

```bash
BOLSABR_UNDERLYINGS="PETR4 VALE3 ITUB4" \
  docker compose -f deploy/compose.yml --profile jobs run --rm publisher
```

O worker baixa os datasets comuns uma única vez e monta as chains solicitadas em lote.

## Subir Web + API

```bash
docker compose -f deploy/compose.yml up -d api web
```

Abrir:

```text
http://localhost:3000/acoes/PETR4/opcoes
```

## Health

API:

```text
GET http://api:8000/healthz
```

Web:

```text
GET /healthz
```

Ambos são independentes do download live da B3.

## Volume

Named volume:

`bolsabr_snapshots`

Mounts:

- publisher: `/data/serving` read-write
- API: `/data/serving` read-only
- Web: sem acesso ao volume

Reiniciar ou substituir os containers Web/API não apaga o snapshot.

## Atualização EOD

Executar o publisher novamente:

```bash
docker compose -f deploy/compose.yml --profile jobs run --rm publisher
```

O store:

- cria um arquivo imutável por ref_date;
- atualiza `latest.json` atomicamente.

O horário do job deve ser posterior à disponibilidade dos arquivos finais necessários da B3. O pipeline já procura snapshots `Final` e preserva provenance/freshness.

## Backfill COTAHIST

Depois que um contrato entrou no Contract Registry, é possível popular histórico anterior de preço/volume usando a série anual oficial B3.

Exemplo:

```bash
docker compose -f deploy/compose.yml --profile jobs run --rm \
  publisher   python scripts/backfill_cotahist.py     2026 PETR4 VALE3 ITUB4     --snapshot-dir /data/serving     --start 2026-01-01     --end 2026-09-23
```

A série anual é baixada uma vez para a união dos underlyings/contratos solicitados.

O backfill:
- não move `latest.json` para trás;
- preserva contratos vencidos no registry;
- preenche somente campos observáveis em COTAHIST;
- deixa OI/IV/Greeks nulos quando não há fonte suficiente;
- marca provenance `B3_COTAHIST_BACKFILL`.

Live proof PETRJ510:

- 01/08/2026 a 23/09/2026;
- 22 observações reais recuperadas;
- run `36070142229`.

O backfill é um job eventual/reprocessável, separado do publisher EOD diário.

## Coolify

### API

Build:
- contexto: raiz do repo
- Dockerfile: `deploy/api/Dockerfile`

Persistência:
- volume em `/data/serving`

Variável:

```text
BOLSABR_SNAPSHOT_DIR=/data/serving
```

Porta interna:

`8000`

Não é necessário domínio público no MVP.

### Web

Build:
- contexto: `apps/web`
- Dockerfile: `Dockerfile`

Variável:

```text
BOLSABR_API_BASE_URL=http://api:8000
```

Na configuração multi-serviço, usar o hostname interno atribuído ao serviço FastAPI.

Porta:

`3000`

### Publisher

Build:
- contexto: raiz do repo
- Dockerfile: `deploy/worker/Dockerfile`

Mount:
- mesmo volume do API em `/data/serving`, com escrita.

Executar como job agendado EOD, não como serviço permanente.

## Atualização de código

Fluxo recomendado:

1. build das novas imagens;
2. manter o volume de snapshots;
3. substituir API/Web;
4. validar `/healthz`;
5. validar PETR4;
6. publisher roda no próximo ciclo EOD.

## Recuperação

Como snapshots datados são imutáveis, um snapshot anterior permanece no volume.

Se o novo pipeline falhar:
- `latest.json` antigo continua disponível se o publisher não chegou à promoção;
- API/Web continuam servindo o último snapshot válido;
- freshness deixa explícita a data ao usuário.

## Evolução

Quando filesystem deixar de ser suficiente:

```text
FilesystemSnapshotStore
        ↓
ObjectStorageSnapshotStore
```

A API e o frontend não precisam mudar de contrato.
