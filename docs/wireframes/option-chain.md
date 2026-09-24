# Wireframe — Option Chain PETR4

## Estado

Wireframe funcional para **Fase 1 — Read-only MVP**.

Este documento define comportamento, hierarquia e densidade de informação antes da escolha final de framework/visual design.

## Princípio

> Manter a velocidade de leitura do Profit, mas eliminar a densidade desnecessária de um terminal desktop.

A chain é o centro da experiência.

O usuário deve responder rapidamente:

1. qual é o preço do underlying;
2. qual vencimento está olhando;
3. onde está o ATM;
4. quais contratos têm mercado real;
5. qual é Bid/Ask/IV/Delta/OI;
6. se o analytics veio de MID ou LAST.

---

# 1. Desktop — estrutura

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ BOLSABR       [ Buscar ativo... PETR4 ]                     Dados B3 · EOD    │
├───────────────────────────────────────────────────────────────────────────────┤
│ PETR4 · Petrobras PN                                                        │
│ R$ 49,60                                      Fechamento 23/09/2026           │
│                                                                               │
│ [ Opções ]  [ Volatilidade ]  [ Dividendos ]  [ Eventos ]                   │
├───────────────────────────────────────────────────────────────────────────────┤
│ VENCIMENTOS                                                                  │
│ [25 SET · S · 2d] [02 OUT · S · 9d] [09 OUT · S · 16d]                     │
│ [16 OUT · M · 23d ★] [23 OUT · S · 30d] [30 OUT · S · 37d]                 │
│ [19 NOV · M · 57d] [18 DEZ · M · 86d] ...                                  │
├───────────────────────────────────────────────────────────────────────────────┤
│ [Básico] [Liquidez] [Greeks] [Volatilidade] [Lançador] [Personalizar]       │
│                                                                               │
│ Strikes: [±10 ▼]  [ ] Só com preço  [ ] Só mercado bilateral                │
│ [ ] Ocultar spread >30%             Buscar contrato [________]               │
├───────────────────────────────────────────────────────────────────────────────┤
│                 CALLS               │ STRIKE │               PUTS             │
│ OI     Vol    Δ     IV   Bid   Ask  │        │ Bid   Ask    IV     Δ  Vol OI │
├─────────────────────────────────────┼────────┼───────────────────────────────┤
│ 1.2M   132k  .72   46%  4.24  4.32 │ 46,61  │ .66  1.87   54%  -.18 382k .8M│
│ ...                                 │ 48,86  │ ...                           │
│                                     │        │                               │
├─────────────────────────────────────┼────────┼───────────────────────────────┤
│                         PETR4  ●  R$49,60                                   │
├─────────────────────────────────────┼────────┼───────────────────────────────┤
│ 7.8M   505k  .52   41%  2.01  2.40 │ 49,61  │1.79  2.50   47%  -.47 533k 7M│
│ 1.1M   778k  .46   43%  2.14  2.27 │ 49,86  │1.90  2.15   42%  -.52 874k .8M│
│ ...                                 │ 50,36  │ ...                           │
└─────────────────────────────────────┴────────┴───────────────────────────────┘
```

---

# 2. Cabeçalho

## Linha 1

- logo BOLSABR;
- busca global;
- freshness/fonte.

Exemplo:

`Dados B3 · fechamento 23/09/2026`

Nunca esconder a data do dado.

## Ativo

Mostrar:

- PETR4;
- nome;
- classe;
- spot;
- variação quando disponível;
- status EOD.

Não mostrar 20 indicadores antes da chain.

---

# 3. Abas do ativo

V1:

- Opções
- Volatilidade
- Dividendos
- Eventos

Somente **Opções** precisa estar funcional no primeiro protótipo.

As demais podem estabelecer arquitetura de navegação sem implementar toda a feature.

---

# 4. Vencimentos

## Representação

Chip:

```text
16 OUT
MENSAL
23d
```

Compacto:

`16 OUT · M · 23d`

Weekly:

`02 OUT · S · 9d`

## Dados

O API fornece:

- date;
- type WEEKLY/MONTHLY;
- dte_calendar;
- dte_business.

Tooltip:

```text
Vencimento mensal
23 dias corridos
16 pregões
```

## Default

Novo usuário:

**próximo MONTHLY com liquidez material.**

No snapshot analisado:

16/10/2026:
- 130 contratos TWO_SIDED;
- 193 contratos com IV;
- ~53 milhões de volume;
- ~239,7 milhões de OI.

25/09/2026 semanal:
- 19 TWO_SIDED;
- spread bilateral mediano ~66,7%.

Portanto o default do protótipo será **16/10**.

## Usuário recorrente

Persistir último vencimento/tipo preferido posteriormente.

---

# 5. Janela de strikes

Não renderizar 224 strikes de uma vez por padrão.

Default desktop:

**±10 strikes ao redor do ATM**.

Controles:

- ±5
- ±10
- ±20
- Todos

Botões adicionais:

`↑ mais strikes`

`↓ mais strikes`

A troca deve ser local/imediata.

---

# 6. Marcador ATM

O spot deve atravessar visualmente a grade.

Exemplo:

```text
48,86
49,36
──────── PETR4 49,60 ────────
49,61
49,86
50,36
```

Não criar uma linha fictícia de opção.

O marcador fica entre os strikes corretos.

---

# 7. Presets

## Básico

Para usuário novo:

CALL:
- Last
- Bid
- Ask
- Volume
- OI

PUT:
- Bid
- Ask
- Last
- Volume
- OI

## Liquidez

- Bid
- Ask
- Spread %
- Negócios
- Volume
- OI

## Greeks

- IV
- Delta
- Gamma
- Theta
- Vega

## Volatilidade

V1:
- IV
- price_basis
- spread %

Depois:
- IV Bid
- IV Ask
- HV
- IV Rank
- IV Percentile

## Lançador

Posteriormente:
- prêmio
- prêmio %
- distância do strike
- Delta
- Theta
- OI
- yield
- break-even

Não bloquear o MVP esperando este preset.

---

# 8. Densidade de dados

## Regra

A grade pode ser densa.

O resto da página não.

A chain é a superfície profissional; header/filtros devem permanecer simples.

## Números

Formatação compacta:

- 7.756.100 → 7,76M
- 505.300 → 505k
- Delta 0.5234 → 0,52
- IV 0.4062 → 40,62%

Tooltip mostra valor completo.

---

# 9. Quote quality

O produto NÃO deve pintar todos os números como igualmente confiáveis.

## TWO_SIDED

Mercado bilateral.

Visual normal.

## ONE_SIDED

Somente Bid ou Ask.

Visual ligeiramente atenuado.

Tooltip:

`Somente uma ponta disponível no fechamento.`

## LAST_ONLY

Sem Bid/Ask útil.

Mostrar Last, mas analytics com indicador de qualidade.

Tooltip:

`IV calculada a partir do último negócio; esse negócio pode não estar sincronizado com o fechamento do ativo.`

## NO_PRICE

Sem preço útil.

Não esconder por padrão da base completa, porém:

- linha muito atenuada;
- analytics `—`;
- filtros permitem ocultar.

## WIDE_SPREAD_GT_30PCT

Mostrar ícone discreto ao lado do preço/IV.

Não usar vermelho de erro; spread largo não é erro de sistema.

---

# 10. Cor

O significado não pode depender exclusivamente da cor.

Sugestão sem fechar branding:

- fundo neutro;
- CALL e PUT diferenciados por label/cabeçalho, não por duas cores saturadas;
- ATM com contraste forte;
- estados de qualidade por opacidade + ícone + tooltip;
- verde/vermelho reservado para P&L/variação, não para decoração.

---

# 11. Seleção de contrato

Clique simples:

abre drawer lateral.

Exemplo:

```text
PETRJ510
CALL · AMERICANA
Venc. 16/10/2026
Strike R$49,86

