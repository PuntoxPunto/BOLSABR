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

## Sitemap

`/sitemap.xml`

Contém:

- home;
- páginas de ativos publicados;
- páginas de contratos publicados.

O catálogo é paginado no API e o gerador percorre todas as páginas.

### Escala

A implementação atual é adequada enquanto o sitemap permanecer abaixo do limite padrão de 50.000 URLs.

Antes de ultrapassar esse volume, migrar para sitemap index segmentado por ativo ou lote.

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
