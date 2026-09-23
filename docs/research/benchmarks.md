# Pesquisa e benchmarks — BOLSABR

## Objetivo

Registrar referências de mercado sem transformar concorrentes em dependência técnica.

## Opções.Net.Br

### O que nos interessa
- grade ampla de opções
- histórico
- páginas individuais por contrato
- forte indexação/SEO
- dados de fechamento gratuitos
- real-time em camada paga

### Descoberta técnica relevante
Historicamente a grade foi carregada dinamicamente via chamadas AJAX/JSON e existem referências públicas antigas a endpoints internos como `/listaopcoes/completa`.

Isso serve apenas para entender a arquitetura histórica da interface.

### Decisão
**Não usar scraping/endpoint interno como fonte do produto.**

A origem upstream do market data em tempo real não foi confirmada publicamente com segurança.

---

## Profit Pro / Nelogica

### O que nos interessa
- CALLs à esquerda
- strike central
- PUTs à direita
- ATM como referência visual
- vencimentos
- número configurável de strikes
- colunas configuráveis
- Bid/Ask
- IV
- Greeks
- criação de estratégias a partir da grade
- payoff

### Decisão
Profit é a principal referência de ergonomia para trader brasileiro, mas a interface final deve ser web-first e mais simples.

---

## OpLab

### O que nos interessa
- IV
- IV Rank / Percentile
- Greeks
- scanners
- payoff
- estratégias
- analytics específicos para derivativos

### Decisão
Usar como benchmark quantitativo e funcional.

---

## Investidor10

### O que nos interessa
- patrimônio
- carteira consolidada
- proventos
- dividendos
- calendário
- navegação simples
- experiência para investidor pessoa física

### Decisão
A principal contribuição ao BOLSABR é a retenção:

**usuário acompanha sua carteira, renda e eventos futuros no mesmo lugar onde analisa opções.**

Investidor10 deve ser referência de produto/UX, não datasource.

---

## Síntese de produto

A direção atual pode ser resumida como:

> Profit para ergonomia da Option Chain + OpLab para analytics + Investidor10 para carteira/proventos + experiência web moderna.

## Diferencial pretendido

A mesma ação é entendida simultaneamente como:
- posição
- underlying
- fonte de dividendos
- parte de uma estratégia
- evento de calendário
- fonte de renda
- componente de risco

Isso conecta mercado e carteira de forma que os benchmarks tratam de maneira separada.