Mercado
Bid        2,14
Ask        2,27
Last       2,22
Spread     5,9%
Negócios   ...
Volume     ...
OI         ...

Analytics
IV         43,13%
Delta      ...
Gamma      ...
Theta      ...
Vega       ...

Cálculo
Preço usado     MID
Taxa DI1        ...
Modelo          BSM_AMERICAN_CALL_NO_DIVIDEND

[ Selecionar para estratégia ]
```

Na Fase 1 o botão apenas adiciona o contrato a uma seleção local.

Não executa ordem.

---

# 12. Seleção para futura estratégia

Quando 1+ legs forem selecionadas:

barra inferior:

```text
1 contrato selecionado
PETRJ510 · Comprar

[Limpar]                         [Analisar estratégia]
```

Na Fase 1, `Analisar estratégia` pode estar marcado como próximo módulo ou abrir uma visão simples.

A estrutura deve permitir evoluir para Strategy Builder sem redesenhar a chain.

---

# 13. Filtros

## V1

- vencimento;
- janela de strikes;
- só com preço;
- só TWO_SIDED;
- ocultar spread >30%;
- CALL/PUT via própria grade;
- busca por ticker do contrato.

## Depois

- Delta
- IV
- OI
- Volume
- moneyness
- exercício
- yield
- probabilidade

---

# 14. Ordenação

A chain não deve ser ordenada por IV/volume como uma tabela comum, porque isso destrói a geometria CALL–STRIKE–PUT.

Ordenação principal fixa:

**strike ascendente**.

Filtros removem linhas; não reorganizam a relação por strike.

Scanners/rankings pertencem a outra superfície.

---

# 15. Mobile / viewport estreito

Não tentar comprimir a chain bilateral completa em 390px.

Estratégia:

```text
[CALL | PUT]

