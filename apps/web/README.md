# BOLSABR Web

Aplicação web de produção do BOLSABR.

## Stack

- Next.js 16 App Router
- React
- TypeScript
- CSS próprio / design tokens
- Docker standalone

Decisão completa:

`docs/decisions/ADR-0001-web-stack.md`

## Desenvolvimento

Requisito:

- Node.js 22+

```bash
cd apps/web
npm install
npm run dev
```

Abrir:

`http://localhost:3000/acoes/PETR4/opcoes`

## Dados

A camada web consome apenas o contrato:

`Option Chain API v0.1`

Nunca consome arquivos B3 diretamente.

### Sem backend HTTP

PETR4 usa um fixture real reduzido para desenvolvimento e QA.

### Com backend

Definir:

```bash
BOLSABR_API_BASE_URL=https://api.exemplo.com
```

A aplicação consulta conceitualmente:

```text
GET /v1/assets/PETR4/options
```

O adapter rejeita payloads incompatíveis com `schema_version = 0.1`.

## Rotas iniciais

```text
/                       -> /acoes/PETR4/opcoes
/acoes/[ticker]/opcoes
```

Rotas futuras:

```text
/opcoes/[contract]
/acoes/[ticker]/volatilidade
/acoes/[ticker]/dividendos
```

## QA

```bash
npm run typecheck
npm run build
```

GitHub Actions:

`Web Production QA`

O workflow também inicia o build de produção e captura screenshots desktop/mobile.

## Docker

A partir de `apps/web`:

```bash
docker build -t bolsabr-web .
docker run --rm -p 3000:3000 bolsabr-web
```

Imagem de runtime usa o output `standalone` do Next.js.

## Coolify

Configuração conceitual:

- Build pack: Dockerfile
- Context: `apps/web`
- Port: `3000`
- Health endpoint: adicionar quando a API pública entrar
- env opcional: `BOLSABR_API_BASE_URL`

## Regra de produto

A migração primeiro reproduz a UX validada do protótipo.

Não adicionar features de carteira/execução/IA antes de fechar a Option Chain pública.
