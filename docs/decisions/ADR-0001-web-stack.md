# ADR-0001 — Stack web de produção

**Status:** Aceito  
**Data:** 2026-09-24

## Contexto

O Proof of Data PETR4 está funcional e o protótipo read-only da Option Chain passou por QA visual desktop/mobile.

A aplicação web precisa atender simultaneamente:

- Option Chain altamente interativa;
- páginas públicas indexáveis;
- SEO programático por ativo/contrato;
- SSR/SSG para conteúdo público;
- áreas autenticadas no futuro;
- carteira e Strategy Builder;
- deploy self-hosted em Docker/Coolify;
- consumo de uma API de domínio independente do provider B3.

## Decisão

### Framework

**Next.js 16 App Router + React + TypeScript.**

A aplicação viverá em:

`apps/web`

O motor atual Python permanece independente em:

`src/bolsabr`

Não portar analytics para JavaScript.

## Motivos

### 1. Híbrido público + aplicação

BOLSABR precisa de dois modos no mesmo produto:

- páginas públicas de ativos/opções, adequadas para SEO;
- superfícies interativas e personalizadas, como carteira e Strategy Builder.

Next.js permite combinar renderização estática, server rendering e componentes interativos.

### 2. SEO programático

Rotas-alvo:

```text
/acoes/PETR4/opcoes
/opcoes/PETRJ510
/acoes/PETR4/volatilidade
/acoes/PETR4/dividendos
```

A Metadata API e o rendering server-side evitam depender de um shell SPA vazio para páginas públicas.

### 3. Self-host / Coolify

Deploy alvo inicial:

`Docker + Coolify`

Next.js suporta self-hosting em Node/Docker e `output: "standalone"`.

Não existe dependência arquitetural de Vercel.

### 4. Ecossistema e manutenção

Next.js 16 é uma linha estável/LTS em 2026 e possui amplo suporte de tooling, testes e agentes de código.

A versão deve acompanhar patches de segurança; nunca manter versão vulnerável apenas para preservar lockfile.

## Alternativas avaliadas

### React Router Framework Mode

**Viável e forte alternativa.**

Possui SSR e pre-rendering, com uma arquitetura Vite simples e portátil.

Não escolhido porque, para este produto, Next entrega mais convenções prontas para:

- SEO;
- metadata;
- páginas públicas;
- rendering híbrido;
- deploy standalone.

Se Next criar complexidade operacional real, React Router permanece plano B legítimo.

### TanStack Start

Não escolhido como framework principal neste momento porque a documentação atual ainda o classifica como Release Candidate.

Pode ser reavaliado após v1 estável.

### SPA pura

Rejeitada para produção.

O protótipo vanilla permanece como referência UX, mas uma SPA pura prejudica a estratégia de páginas públicas/SEO e empurra responsabilidades de rendering para o browser.

## Tabela / virtualização

### Decisão inicial

**Não adicionar TanStack Table ou virtualização no primeiro port.**

Motivos:

- a Option Chain possui geometria própria CALL | STRIKE | PUT;
- um vencimento PETR4 observado possui ~224 strikes;
- o default mostra ±10 strikes;
- normal rendering é mais simples e suficiente nesta escala.

### Quando adicionar

Introduzir TanStack Virtual apenas se profiling real mostrar problema em:

- modo "Todos";
- datasets significativamente maiores;
- scanners/rankings futuros.

Não otimizar antecipadamente.

## Styling

Inicialmente:

- CSS próprio;
- design tokens via CSS variables;
- sem UI kit genérico;
- sem copiar Profit/OpLab;
- componentes React específicos do domínio.

Objetivo: preservar a identidade visual validada no protótipo.

## Data boundary

O frontend consome exclusivamente o contrato:

`Option Chain API v0.1`

Nunca consome CSV/XML B3 diretamente.

Fluxo:

```text
B3/BCB/CVM
   ↓
Python ingestion + domain + analytics
   ↓
BOLSABR API / artifact versionado
   ↓
Next.js web
```

## Estratégia de dados da Fase 1

Durante a migração:

1. fixture real pequeno para desenvolvimento/testes;
2. adapter que aceita a payload v0.1;
3. posteriormente `BOLSABR_API_BASE_URL`;
4. EOD público pode ser cacheado/revalidado;
5. carteira futura será dinâmica/autenticada.

## Deployment

Primeira topologia:

```text
Coolify
├── bolsabr-web   (Next.js standalone)
└── bolsabr-api   (Python, etapa seguinte)
```

PostgreSQL/object storage entram conforme o roadmap.

## Testing

Web:

- TypeScript typecheck;
- `next build`;
- Playwright smoke/visual;
- testes de interação críticos.

Data:

- pytest;
- live smoke B3 separado.

Os workflows não devem fazer download B3 para mudanças apenas de frontend.

## Consequências

### Positivas

- SEO e app no mesmo framework;
- caminho claro para páginas de contratos;
- deploy compatível com infraestrutura atual;
- componentes interativos React;
- separação forte Python/Web.

### Custos

- runtime Node adicional;
- caching/rendering do App Router exige disciplina;
- atualizações de segurança precisam ser frequentes.

## Regra

A migração para Next deve reproduzir a UX validada antes de adicionar novas features.

Primeiro parity. Depois expansão.
