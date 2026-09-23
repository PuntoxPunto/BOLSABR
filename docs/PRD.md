# PRD v0.1 — BOLSABR

## 1. Visão do produto

Plataforma brasileira de análise e gestão de investimentos com especialização profunda em opções da B3.

O produto combina:

**Option Chain profissional + carteira + estratégias + dividendos/proventos + vencimentos + analytics.**

Não é uma corretora nem um terminal de execução. É o painel de inteligência do investidor que utiliza ações e opções.

---

## 2. Benchmarks

### Profit / Nelogica
Referência para:
- Chain bilateral: CALLs à esquerda, strike ao centro, PUTs à direita
- strikes próximos ao dinheiro
- vencimentos
- colunas configuráveis
- Bid/Ask
- IV e Greeks
- criação de estratégias
- payoff

### Opções.Net.Br
Referência para:
- profundidade de informação
- histórico
- páginas individuais de contratos
- SEO programático
- universo amplo de opções

Não utilizar como datasource.

### OpLab
Referência para:
- IV
- Greeks
- scanners
- estratégias
- payoff
- analytics de derivativos

### Investidor10
Referência para:
- carteira
- patrimônio
- rentabilidade
- proventos
- calendário
- experiência simples para pessoa física

### Ferramentas internacionais
OptionStrat/TradingView e similares como referência para visualização moderna e interação.

---

## 3. Navegação principal

Cinco áreas conectadas:

1. **Mercado** — ativos e Option Chain
2. **Estratégias** — criação, análise e payoff
3. **Carteira** — posições, patrimônio e performance
4. **Renda** — dividendos, JCP e resultado de opções
5. **Calendário** — vencimentos, proventos e eventos

---

## 4. Dashboard

### Patrimônio
- patrimônio atual
- total investido
- resultado realizado
- resultado não realizado
- rentabilidade
- evolução 1M / 3M / 12M / YTD / total

### Renda
Separar:
- dividendos
- JCP
- rendimentos
- prêmio recebido
- prêmio pago
- resultado realizado em opções

**Regra:** prêmio recebido não é automaticamente lucro.

### Eventos próximos
- opções vencendo
- datas EX
- pagamentos de proventos
- eventos corporativos

### Estratégias ativas
Exemplos:
- Covered Calls
- Cash Secured Puts
- Bull Call Spreads
- posições simples

---

## 5. Option Chain

A Option Chain é a principal superfície pública e de aquisição.

### Cabeçalho
- ticker
- preço do ativo
- variação
- IV
- HV20 / HV30
- IV Rank
- IV Percentile
- volume de opções
- Put/Call Ratio
- próximo vencimento

### Vencimentos
Chips por vencimento com:
- data
- dias corridos
- dias úteis
- semanal/mensal

### Layout desktop

```text
CALLS                              PUTS
OI Δ IV Bid Ask | STRIKE | Bid Ask IV Δ OI
                  44,00
                  45,00
                  46,00
                 ───────
                PETR4 47,42
                 ───────
                  48,00
                  49,00
```

O spot deve funcionar como marcador visual entre os strikes.

---

## 6. Presets de colunas

### Básico
- Último
- Bid
- Ask
- Volume
- OI

### Liquidez
- Bid
- Ask
- Spread %
- Volume
- OI
- Negócios

### Volatilidade
- IV
- IV Bid
- IV Ask
- HV
- IV/HV
- IV Rank

### Greeks
- Delta
- Gamma
- Theta
- Vega

### Lançador
- prêmio
- prêmio %
- distância do strike
- Delta
- Theta
- OI
- yield anualizado
- break-even

### Personalizado
Colunas escolhidas pelo usuário.

---

## 7. Dados da Chain

### Dados brutos
- ticker
- underlying
- call/put
- strike
- vencimento
- tipo de exercício
- último
- bid
- ask
- abertura
- máxima
- mínima
- fechamento anterior
- quantidade
- número de negócios
- volume financeiro
- open interest

### Dados calculados
- spread absoluto
- spread percentual
- moneyness
- ITM / ATM / OTM
- valor intrínseco
- valor extrínseco
- volatilidade implícita
- Delta
- Gamma
- Theta
- Vega
- Rho
- probabilidade aproximada ITM
- distância ao strike
- yield do prêmio
- yield anualizado
- IV Rank
- IV Percentile

---

## 8. Strategy Builder

O usuário seleciona pernas diretamente da Chain.

O sistema identifica estruturas conhecidas quando possível.

Mostrar:
- legs
- quantidade
- preços
- crédito/débito
- lucro máximo
- risco máximo
- break-even
- Delta agregado
- Gamma agregado
- Theta agregado
- Vega agregado
- dias até vencimento
- payoff

Simulações:
- hoje
- +7 dias
- +14 dias
- vencimento

