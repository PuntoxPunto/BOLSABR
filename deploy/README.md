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

O baseline atual de staging é o universo automático top-50 de ações:

```text
BOLSABR_UNIVERSE_MODE=auto
BOLSABR_UNIVERSE_KIND=stocks
BOLSABR_UNIVERSE_LIMIT=50
BOLSABR_UNIVERSE_MIN_FINANCIAL_VOLUME=0
```

Para execução local one-shot, use diretamente o entrypoint:

```bash
docker compose -f deploy/compose.yml exec publisher \
  python scripts/run_eod_publisher.py
```

O worker baixa os datasets comuns uma única vez, descobre o universo, seleciona o top-N e monta as chains em lote.

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

O serviço `publisher` permanece rodando de forma inativa para servir como alvo de Scheduled Tasks do Coolify.

Comando EOD:

```text
python scripts/run_eod_publisher.py
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
- mesmo volume do API em `/data/serving`, com escrita;
- API monta esse volume como read-only.

O container publisher fica rodando inativo porque o Coolify executa Scheduled Tasks dentro de um container existente.

Scheduled Task:

```text
Container: publisher
Command: python scripts/run_eod_publisher.py
Timeout: 1800 s ou superior
```

Frequência: dias úteis, após a disponibilidade dos arquivos EOD finais da B3. O cron usa o timezone configurado no deployment server do Coolify.

Antes de habilitar o agendamento:
1. Execute a task manualmente com `Execute Now`;
2. confirme `Success`;
3. confirme que `/v1/assets` passa a listar o universo publicado;
4. só então habilite o cron recorrente.

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


---

## Staging Coolify — procedimento final da Fase 1

### 1. Criar o recurso

No Coolify, crie um **Service / Docker Compose** apontando para este repositório e para:

```text
deploy/compose.yml
```

O Compose é a fonte de verdade para:
- Web;
- API;
- publisher;
- volume `bolsabr_snapshots`;
- health checks;
- mounts.

### 2. Variáveis

Copie os valores de `deploy/staging.env.example` para o ambiente de staging.

Obrigatórias:

```text
BOLSABR_SITE_URL=https://<dominio-staging>
BOLSABR_API_BASE_URL=http://api:8000

BOLSABR_UNIVERSE_MODE=auto
BOLSABR_UNIVERSE_KIND=stocks
BOLSABR_UNIVERSE_LIMIT=50
BOLSABR_UNIVERSE_MIN_FINANCIAL_VOLUME=0
```

`BOLSABR_SITE_URL` deve ser a URL HTTPS externa real. Ela alimenta canonical, Open Graph, robots e sitemaps em runtime.

### 3. Domínio

Exponha somente o serviço Web na internet.

API:
- rede interna;
- sem domínio público obrigatório;
- porta 8000.

Web:
- porta 3000;
- domínio HTTPS de staging.

### 4. Primeiro publish

Depois que os três containers estiverem rodando, crie ou execute manualmente a Scheduled Task no componente `publisher`:

```text
python scripts/run_eod_publisher.py
```

Resultado esperado:
- ~50 ativos;
- dezenas de milhares de contratos;
- arquivos em `/data/serving`;
- API passa a responder catálogo real.

Baseline live já validado:
- 50 ativos;
- 43.596 contratos;
- ~20,72 s de build/publish em GitHub Actions;
- ~59,89 MB de serving store;
- ~495 MB peak RSS.

### 5. Smoke remoto

No repo existe:

```text
scripts/staging_smoke.py
```

Execução local:

```bash
python scripts/staging_smoke.py \
  https://<dominio-staging> \
  --ticker PETR4 \
  --min-assets 50 \
  --require-https
```

Ele valida:
- Web health;
- root sitemap;
- PETR4;
- robots;
- sitemap segmentado;
- uma página real de contrato descoberta dinamicamente;
- canonical;
- freshness EOD;
- 404 de ativo inexistente.

Também existe o workflow manual:

```text
Staging Smoke
```

Pode receber `base_url` manualmente ou usar o secret de environment:

```text
BOLSABR_STAGING_URL
```

### 6. Persistência

Depois do primeiro smoke verde:

1. anote o `ref_date` de PETR4;
2. faça redeploy/restart de Web e API;
3. não remova o volume;
4. rode novamente o smoke;
5. confirme que os snapshots continuam disponíveis.

O publisher é o único componente com escrita no volume.

### 7. Gate da Fase 1

Fase 1 fecha quando:

```text
Coolify staging
→ publisher top-50
→ HTTPS
→ smoke remoto verde
→ redeploy Web/API
→ snapshots persistem
```

A partir daí, o próximo desenvolvimento é **Fase 2 — Conta + Carteira**.
