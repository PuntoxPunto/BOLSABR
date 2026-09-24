# Fase 0 — Proof of Data PETR4

## Objetivo

Demonstrar que o BOLSABR consegue reconstruir uma Option Chain EOD auditável de PETR4 usando fontes oficiais, cálculos próprios e sem depender de scraping de concorrentes.

## Status

**Núcleo técnico validado.**

O pipeline live já produz uma Option Chain completa pronta para frontend.

Snapshot de referência validado: **23/09/2026**.

- PETR4: R$ 49,60
- 3.534 contratos
- 30 vencimentos
- 1.767 linhas de strike
- 833 registros PETR4/opções presentes no COTAHIST
- 319 registros com Bid/Ask bilateral válido
- 45 vértices DI1
- Corporate Actions PETR4 via ISIN BRPETRACNPR6

## Fontes

### InstrumentsConsolidated

Responsável pelo cadastro dos contratos.

Campos centrais:
- TckrSymb
- Asst
- SgmtNm
- SctyCtgyNm
- XprtnDt
- OptnTp
- ExrcPric
- OptnStyle
- CtrctMltplr
- ISIN

### Descoberta live de schema

Para opções sobre ações no snapshot atual:

- Asst = PETR4
- SgmtNm = EQUITY CALL ou EQUITY PUT
- SctyCtgyNm = OPTION ON EQUITIES
- UndrlygTckrSymb1/2 aparece vazio nas linhas observadas

**Decisão:** para equity options, `Asst` é o vínculo primário com o underlying.

### TradeInformationConsolidated

Uso:
- MinPric
- MaxPric
- TradAvrgPric
- LastPric
- TradQty
- FinInstrmQty
- NtlFinVol
- AdjstdQt
- AdjstdQtTax

Também fornece os dados necessários para reconstruir os vértices DI1.

### DerivativesOpenPosition

Uso:
- OpnIntrst
- VartnOpnIntrst
- CvrdQty
- UcvrdQty
- TtlPos

### COTAHIST

Complementa a chain EOD com:
- PREOFC — melhor compra
- PREOFV — melhor venda
- PREULT
- TOTNEG
- QUATOT
- VOLTOT
- PREEXE
- DATVEN

Validação live concluída.

No snapshot de 23/09:
- 833 opções/ativo PETR4 encontradas
- 319 com mercado bilateral útil

### DI1

A taxa principal do pricing vem dos futuros DI1.

O BOLSABR usa:

```text
DF = AdjstdQt / 100000
```

Entre vértices:
- interpolação linear de log(DF) por data calendário;
- conversão para taxa contínua equivalente no vencimento exato da opção.

Isso evita misturar implicitamente a convenção de cotação DI1 com `T = dias/365` do modelo.

Selic/BCB permanece apenas como fallback.

### Corporate Actions

Fonte primária:
`GetListedSupplementCompany`.

Identidade do papel:
**ISIN**, não texto de classe.

PETR4:
`BRPETRACNPR6`.

Campos:
- assetIssued
- paymentDate
- rate
- relatedTo
- approvedOn
- isinCode
- label
- lastDatePrior

No snapshot validado:
- 12 proventos PETR4 retornados
- nenhum evento com data-COM futura
- pagamentos futuros de eventos que já estavam EX

Isso permite separar:
- evento que afeta pricing;
- recebimento futuro que afeta calendário/cashflow.

## Calendário B3

O calendário de pregão é versionado.

Para 2026:
- finais de semana e fechamentos oficiais são respeitados;
- dias de sessão especial continuam sendo pregões;
- anos ainda não versionados falham explicitamente.

Exemplo:

```text
último dia com direito: 21/08/2026
data EX derivada:       24/08/2026
```

## Construção da chain

Join principal:

```text
InstrumentsConsolidated
        |
        | TckrSymb
        v
TradeInformationConsolidated
        |
        | TckrSymb
        v
DerivativesOpenPosition
        |
        +---- COTAHIST
        |
        +---- DI1
        |
        +---- Corporate Actions / ISIN
        v
Option Chain API
```

## Política de preço para analytics

