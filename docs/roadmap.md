# Roadmap — BOLSABR

## Estado atual

**Fase 0: núcleo técnico validado.**

**Fase 1: MVP read-only funcional, ainda não encerrado.**

A aplicação de produção já usa Next.js + FastAPI, snapshots EOD oficiais e busca multiativo. PETR4, VALE3 e ITUB4 foram validados ao vivo em B3.

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

**Em andamento — núcleo read-only operacional.**

Issue principal:
`#6 — Option Chain Web Read-only`.

### Concluído

- UX desktop/mobile validada;
- Next.js 16 + TypeScript;
- FastAPI read-only;
- SnapshotStore EOD imutável;
- Docker/Coolify topology;
- Option Chain ligada a endpoint HTTP;
- busca real baseada em snapshots publicados;
- multiativo PETR4 / VALE3 / ITUB4 validado ao vivo;
- presets Básico/Liquidez/Greeks;
- filtros de qualidade;
- ATM marker;
- drawer de contrato;
- seleção local de legs;
- SEO/SSR na rota de ativo;
- CI: unit/API/build/visual/E2E/deployment/live multiasset.

### Próximo gate

Fechar a superfície pública read-only antes de conta/carteira:

1. histórico/gráficos básicos;
2. ampliar universo EOD;
3. performance final com dataset maior;
4. deploy staging/público em Coolify.

### Entregáveis restantes

- página individual de opção — concluída;
- sitemap/SEO programático por contrato — concluído;
- histórico de preço/IV/OI por contrato;
- gráficos básicos;
- universo EOD além dos três ativos de prova;
- deploy staging/público;
- performance/virtualização somente se profiling justificar.

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