Strike 49,86
PETRJ510

Bid    2,14
Ask    2,27
IV     43,13%
Delta  ...
OI     1,19M
```

Toggle:

`CALL | PUT`

O strike permanece sticky.

Outra alternativa posterior:
horizontal scroll controlado, mas não como experiência principal.

---

# 16. Loading

## Primeiro carregamento

Skeleton:
- header;
- chips;
- ~15 linhas de chain.

Não usar spinner central bloqueando a página.

## Troca de vencimento

Se payload completa já está em memória:

zero network request.

Atualização instantânea.

## Evolução por endpoint

Se passarmos a endpoint por vencimento:

prefetch do próximo mensal + vencimento adjacente.

---

# 17. Performance

Payload PETR4 completa:

- ~1,94 MB minificada;
- ~117 KB gzip.

Logo, no MVP podemos carregar tudo de uma vez.

Mesmo assim:

- não renderizar 1.767 linhas;
- renderizar apenas o vencimento ativo;
- default ±10 strikes;
- virtualização quando `Todos`.

---

# 18. Acessibilidade

- keyboard navigation nas linhas;
- foco visível;
- tooltips acessíveis por teclado;
- não depender apenas de cor;
- números alinhados tabularmente;
- headers sticky;
- `aria-label` com ticker/tipo/strike para células interativas.

---

# 19. SEO

Página pública:

`/acoes/PETR4/opcoes`

Posteriormente:

`/opcoes/PETRJ510`

O HTML inicial deve expor conteúdo útil além do shell JS:

- PETR4;
- snapshot;
- vencimentos;
- strikes principais;
- explicação da chain.

---

# 20. Componentes conceituais

```text
OptionChainPage
├── AssetSearch
├── AssetHeader
├── AssetTabs
├── ExpirationStrip
├── ChainToolbar
│   ├── ColumnPreset
│   ├── StrikeWindow
│   └── QualityFilters
├── OptionChainGrid
│   ├── ChainHeader
│   ├── StrikeRow*
│   │   ├── CallCells
│   │   ├── StrikeCell
│   │   └── PutCells
│   └── SpotMarker
├── OptionDetailDrawer
└── SelectedLegsBar
```

---

# 21. Critérios do primeiro protótipo

O protótipo estará correto quando:

1. abre PETR4 no mensal líquido;
2. mostra spot e freshness;
3. alterna vencimentos instantaneamente;
4. ATM é identificável em menos de um segundo;
5. Bid/Ask/OI/Volume são legíveis sem abrir detalhes;
6. preset Greeks não destrói o alinhamento;
7. contratos LAST_ONLY/ONE_SIDED não parecem tão confiáveis quanto TWO_SIDED;
8. clique abre detalhes auditáveis;
9. usuário consegue selecionar legs;
10. não existe qualquer botão que sugira execução real de ordem.

---

# 22. Próximo passo depois deste wireframe

Construir um protótipo web usando o artifact real:

`petr4-option-chain-v0.json`.

O protótipo deve ser avaliado visualmente contra:

- Profit;
- OpLab;
- Opções.Net.Br;

sem copiar o design literal de nenhum deles.
