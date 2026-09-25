# SEO programático — páginas de contratos

## Objetivo

Criar páginas públicas úteis para cada contrato de opção que exista em um snapshot EOD publicado.

A estratégia não cria páginas vazias nem URLs para séries inexistentes.

## Rotas

### Underlying

```text
/acoes/{ticker}/opcoes
```

Exemplo:

`/acoes/PETR4/opcoes`

### Contrato

```text
/opcoes/{contract}
```

Exemplo:

`/opcoes/PETRJ510`

## Fonte de verdade

```text
SnapshotStore
→ /v1/options
→ sitemap
→ /opcoes/[contract]
```

Se o contrato não estiver publicado:

`404`

O frontend não mantém uma lista paralela.

## Conteúdo mínimo indexável

Cada página SSR inclui:

- ticker do contrato;
- CALL/PUT;
- underlying;
- strike;
- vencimento;
- estilo de exercício;
- último/Bid/Ask;
- volume;
- open interest;
- IV;
- Delta/Gamma/Theta/Vega/Rho;
- intrínseco/extrínseco;
- estado de qualidade;
- inputs do analytics;
- data/fonte do snapshot;
- texto explicativo curto e factual.

## Metadata

Title conceitual:

```text
PETRJ510 — CALL PETR4 strike R$ 49,86 | BOLSABR
```

Description:

```text
PETRJ510: CALL de PETR4, strike R$ 49,86, vencimento 16/10/2026.
Bid/Ask, volume, OI, IV e Greeks no fechamento B3.
```

Canonical:

```text
/opcoes/PETRJ510
```

Host definido por:

`BOLSABR_SITE_URL`

## Structured Data

V1 usa `BreadcrumbList`.

Não atribuímos um schema.org de produto financeiro que implique oferta, distribuição ou execução do contrato.

## Sitemaps

A estrutura é segmentada por responsabilidade.

### Core

```text
/sitemap.xml
```

Contém somente:

- home;
- páginas de ativos atualmente publicados.

Isso mantém o sitemap principal pequeno e rápido.

### Contratos por underlying

```text
/opcoes/sitemap/PETR4.xml
/opcoes/sitemap/VALE3.xml
/opcoes/sitemap/ITUB4.xml
...
```

Cada arquivo contém somente contratos do underlying correspondente, incluindo contratos arquivados preservados pelo Contract Registry.

O catálogo é paginado em blocos de 500 no API durante a geração do sitemap.

### Descoberta

`robots.txt` anuncia:

- `/sitemap.xml`;
- um sitemap de opções para cada ativo publicado.

Next.js 16 permite múltiplos sitemaps por route segment via `generateSitemaps()`, com URLs no formato `/.../sitemap/{id}.xml`.

### Limite e escala

Cada sitemap de contratos deve permanecer abaixo de 50.000 URLs.

Segmentar por underlying evita que o crescimento do universo some todos os contratos em um único XML. Se algum underlying individual ultrapassar 50.000 contratos arquivados, ele deve ser subdividido por lote/época sem alterar as URLs das páginas.

### Evidência que motivou a mudança

Proof top-20 anterior à segmentação:

- 20 ativos;
- 28.052 contratos;
- 28.073 URLs em um único sitemap;
- 3,97 MB;
- 4,66 s para gerar/responder.

Por isso a segmentação foi antecipada antes do proof top-50.

## Linkagem interna

Option Chain:
- célula → drawer;
- drawer → página do contrato.

Página do contrato:
- link → Option Chain do underlying.

Isso cria uma estrutura bidirecional clara para usuário e crawler.

## Regras

1. Nunca gerar contrato por convenção de ticker sem snapshot.
2. Nunca mostrar analytics fabricado para preencher SEO.
3. Freshness sempre visível.
4. Quote quality permanece visível.
5. Página não recomenda compra/venda.
6. Historical charts entram apenas quando houver série histórica real.
