# Roadmap — BOLSABR

## Estado atual

Discovery consolidando.

**Próxima etapa obrigatória: Proof of Data PETR4.**

---

## Fase 0 — Proof of Data

Objetivo: reconstruir uma Option Chain confiável sem depender de concorrentes.

### Entregáveis
- parser da fonte oficial de instrumentos
- universo de opções PETR4
- vencimentos
- strikes
- CALL/PUT
- estilo de exercício
- preços
- volume
- open interest
- IV
- Greeks

### Validação
Comparar com:
- Profit
- OpLab
- Opções.Net.Br
- brapi

### Gate
Não estabilizar frontend/API antes de entender divergências materiais.

---

## Fase 1 — Read-only MVP

Sem login.

### Entregáveis
- busca
- página PETR4
- Option Chain
- filtros de vencimento
- presets de colunas
- página individual da opção
- IV
- Greeks
- gráficos básicos

### Objetivo
Validar utilidade e UX da Chain.

---

## Fase 2 — Conta + Carteira

### Entregáveis
- autenticação
- criação de carteira
- lançamentos manuais
- ações
- opções
- preço médio
- posições
- resultado realizado/não realizado
- patrimônio

### Gate
A carteira deve ser reconstruível pelo histórico de eventos.

---

## Fase 3 — Strategy Builder

### Entregáveis
- seleção de legs pela Chain
- 2–4 legs
- reconhecimento de estratégias
- payoff
- risco máximo
- lucro máximo
- break-even
- Greeks agregados
- salvar estratégia

---

## Fase 4 — Renda

### Entregáveis
- dividendos
- JCP
- prêmio recebido
- prêmio pago
- resultado realizado
- visão mensal
- 12 meses
- por ativo
- por estratégia

---

## Fase 5 — Calendário + Alertas

### Entregáveis
- vencimentos
- datas EX
- pagamentos
- eventos da carteira
- alertas de vencimento
- alerta próximo ao strike
- ITM
- evento de provento

---

## Fase 6 — Analytics Pro

### Entregáveis
- IV Rank
- IV Percentile
- volatility surface
- histórico extenso
- scanners
- alertas customizados
- simulação temporal avançada
- análise de rolagem

---

## Fase 7 — Market Data intraday

Somente após:
- tração comprovada
- modelo de negócio validado
- análise/licenciamento B3 concluído

Possíveis níveis:
- delayed
- snapshot
- real-time

---

## Fase 8 — Expansão de carteira

Depois da proposta principal estar validada:
- FIIs
- ETFs
- BDRs
- renda fixa
- exterior
- cripto
- fiscalidade

---

## Backlog futuro

- importação de notas
- integração B3/corretoras
- tax lots
- IR
- backtesting
- API pública
- app mobile
- notificações push
- relatórios
- journal de operações

---

## Decisões vigentes

- ações + opções primeiro
- PETR4 como Proof of Data
- Option Chain como aquisição
- carteira como retenção
- dividendos + vencimentos como hábito recorrente
- analytics avançados como monetização
- sem execução de ordens no MVP
