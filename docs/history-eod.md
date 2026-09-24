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

## Backfill oficial COTAHIST

A série cresce diariamente a partir dos snapshots BOLSABR e também pode receber histórico anterior a partir da Série Histórica oficial da B3.

Fonte:

`COTAHIST_A{ano}.ZIP`

O downloader anual:
- faz streaming do ZIP;
- derrama para disco após 8 MB;
- lê o TXT linha a linha;
- filtra data/ticker antes do parse completo;
- não carrega o mercado anual inteiro em memória.

### Validação do contrato

Um registro histórico só é aceito quando coincide com o registry persistente em:

- ticker;
- CODBDI 78 para CALL ou 82 para PUT;
- strike;
- vencimento.

Isso evita misturar tickers reutilizados em séries diferentes.

### Campos preenchidos pelo backfill

COTAHIST fornece:

- underlying spot quando encontrado na mesma data;
- Last;
- Bid;
- Ask;
- spread;
- quote_state/quality flags;
- negócios;
- volume;
- volume financeiro.

Mantemos explicitamente nulos:

- open interest;
- taxa usada no modelo;
- price_basis;
- IV;
- Greeks;
- intrínseco/extrínseco.

Não existe inferência desses campos.

### Provenance

Pontos de histórico usam:

- `BOLSABR_SNAPSHOT`;
- `B3_COTAHIST_BACKFILL`.

Se COTAHIST e snapshot BOLSABR existem na mesma data, o snapshot BOLSABR prevalece.

### Live proof

Run:

`36070142229 — COTAHIST Backfill Proof — success`

Contrato real usado:

`PETRJ510`

Janela:

`01/08/2026 → 23/09/2026`

Resultado:

- 71 registros COTAHIST filtrados incluindo underlying/contrato;
- 1 contrato registrado;
- 1 contrato backfilled;
- **22 observações reais PETRJ510**.

Isso permite que uma página de opção atual nasça com semanas de histórico de mercado sem centenas de downloads diários.

## Contract Registry e opções vencidas

Cada publish atualiza um registry persistente por underlying:

- first_seen;
- last_seen;
- strike;
- expiration;
- CALL/PUT;
- exercise_style;
- última observação conhecida.

Um publish histórico nunca move `latest.json` para trás.

Quando o contrato deixa de aparecer no latest:

- a URL `/opcoes/{contract}` continua válida;
- o catálogo continua contendo o contrato;
- o histórico permanece acessível;
- o sitemap preserva a URL.

E2E:

`36070297127 — success`

O teste remove `PETRJOLD` do latest em 24/09, mas comprova que detalhe, histórico 22/23 e sitemap continuam vivos.

## Evolução de storage

Filesystem é suficiente para o MVP.

Quando o histórico/universo crescer:

```text
FilesystemSnapshotStore
        ↓
ObjectStorage / columnar historical store
```

A API pública pode permanecer compatível.
