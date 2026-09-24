# Benchmark PETR4 — 22/09/2026

## Objetivo

Validar o motor de IV/Greeks do BOLSABR contra uma referência pública externa sem confundir observações de mercado diferentes.

Data de referência do snapshot B3: **22/09/2026**.

## Regra metodológica

Existem pelo menos três preços diferentes que podem ser usados no cálculo de IV:

1. **MID de fechamento** — média entre Bid/Ask EOD quando ambos existem.
2. **Último negócio** — último preço negociado da opção.
3. **Último negócio sincronizado** — preço da opção e preço do underlying no mesmo instante.

BOLSABR consegue calcular (1) e (2) com os dados EOD atuais.

Opções.Net.Br informa que seus gráficos relacionam as cotações da opção com o horário aproximado em que ocorreram. Portanto a IV publicada para `Ult` não deve ser comparada diretamente com uma IV calculada usando o último preço da opção e o **fechamento** do underlying, caso o contrato seja ilíquido.

### Política BOLSABR

- `TWO_SIDED` → usar MID como IV principal EOD.
- `ONE_SIDED` → não inventar MID; LAST pode ser fallback.
- `LAST_ONLY` → IV marcada como qualidade inferior.
- `NO_PRICE` → sem IV.
- Benchmark quantitativo principal deve priorizar contratos líquidos / observações comparáveis.

---

## PETRV483 — PUT europeia

- Underlying: PETR4
- Spot de fechamento B3: **R$ 48,35**
- Strike: **R$ 47,11**
- Vencimento: **16/10/2026**
- DTE calendário: **24**
- Bid EOD: **R$ 1,00**
- Ask EOD: **R$ 1,30**
- Último: **R$ 1,30**
- OI: **1.005.200**
- Taxa DI1 equivalente contínua para o vencimento: aproximadamente **12,78% a.a.**

### BOLSABR — MID EOD

Preço usado: **R$ 1,15**

IV: aproximadamente **38,14%**

Esse é nosso indicador primário de IV EOD, mas não deve ser comparado com a coluna `Ult` de Opções.Net.Br porque os preços usados são diferentes.

### BOLSABR — LAST vs referência externa

Preço usado: **R$ 1,30**

IV BOLSABR: aproximadamente **41,41%**

Opções.Net.Br em 22/09/2026:
- último preço: R$ 1,30
- IV `Ult`: **41,23%**

Diferença: aproximadamente **0,18 ponto percentual de volatilidade**.

Referência:
https://opcoes.net.br/PETRV483

### Resultado

A PUT europeia valida fortemente:
- spot;
- strike;
- tempo;
- taxa;
- Black-Scholes-Merton;
- solver de IV.

---

## PETRK442 — CALL americana

- Underlying: PETR4
- Spot de fechamento B3: **R$ 48,35**
- Strike: **R$ 41,91**
- Vencimento: **19/11/2026**
- DTE calendário: **58**
- Último: **R$ 7,78**
- OI BOLSABR snapshot: **45.900**
- Sem Bid/Ask completo EOD no COTAHIST selecionado.
- Taxa DI1 equivalente contínua para o vencimento: aproximadamente **12,38% a.a.**

Usando o último preço e taxa DI1, BOLSABR fica próximo de **38,9% IV**.

Opções.Net.Br em 22/09/2026:
- último: R$ 7,78
- IV `Ult`: **39,04%**

Diferença aproximada: **0,1–0,2 ponto percentual**.

Referência:
https://opcoes.net.br/PETRK442

### Resultado

Como não havia data-COM futura conhecida entre 22/09/2026 e esse vencimento, uma CALL americana não possui prêmio econômico de exercício antecipado por dividendos. O BOLSABR usa, nesse caso, a equivalência exata com BSM e registra o modelo como `BSM_AMERICAN_CALL_NO_DIVIDEND`.

O resultado é coerente com o benchmark externo sem pagar o custo computacional de uma árvore CRR desnecessária.

---

## PETRL56 — exemplo de contrato NÃO adequado para calibrar

- Strike B3/Opções.Net.Br: **R$ 36,91**
- Vencimento: **18/12/2026**
- Último em 22/09: **R$ 12,40**
- Apenas **2 negócios** no dia segundo Opções.Net.Br.
- Bid EOD B3: R$ 11,39
- Ask EOD: ausente.

Opções.Net.Br publica IV `Ult` de **24,72%**, mas também deixa claro que a IV histórica é relacionada ao horário aproximado dos negócios da opção.

Como o último negócio pode ter ocorrido com PETR4 em outro preço, combinar R$12,40 com o spot de fechamento R$48,35 produz uma observação temporalmente inconsistente.

Referência:
https://opcoes.net.br/PETRL56

### Decisão

**Excluir contratos desse tipo da calibração quantitativa.**

Eles continuam na Option Chain, mas devem carregar estado `ONE_SIDED` ou `LAST_ONLY` e qualidade inferior para analytics.

---

## Curva DI1

O BOLSABR utiliza os PUs de ajuste B3 como fatores de desconto observados:

```text
DF = AdjstdQt / 100000
```

Entre vértices:

- interpolação linear de `log(DF)` por data calendário;
- depois conversão do DF para taxa contínua equivalente para o tempo calendário do modelo.

Isso evita converter a taxa DI1 de base 252 para um modelo com `T = dias/365` sem explicitar a convenção.

Exemplos no snapshot:

| Vencimento opção | Taxa contínua equivalente aproximada |
|---|---:|
| 16/10/2026 | 12,78% |
| 19/11/2026 | 12,38% |
| 18/12/2026 | 12,27% |

---

## Conclusão parcial

O motor já está suficientemente próximo das referências externas em contratos comparáveis para avançar.

O próximo benchmark deve usar uma amostra maior, priorizando:

- vencimento mensal;
- strikes próximos ao ATM;
- Bid/Ask completo;
- spread controlado;
- volume e OI relevantes.

A validação de **raw market data** e a validação de **analytics** devem permanecer separadas.


---

## Corporate Actions na data de referência

A página oficial da B3 para PETROBRAS registra proventos PN deliberados em 06/08/2026 com último dia com direito em **21/08/2026** e pagamentos em novembro/dezembro de 2026.

Como o snapshot do benchmark é 22/09/2026, esses eventos já estavam EX.

Consequência metodológica:

- entram no calendário/carteira como pagamentos futuros;
- não são descontados novamente do spot no pricing das opções;
- a existência de pagamento futuro, por si só, não significa dividendo futuro relevante para a opção; o evento relevante para pricing é a data EX ainda não ocorrida.

Fonte oficial:
https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/main/9512/PETR/corporate-actions?language=pt-BR