Permitir alterar:
- preço do underlying
- volatilidade
- tempo

V1 sem execução de ordens.

---

## 9. Carteira

Escopo inicial:
- ações
- opções

Depois:
- FIIs
- ETFs
- renda fixa
- BDRs
- exterior
- cripto

### Eventos suportados
- compra
- venda
- dividendos
- JCP
- bonificação
- subscrição
- desdobramento
- grupamento
- compra de opção
- venda de opção
- encerramento
- exercício
- atribuição
- rolagem

**Fonte de verdade:** histórico de Transactions/Events.

Position deve ser derivada dos eventos, não armazenada como verdade isolada.

---

## 10. Relação ações + opções

### Covered Call
Se o usuário possui 500 PETR4 e -5 CALLs compatíveis, identificar automaticamente a cobertura.

Mostrar:
- quantidade coberta
- quantidade descoberta
- prêmio recebido
- preço médio
- strike
- preço efetivo de saída
- yield
- distância ao strike
- DTE
- ITM/OTM

### PUT vendida
Mostrar:
- obrigação potencial
- capital necessário para exercício
- prêmio recebido
- preço econômico de aquisição considerando o prêmio

Exemplo:
Strike R$35, prêmio R$1,20 → custo econômico R$33,80.

Manter separado do preço contábil do exercício.

---

## 11. Renda / Proventos

Separar:

### Corporativo
- dividendos
- JCP
- rendimentos
- amortizações

### Derivativos
- prêmio recebido
- prêmio pago
- resultado realizado
- exercício

Visões:
- mensal
- 12 meses
- por ativo
- por estratégia
- por tipo

---

## 12. Calendário

Eventos:
- vencimentos
- data COM
- data EX
- pagamentos
- exercício
- eventos corporativos
- resultados futuramente

Filtros:
- Tudo
- Minha carteira
- Opções
- Dividendos
- Resultados

Cada vencimento deve ligar para:
- Ver cadeia
- Simular fechamento
- Simular rolagem

---

## 13. Dividendos + opções

Se uma data EX ocorrer antes do vencimento de uma opção da carteira, mostrar o evento no contexto da posição.

A plataforma deve informar impactos e contexto, sem executar ou recomendar automaticamente uma operação.

---

## 14. Alertas

V1:
- opção vence em X dias
- posição entrou ITM
- preço próximo do strike
- mudança importante de IV
- data EX próxima
- provento anunciado
- pagamento de provento

Posteriormente:
- condições de rolagem
- IV Rank
- Delta
- Theta
- OI

---

## 15. Página individual da opção

URL própria, ex.:

`/opcoes/PETRJ400`

Mostrar:
- ticker
- tipo
- underlying
- strike
- vencimento
- exercício
- preço
- bid/ask
- volume
- OI
- IV
- Greeks
- histórico
- moneyness
- intrínseco/extrínseco
- gráfico

Objetivo adicional: SEO programático.

---

## 16. Página do ativo

Ex.:

`/acoes/PETR4`

Tabs:
- Visão geral
- Opções
- Volatilidade
- Dividendos
- Fundamentos
- Eventos

---

## 17. Free vs Pro — hipótese

### FREE
- Option Chain EOD
- vencimentos
- strikes
- volume
- OI
- IV
- Greeks básicos
- carteira manual
- patrimônio
- operações
- dividendos
- calendário
- payoff simples
- histórico limitado

### PRO
- delay/real-time quando licenciado
- sincronização B3
- histórico completo
- IV Rank
- IV Percentile
- volatility surface
- scanners
- alertas avançados
- simulação temporal
- estratégias avançadas
- analytics de renda
- exportação
- fiscalidade posteriormente

**Regra:** a Option Chain essencial não deve ficar bloqueada no PRO.

---

## 18. Fora do MVP

Não construir inicialmente:
- execução de ordens
- book completo
- Times & Trades
- tape reading
- rede social
- cursos
- recomendações automáticas
- IA escolhendo operações
- IR completo
- todas as classes de ativos
- integrações com todas as corretoras

---

## 19. MVP

1. Market Data PETR4
2. Option Chain
3. Strategy Builder 2–4 legs
4. Carteira ações + opções
5. Dividendos/JCP
6. Calendário

---

## 20. North Star Metric

**Usuários com pelo menos uma posição ou estratégia acompanhada semanalmente.**

Métricas secundárias:
- Chains abertas
- contratos analisados
- estratégias salvas
- posições cadastradas
- alertas configurados
- retorno semanal
- conversão Free → Pro

---

## 21. Diferencial

A oportunidade está na interseção:

> entender profundamente a relação entre carteira de ações, renda, dividendos e opções.

A mesma PETR4 deve aparecer como ação, posição, underlying, fonte de dividendos, componente de estratégia, evento de calendário, renda e risco.
