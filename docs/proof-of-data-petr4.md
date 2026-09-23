# Fase 0 — Proof of Data PETR4

## Objetivo

Produzir uma Option Chain EOD de PETR4 a partir de fontes primárias da B3 e cálculos próprios, mantendo provenance e inputs reproduzíveis.

## Fontes oficiais confirmadas

### 1. InstrumentsConsolidated
Uso:
- ticker da opção (`TckrSymb`)
- vencimento (`XprtnDt`)
- tipo (`OptnTp`)
- strike (`ExrcPric`)
- estilo de exercício (`OptnStyle`)
- underlying (`UndrlygTckrSymb1`)
- multiplicador (`CtrctMltplr`)
- ISIN

O glossário B3 informa que o arquivo de cadastro de instrumentos listados é publicado em CSV antes da abertura e após o encerramento do pregão.

### 2. TradeInformationConsolidated
Uso:
- mínima (`MinPric`)
- máxima (`MaxPric`)
- média (`TradAvrgPric`)
- último (`LastPric`)
- número de negócios (`TradQty`)
- quantidade (`FinInstrmQty`)
- volume financeiro (`NtlFinVol`)

O arquivo é consolidado por ativo e publicado à noite.

### 3. DerivativesOpenPosition
Uso:
- open interest (`OpnIntrst`)
- variação do OI (`VartnOpnIntrst`)
- quantidade coberta (`CvrdQty`)
- quantidade descoberta (`UcvrdQty`)
- posição total (`TtlPos`)

É publicado diariamente após o pregão em CSV.

### 4. COTAHIST
Uso complementar:
- melhor oferta de compra EOD (`PREOFC`)
- melhor oferta de venda EOD (`PREOFV`)
- último negócio (`PREULT`)
- número de negócios (`TOTNEG`)
- quantidade negociada (`QUATOT`)
- volume financeiro (`VOLTOT`)
- strike (`PREEXE`)
- vencimento (`DATVEN`)

O layout oficial da B3 define registros fixos de 245 bytes. O parser inicial está em `bolsabr.b3.cotahist`.

**Decisão:** para o Free EOD, COTAHIST é candidato a complementar a chain com Bid/Ask de fechamento. Precisamos validar empiricamente cobertura e freshness para as séries atuais antes de torná-lo obrigatório.

### 5. BCB SGS 11 — Selic diária
Uso:
- fallback explícito de taxa livre de risco durante o Proof of Data.

O BCB publica a série 11 diariamente em percentual ao dia. O módulo `bolsabr.bcb.sgs` converte essa taxa para uma taxa anual contínua plana.

**Importante:** esta é uma aproximação da Fase 0. Para comparação fina de IV/Greeks por vencimento, a direção correta é usar uma curva por prazo, preferencialmente DI1/BDI.

## Download B3

O portal público de arquivos da B3 expõe um fluxo de download em duas etapas observado no portal atual:

1. solicitar token para o nome da tabela e data;
2. baixar o CSV usando o token.

A implementação inicial fica encapsulada em `bolsabr.b3.client`, para que possamos trocar o mecanismo de transporte sem afetar o domínio se a B3 alterar o portal.

## Regra de freshness

- Nunca substituir um snapshot `Final` por um snapshot `Parcial`.
- Cada registro normalizado deve carregar a data de referência.
- O futuro storage deve guardar também horário de ingestão, origem e hash do arquivo bruto.
- A UI deverá mostrar `ref_date`/freshness explicitamente.

## Join inicial

Chave principal entre os três datasets diários:

`TckrSymb`

Fluxo:

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
          +------> COTAHIST (enriquecimento EOD Bid/Ask)
```

Para PETR4, a seleção primária das opções deve usar `UndrlygTckrSymb1 == PETR4` e confirmar que o segmento/tipo corresponde a opções de ações.

## Schema de saída v0

```json
{
  "ref_date": "2026-09-22",
  "underlying": {
    "ticker": "PETR4",
    "last": 0.0
  },
  "expirations": [
    {
      "date": "2026-10-16",
      "days": 0,
      "rows": [
        {
          "strike": 0.0,
          "call": {
            "ticker": "...",
            "last": 0.0,
            "bid": 0.0,
            "ask": 0.0,
            "volume": 0,
            "oi": 0,
            "iv": 0.0,
            "delta": 0.0,
            "gamma": 0.0,
            "theta": 0.0,
            "vega": 0.0
          },
          "put": {}
        }
      ]
    }
  ]
}
```

## Cálculos v0

### Europeias
Black-Scholes-Merton.

### Americanas
CRR binomial inicialmente.

### IV
Bisseção robusta sobre o mesmo modelo utilizado para precificar o contrato.

### Greeks
- forma fechada BSM para europeias;
- diferenças finitas sobre CRR para americanas no Proof of Data.

## Inputs que devem acompanhar cada cálculo

- spot
- strike
- preço observado da opção
- vencimento / tempo
- taxa usada
- hipótese de dividend yield ou fluxo de dividendos
- modelo
- quantidade de passos (CRR)
- timestamp / ref_date

Sem esses inputs, IV e Greeks não são auditáveis.

## Questões ainda abertas antes de declarar o Proof como concluído

1. Substituir o fallback Selic plana por curva DI1 por vencimento.
2. Definir tratamento de dividendos discretos para opções americanas.
3. Validar empiricamente Bid/Ask COTAHIST nas séries PETR4 atuais.
4. Confirmar em um snapshot real PETR4 os valores/domínios de `OptnTp` e `OptnStyle`.
5. Comparar IV/Greeks contra Profit e OpLab com os mesmos inputs e convenções.

## Critério de conclusão

O Proof de PETR4 só fecha quando:
- contratos, strikes e vencimentos baterem com B3;
- preços/volume/OI possuírem provenance;
- IV/Greeks forem reproduzíveis;
- divergências contra benchmarks estiverem documentadas;
- nenhuma coluna crítica depender de scraping de concorrentes.
