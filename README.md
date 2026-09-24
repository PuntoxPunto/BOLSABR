# BOLSABR

Plataforma brasileira de análise e gestão de investimentos com foco profundo em opções da B3.

## Visão

BOLSABR combina:

- Option Chain profissional
- Carteira consolidada
- Estratégias com opções
- Dividendos e proventos
- Vencimentos e calendário
- Analytics de volatilidade e Greeks

A proposta é unir a ergonomia de leitura do **Profit/Nelogica**, a profundidade quantitativa de **OpLab/Opções.Net.Br** e a gestão de carteira/proventos do **Investidor10**, em uma experiência web moderna.

## Tese

O produto não pretende substituir uma corretora ou terminal de execução.

A proposta é ser o **painel de inteligência do investidor brasileiro que utiliza ações e opções**.

A mesma ação deve ser entendida como:

- ativo em carteira;
- underlying de opções;
- geradora de dividendos;
- componente de estratégias;
- fonte de eventos no calendário;
- geradora de renda e risco.

## Estado atual

**Fase 0 — Proof of Data: núcleo técnico validado**

A Option Chain EOD de PETR4 já é reconstruída diretamente de fontes oficiais.

Snapshot live validado em **23/09/2026**:

- PETR4: **R$ 49,60**
- **3.534** contratos de opções
- **30** vencimentos
- **1.767** linhas de strike
- **833** registros PETR4/opções encontrados no COTAHIST
- **319** com Bid/Ask bilateral válido
- **45** vértices DI1
- Corporate Actions PETR4 identificados por ISIN `BRPETRACNPR6`

O CI gera uma payload frontend-ready:

`petr4-option-chain-v0.json`

Características do artifact validado:

- schema: **0.1**
- 3.534 legs
- 30 vencimentos
- ~3,8 MB pretty JSON
- ~1,94 MB minificado
- ~117 KB estimados com gzip
- 756 contratos com IV calculável no snapshot

Distribuição de quote-state no snapshot:

- TWO_SIDED: 318
- ONE_SIDED: 251
- LAST_ONLY: 263
- NO_PRICE: 2.702

Isso reforça que o produto deve mostrar qualidade/liquidez da observação e não tratar todas as séries como igualmente úteis.

### Já concluído

- ingestão B3 `InstrumentsConsolidated`;
- `TradeInformationConsolidated`;
- `DerivativesOpenPosition`;
- COTAHIST para Bid/Ask EOD;
- normalização da Option Chain;
- curva DI1 por vencimento via PU/fator de desconto;
- Selic/BCB como fallback;
- Black-Scholes-Merton;
- CRR para casos americanos que realmente exigem exercício antecipado;
- equivalência BSM para CALL americana sem dividendos futuros;
- IV por bisseção;
- Delta/Gamma/Theta/Vega/Rho;
- Corporate Actions B3 via `GetListedSupplementCompany`;
- identidade por ISIN;
- calendário B3 2026 e derivação de data EX;
- metadata transparente de qualidade de mercado;
- Option Chain API schema v0.1;
- testes + live smoke em GitHub Actions.

### Ainda aberto na Fase 0

- ampliar benchmark quantitativo contra OpLab/Profit;
- formalizar tolerâncias finais de IV/Greeks;
- tratamento de dividendos discretos futuros em opções americanas;
- versionar calendários B3 adicionais quando necessário.

## Próxima fase

**Fase 1 — Option Chain Web Read-only**

Issue: https://github.com/PuntoxPunto/BOLSABR/issues/6

Próximo entregável:

> Wireframe funcional da tela PETR4 consumindo somente o Option Chain API v0.1.

## Benchmarks

- Profit Pro / Nelogica — grade, leitura rápida, estratégias
- Opções.Net.Br — profundidade, histórico, SEO
- OpLab — volatilidade, Greeks, scanners e payoff
- Investidor10 — carteira, patrimônio e proventos
- OptionStrat e ferramentas internacionais — visualização de estratégias

## Documentação

- [PRD v0.1](docs/PRD.md)
- [Estratégia de dados](docs/data-sources.md)
- [Arquitetura inicial](docs/architecture.md)
- [Proof of Data PETR4](docs/proof-of-data-petr4.md)
- [Option Chain API v0.1](docs/api-option-chain-v0.md)
- [Benchmark PETR4 22/09/2026](docs/research/benchmark-petr4-2026-09-22.md)
- [Roadmap](docs/roadmap.md)
- [Benchmarks](docs/research/benchmarks.md)

## Princípios

1. B3/CVM/BCB como fontes primárias sempre que possível.
2. Não depender de scraping de concorrentes.
3. Guardar histórico próprio desde o primeiro dia.
4. Transactions/events como fonte de verdade da carteira.
5. Option Chain essencial deve permanecer útil no plano gratuito.
6. Separar dados observados, inputs analíticos e métricas calculadas.
7. Mostrar freshness e qualidade da observação.
8. Produto primeiro para ações + opções; ampliar classes depois.

## Repositório

Este repositório é a fonte de verdade para produto, pesquisa, arquitetura e implementação do BOLSABR.