### TWO_SIDED

Bid e Ask válidos.

Preço principal:
`MID = (Bid + Ask) / 2`.

### ONE_SIDED

Somente um lado válido.

Não fabricar MID.

LAST pode ser fallback.

### LAST_ONLY

Sem book útil, mas existe último negócio.

Pode gerar analytics com indicação explícita de menor qualidade.

### NO_PRICE

Sem observação suficiente.

IV/Greeks ficam nulos.

## Quality metadata

A API expõe fatos, não um score opaco:

- quote_state
- spread_pct
- trade_count
- volume
- open_interest
- quality_flags

Flags atuais:
- WIDE_SPREAD_GT_30PCT
- LAST_ONLY
- ONE_SIDED
- NO_TRADES
- NO_OPEN_INTEREST
- NO_PRICE

## Pricing

### PUT europeia

Black-Scholes-Merton.

### CALL europeia

Black-Scholes-Merton.

### CALL americana sem dividendo futuro relevante

Uma CALL americana sem dividendos futuros antes do vencimento não possui prêmio econômico de exercício antecipado.

Modelo:
`BSM_AMERICAN_CALL_NO_DIVIDEND`.

### Outros casos americanos

CRR binomial.

### IV

Solver por bisseção robusta.

O solver adapta o lower bound quando a árvore CRR ainda não está em domínio válido em volatilidades muito baixas.

## Benchmark inicial

Documentado em:

`docs/research/benchmark-petr4-2026-09-22.md`.

Resultados de referência:

### PETRV483

- último: R$ 1,30
- BOLSABR IV usando LAST + DI1: ~41,41%
- Opções.Net.Br IV Ult: 41,23%

Diferença aproximada:
**0,18 ponto percentual de IV**.

### PETRK442

- último: R$ 7,78
- BOLSABR: ~38,9%
- Opções.Net.Br: 39,04%

Diferença:
na ordem de **0,1–0,2 p.p.**.

Contratos com último negócio não sincronizado ao fechamento do underlying não são usados para calibrar o motor.

## Liquidez observada

Snapshot de 23/09:

| Estado | Contratos |
|---|---:|
| TWO_SIDED | 318 |
| ONE_SIDED | 251 |
| LAST_ONLY | 263 |
| NO_PRICE | 2.702 |

Contratos com IV calculável:
**756**.

Conclusão de produto:

> O cadastro completo deve permanecer acessível, mas a UX precisa priorizar vencimentos e strikes realmente negociáveis.

## API v0.1

O workflow produz:

- `b3-petr4-smoke.json`
- `petr4-option-chain-v0.json`

Documentação:
`docs/api-option-chain-v0.md`.

A payload separa:

- market
- analytics_input
- analytics

e inclui:
- freshness
- fonte
- DTE calendário
- DTE pregões
- taxa por vencimento
- quote quality
- modelo de pricing

## Performance

Artifact completo PETR4:

- ~3,8 MB pretty JSON
- ~1,94 MB minificado
- ~117 KB estimados com gzip

Um vencimento mensal como 16/10/2026 fica na ordem de ~26 KB gzip.

Isso permite servir a chain completa comprimida, embora a UI deva renderizar apenas o vencimento/intervalo necessário.

## Gates ainda abertos

A Fase 0 ainda mantém dois trabalhos de calibração:

1. ampliar benchmark contra OpLab/Profit e formalizar tolerâncias finais;
2. implementar dividendos discretos futuros no pricing americano quando houver evento com data EX posterior ao snapshot e anterior ao vencimento.

Esses gates não bloqueiam o início do wireframe/read-only frontend.

## Critério já atingido

Está demonstrado que:

- contratos, strikes, estilos e vencimentos são obtidos diretamente da B3;
- preço/volume/OI possuem provenance;
- Bid/Ask EOD está disponível quando existe mercado;
- taxa por vencimento é derivada de DI1;
- IV/Greeks são reproduzíveis;
- Corporate Actions vêm de fonte oficial;
- nenhuma coluna crítica depende de scraping de concorrentes;
- existe uma payload estável capaz de alimentar o frontend.
