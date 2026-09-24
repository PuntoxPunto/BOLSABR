# Roadmap — BOLSABR

## Estado atual

**Fase 0: núcleo técnico validado.**

**Fase 1: protótipo read-only iniciado.**

A primeira Option Chain PETR4 já é produzida diretamente de fontes oficiais e existe um protótipo web interativo consumindo o contrato de API v0.1.

---

## Fase 0 — Proof of Data

Objetivo: reconstruir uma Option Chain confiável sem depender de concorrentes.

### Concluído

- cadastro oficial de instrumentos;
- universo PETR4;
- vencimentos;
- WEEKLY/MONTHLY;
- strikes;
- CALL/PUT;
- estilo de exercício;
- preços EOD;
- Bid/Ask COTAHIST;
- volume;
- open interest;
- curva DI1;
- IV;
- Greeks;
- Corporate Actions via ISIN;
- calendário B3 2026;
- data EX;
- quote quality;
- API schema v0.1;
- artifact frontend-ready;
- benchmark inicial.

### Gates residuais

- ampliar benchmark contra Profit/OpLab;
- formalizar tolerâncias finais;
- dividendos discretos futuros em pricing americano.

### Status

Esses gates residuais não bloqueiam a Fase 1.

---

## Fase 1 — Read-only MVP

Sem login.

### Estado

**Em andamento.**

Issue:
`#6 — Option Chain Web Read-only`.

### Concluído

- wireframe orientado por dados;
- default de vencimento baseado em liquidez real;
- contrato API;
- protótipo HTML/CSS/JS;
- presets Básico/Liquidez/Greeks;
- filtros de qualidade;
- ATM marker;
- drawer de contrato;
- seleção local de legs;
- CI próprio para o protótipo.

### Próximo gate

**Revisão visual/interacional.**

Depois da revisão:

1. corrigir UX;
2. decidir stack de produção;
3. transformar protótipo em app público.

### Entregáveis restantes

- busca real multiativo;
- página PETR4 de produção;
- chain ligada a endpoint;
- página individual de opção;
- gráficos básicos;
- SEO/SSR ou SSG;
- performance/virtualização final.

---

## Fase 2 — Conta + Carteira

### Entregáveis

- autenticação;
- criação de carteira;
- lançamentos manuais;
- ações;
- opções;
- preço médio;
- posições;
- resultado realizado/não realizado;
- patrimônio.

### Gate

A carteira deve ser reconstruível pelo histórico de eventos.

---

## Fase 3 — Strategy Builder

### Entregáveis

- seleção de legs pela Chain;
- 2–4 legs;
- reconhecimento de estratégias;
- payoff;
- risco máximo;
- lucro máximo;
- break-even;
- Greeks agregados;
- salvar estratégia.

---

## Fase 4 — Renda

### Entregáveis

- dividendos;
- JCP;
- prêmio recebido;
- prêmio pago;
- resultado realizado;
- visão mensal;
- 12 meses;
- por ativo;
- por estratégia.

---

## Fase 5 — Calendário + Alertas

### Entregáveis

- vencimentos;
- datas EX;
- pagamentos;
- eventos da carteira;
- alertas de vencimento;
- alerta próximo ao strike;
- ITM;
- evento de provento.

Corporate Actions e calendário B3 já começaram na Fase 0 porque são dependências do pricing e do futuro módulo de renda.

---

## Fase 6 — Analytics Pro

### Entregáveis

- IV Rank;
- IV Percentile;
- volatility surface;
- histórico extenso;
- scanners;
- alertas customizados;
- simulação temporal avançada;
- análise de rolagem.

---

## Fase 7 — Market Data intraday

Somente após:

- tração comprovada;
- modelo de negócio validado;
- análise/licenciamento B3 concluído.

Possíveis níveis:

- delayed;
- snapshot;
- real-time.

---

## Fase 8 — Expansão de carteira

Depois da proposta principal estar validada:

- FIIs;
- ETFs;
- BDRs;
- renda fixa;
- exterior;
- cripto;
- fiscalidade.

---

## Backlog futuro

- importação de notas;
- integração B3/corretoras;
- tax lots;
- IR;
- backtesting;
- API pública;
- app mobile;
- notificações push;
- relatórios;
- journal de operações.

---

## Decisões vigentes

- ações + opções primeiro;
- PETR4 como Proof of Data;
- B3/CVM/BCB como fontes primárias;
- Option Chain como aquisição;
- carteira como retenção;
- dividendos + vencimentos como hábito recorrente;
- analytics avançados como monetização;
- sem execução de ordens no MVP;
- dados observados separados de analytics;
- qualidade/liquidez sempre visível;
- não escolher stack de produção antes de validar a interação do protótipo.
