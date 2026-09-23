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

**Fase: Discovery / Proof of Data**

Próximo marco técnico:

> Reconstruir uma Option Chain real de PETR4 utilizando fontes próprias/oficiais e validar strike, vencimento, tipo, preço, volume, open interest, IV e Greeks contra referências de mercado.

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
- [Roadmap](docs/roadmap.md)

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
