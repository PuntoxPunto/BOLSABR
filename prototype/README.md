# BOLSABR — Prototype Option Chain

Protótipo sem dependências para validar a UX da Fase 1 antes de escolher a stack de produção.

## O que valida

- layout CALL | STRIKE | PUT;
- vencimento mensal líquido como default;
- chips WEEKLY/MONTHLY;
- janela de strikes ao redor do ATM;
- presets Básico / Liquidez / Greeks;
- filtros de qualidade;
- quote_state e spread;
- drawer auditável por contrato;
- seleção de legs para o futuro Strategy Builder.

## Dados

O app tenta carregar:

`./petr4-option-chain-v0.json`

Esse arquivo é gerado pelo workflow da Fase 0 e não deve ser versionado no Git.

Se ele não existir, o protótipo usa um fixture embutido com dados reais do snapshot PETR4 de 23/09/2026.

## Executar localmente

### Com fixture embutido

A partir da raiz:

```bash
python -m http.server 8080 -d prototype
```

Abrir:

`http://localhost:8080`

### Com a chain completa

1. Executar o pipeline:

```bash
python scripts/b3_smoke.py
```

2. Copiar o artifact:

```bash
cp artifacts/petr4-option-chain-v0.json prototype/petr4-option-chain-v0.json
```

3. Servir:

```bash
python -m http.server 8080 -d prototype
```

O JSON completo é ignorado pelo Git.

## Arquivos

- `index.html`
- `styles.css`
- `app.js`

## Decisão de arquitetura

Este protótipo NÃO define a stack de produção.

Depois da validação visual/interacional decidiremos entre uma arquitetura SSR/SSG adequada a:

- SEO programático;
- páginas públicas de ativos/contratos;
- autenticação/carteira;
- endpoints de market data;
- Strategy Builder;
- alertas.

## Fonte de verdade

Contrato de dados:

`docs/api-option-chain-v0.md`

Wireframe:

`docs/wireframes/option-chain.md`
