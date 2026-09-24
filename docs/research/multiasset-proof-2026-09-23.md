# Live Multiasset Proof — 23/09/2026

## Objetivo

Validar que o pipeline EOD originalmente provado em PETR4 funciona sem hardcodes do underlying e reutiliza os mesmos downloads de mercado para múltiplos ativos.

Run:

`Multiasset EOD Proof — 36035575831`

## Ativos

A seleção PETR4 / VALE3 / ITUB4 é exclusivamente técnica para cobrir underlyings distintos.

Não representa recomendação de investimento.

## Resultado

| Ativo | Spot | Contratos | Vencimentos | Strike rows | COTAHIST | Bid/Ask válido |
|---|---:|---:|---:|---:|---:|---:|
| PETR4 | R$ 49,60 | 3.534 | 30 | 1.767 | 833 | 319 |
| VALE3 | R$ 71,48 | 3.012 | 29 | 1.506 | 591 | 204 |
| ITUB4 | R$ 42,37 | 2.378 | 30 | 1.189 | 465 | 106 |

Curva DI1:

**45 vértices**

Fallback documentado:

`BCB_SGS_11:2026-09-23`

Warnings:

**nenhum**

## Quote quality

Distribuição observada:

### PETR4

- TWO_SIDED: 318
- ONE_SIDED: 251
- LAST_ONLY: 263
- NO_PRICE: 2.702
- IV calculável: 756

### VALE3

- TWO_SIDED: 203
- ONE_SIDED: 200
- LAST_ONLY: 185
- NO_PRICE: 2.424
- IV calculável: 537

### ITUB4

- TWO_SIDED: 105
- ONE_SIDED: 137
- LAST_ONLY: 222
- NO_PRICE: 1.914
- IV calculável: 440

## Default de vencimento

A regra definida em PETR4 também funcionou nos outros dois ativos:

> primeiro vencimento MONTHLY com liquidez material.

Para 16/10/2026:

| Ativo | Legs | TWO_SIDED | IV | Volume | OI |
|---|---:|---:|---:|---:|---:|
| PETR4 | 448 | 130 | 193 | ~53,0M | ~239,7M |
| VALE3 | 404 | 82 | 115 | ~35,7M | ~103,5M |
| ITUB4 | 208 | 60 | 110 | ~15,9M | ~105,9M |

## Performance do dataset

Arquivos JSON formatados do artifact live:

- PETR4: ~3,8 MB
- VALE3: ~3,2 MB
- ITUB4: ~2,6 MB

Compressão gzip observada aproximadamente:

- PETR4: ~136 KB
- VALE3: ~103 KB
- ITUB4: ~83 KB

Conclusão:

O payload completo por ativo continua adequado ao MVP EOD com compressão HTTP.

## Arquitetura comprovada

```text
1 download dos datasets B3 comuns
       ↓
1 curva DI1
       ↓
1 COTAHIST filtrado pela união dos contratos
       ↓
PETR4 / VALE3 / ITUB4
       ↓
3 Option Chain API snapshots
       ↓
FilesystemSnapshotStore
       ↓
GET /v1/assets
```

O API listou os três snapshots publicados.

## Próximo passo

Validar navegação da busca Web entre ativos publicados e, depois, ampliar progressivamente o universo EOD.
