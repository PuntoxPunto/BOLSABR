# Histórico EOD de opções

## Objetivo

Construir histórico de preço, volatilidade e posicionamento sem criar uma fonte de verdade paralela ao pipeline EOD.

## Arquitetura

```text
Snapshot EOD imutável D1
Snapshot EOD imutável D2
Snapshot EOD imutável D3
          ↓
FilesystemSnapshotStore.list_versions()
          ↓
contract_history()
          ↓
GET /v1/options/{contract}/history
          ↓
página /opcoes/{contract}
```

## Por que usar os snapshots

Cada snapshot já contém:

- dados observados B3;
- qualidade da cotação;
- inputs usados no modelo;
- IV/Greeks calculados;
- provenance;
- ref_date.

Portanto a série histórica é uma projeção reprodutível da mesma fonte de verdade utilizada pela Option Chain.

## Séries V1

A ficha do contrato apresenta quatro gráficos:

1. preço — último negócio;
2. IV — volatilidade implícita;
3. OI — open interest;
4. volume — quantidade negociada.

## Regras de integridade

### Sem interpolação

Não ligamos um dia inexistente a um número inventado no dataset.

A linha visual conecta somente observações reais existentes.

### Null permanece null

Se uma observação existe mas um campo específico não pôde ser calculado, esse campo continua nulo.

### Quote quality permanece acessível

Cada ponto preserva:

- quote_state;
- quality_flags;
- price_basis.

A UI mostra o quote_state e a base do cálculo ao selecionar/focar um ponto.

### Uma observação

Com menos de dois valores válidos para uma métrica:

`Histórico em formação`

Não desenhamos uma linha fictícia.

## UX

Gráficos SVG próprios, sem biblioteca externa.

Motivos:

- poucos pontos no início;
- bundle pequeno;
- controle de acessibilidade;
- ausência de smoothing artificial;
- domínio simples.

Cada ponto pode receber foco por teclado e anuncia:

- data;
- valor;
- quote_state.

## Backfill

A série V1 cresce diariamente a partir dos snapshots BOLSABR.

A etapa posterior de backfill deverá reprocessar arquivos oficiais B3 para datas anteriores.

O backfill deve diferenciar:

- campo observado originalmente;
- campo reconstruído de arquivo oficial;
- analytics recalculado;
- campo historicamente indisponível.

Não preencher gaps por inferência.

## Evolução de storage

Filesystem é suficiente para o MVP.

Quando o histórico/universo crescer:

```text
FilesystemSnapshotStore
        ↓
ObjectStorage / columnar historical store
```

A API pública pode permanecer compatível.
