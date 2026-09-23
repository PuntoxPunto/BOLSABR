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

## Tese inicial

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

**Fase: Proof of Data PETR4**

Próximo marco técnico:

> Baixar um snapshot real da B3, reconstruir a Option Chain de PETR4 e validar strike, vencimento, tipo, preço, volume, open interest, IV e Greeks contra referências de mercado.

O primeiro pipeline já está no repositório:
- cliente B3 para datasets públicos;
- parser de CSV e regra Final/Parcial;
- normalização de instrumentos, trades e open interest;
- Black-Scholes-Merton;
- CRR para opções americanas;
- IV por bisseção;
- Greeks;
- testes unitários.

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
- [Roadmap](docs/roadmap.md)
- [Benchmarks](docs/research/benchmarks.md)

## Princípios

1. B3/CVM/BCB como fontes primárias sempre que possível.
2. Não depender de scraping de concorrentes.
3. Guardar histórico próprio desde o primeiro dia.
4. Transactions/events como fonte de verdade da carteira.
5. Option Chain essencial deve permanecer útil no plano gratuito.
6. Separar claramente dados brutos de métricas calculadas.
7. Produto primeiro para ações + opções; ampliar classes depois.

## Repositório

Este repositório será a fonte de verdade para produto, pesquisa, arquitetura e implementação do BOLSABR.
