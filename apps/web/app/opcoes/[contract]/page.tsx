import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import HistoryCharts from "@/components/option-history/HistoryCharts";
import {
  getOptionContract,
  getOptionContractHistory,
} from "@/lib/option-chain";
import { getSiteUrl } from "@/lib/site";

type PageProps = {
  params: Promise<{ contract: string }>;
};

function money(value: number | null | undefined) {
  return value == null
    ? "—"
    : value.toLocaleString("pt-BR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
}

function pct(value: number | null | undefined, scale = 100) {
  return value == null
    ? "—"
    : `${(value * scale).toLocaleString("pt-BR", {
        maximumFractionDigits: 2,
      })}%`;
}

function compact(value: number | null | undefined) {
  if (value == null) return "—";
  const abs = Math.abs(value);
  if (abs >= 1_000_000) {
    return `${(value / 1_000_000).toLocaleString("pt-BR", {
      maximumFractionDigits: 2,
    })}M`;
  }
  if (abs >= 1_000) {
    return `${(value / 1_000).toLocaleString("pt-BR", {
      maximumFractionDigits: 1,
    })}k`;
  }
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
}

function decimal(value: number | null | undefined, digits = 4) {
  return value == null
    ? "—"
    : value.toLocaleString("pt-BR", { maximumFractionDigits: digits });
}

function datePt(iso: string) {
  const [year, month, day] = iso.split("-");
  return `${day}/${month}/${year}`;
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { contract } = await params;
  const data = await getOptionContract(contract);

  if (!data) {
    return {
      title: "Opção não encontrada",
      robots: { index: false, follow: false },
    };
  }

  const c = data.contract;
  const title = `${c.ticker} — ${c.type} ${data.underlying.ticker} strike R$ ${money(c.strike)}`;
  const description =
    `${c.ticker}: ${c.type} de ${data.underlying.ticker}, strike R$ ${money(c.strike)}, ` +
    `vencimento ${datePt(c.expiration)}. Bid/Ask, volume, OI, IV e Greeks no fechamento B3.`;

  const url = new URL(
    `/opcoes/${encodeURIComponent(c.ticker)}`,
    getSiteUrl(),
  ).toString();

  return {
    title,
    description,
    alternates: {
      canonical: url,
    },
    openGraph: {
      type: "website",
      title,
      description,
      url,
    },
  };
}

export default async function OptionContractPage({ params }: PageProps) {
  const { contract } = await params;
  const [data, history] = await Promise.all([
    getOptionContract(contract),
    getOptionContractHistory(contract),
  ]);

  if (!data) {
    notFound();
  }

  const c = data.contract;
  const m = c.market;
  const a = c.analytics;
  const input = c.analytics_input;

  const breadcrumbJsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      {
        "@type": "ListItem",
        position: 1,
        name: "BOLSABR",
        item: getSiteUrl().toString(),
      },
      {
        "@type": "ListItem",
        position: 2,
        name: data.underlying.ticker,
        item: new URL(
          `/acoes/${data.underlying.ticker}/opcoes`,
          getSiteUrl(),
        ).toString(),
      },
      {
        "@type": "ListItem",
        position: 3,
        name: c.ticker,
        item: new URL(`/opcoes/${c.ticker}`, getSiteUrl()).toString(),
      },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(breadcrumbJsonLd).replace(/</g, "\\u003c"),
        }}
      />

      <div className="contract-page">
        <header className="contract-topbar">
          <Link className="brand contract-brand" href="/">
            BOLSA<span>BR</span>
          </Link>
          <div className="freshness">
            B3 · EOD {datePt(data.ref_date)}
          </div>
        </header>

        <main>
          <nav className="breadcrumbs" aria-label="Breadcrumb">
            <Link href="/">BOLSABR</Link>
            <span>/</span>
            <Link href={`/acoes/${data.underlying.ticker}/opcoes`}>
              {data.underlying.ticker}
            </Link>
            <span>/</span>
            <span aria-current="page">{c.ticker}</span>
          </nav>

          <section className="contract-hero">
            <div>
              <div className="eyebrow">
                {c.type} · {c.exercise_style} ·{" "}
                {c.expiration_type === "MONTHLY" ? "Mensal" : "Semanal"}
              </div>
              <h1>{c.ticker}</h1>
              <p>
                Opção de {data.underlying.ticker} com strike de R 
                {money(c.strike)} e vencimento em {datePt(c.expiration)}.
              </p>
            </div>

            <div className="contract-underlying-card">
              <span>Underlying</span>
              <Link href={`/acoes/${data.underlying.ticker}/opcoes`}>
                {data.underlying.ticker}
              </Link>
              <strong>R$ {money(data.underlying.spot)}</strong>
              <small>fechamento B3</small>
            </div>
          </section>

          <section className="contract-summary-grid" aria-label="Resumo da opção">
            <article className="summary-card">
              <span>Último</span>
              <strong>R$ {money(m.last)}</strong>
              <small>{m.quote_state}</small>
            </article>
            <article className="summary-card">
              <span>Bid</span>
              <strong>R$ {money(m.bid)}</strong>
              <small>spread {m.spread_pct == null ? "—" : `${decimal(m.spread_pct, 2)}%`}</small>
            </article>
            <article className="summary-card">
              <span>Ask</span>
              <strong>R$ {money(m.ask)}</strong>
              <small>{m.trade_count == null ? "—" : `${compact(m.trade_count)} negócios`}</small>
            </article>
            <article className="summary-card">
              <span>IV</span>
              <strong>{pct(a.iv)}</strong>
              <small>via {input.price_basis ?? "—"}</small>
            </article>
          </section>

          <div className="contract-columns">
            <section className="contract-panel">
              <div className="contract-panel-head">
                <div>
                  <div className="eyebrow">Mercado</div>
                  <h2>Cotação e liquidez</h2>
                </div>
              </div>
              <dl className="contract-metrics">
                <div><dt>Bid</dt><dd>R$ {money(m.bid)}</dd></div>
                <div><dt>Ask</dt><dd>R$ {money(m.ask)}</dd></div>
                <div><dt>Último</dt><dd>R$ {money(m.last)}</dd></div>
                <div><dt>Spread</dt><dd>{m.spread_pct == null ? "—" : `${decimal(m.spread_pct, 2)}%`}</dd></div>
                <div><dt>Volume</dt><dd>{compact(m.volume)}</dd></div>
                <div><dt>Open Interest</dt><dd>{compact(m.open_interest)}</dd></div>
                <div><dt>Negócios</dt><dd>{compact(m.trade_count)}</dd></div>
                <div><dt>Quote state</dt><dd>{m.quote_state}</dd></div>
              </dl>
              <div className="quality-list contract-quality">
                {m.quality_flags.length ? (
                  m.quality_flags.map((flag) => (
                    <span className="quality-pill" key={flag}>{flag}</span>
                  ))
                ) : (
                  <span className="quality-pill">SEM FLAGS DE QUALIDADE</span>
                )}
              </div>
            </section>

            <section className="contract-panel">
              <div className="contract-panel-head">
                <div>
                  <div className="eyebrow">Analytics</div>
                  <h2>Volatilidade e Greeks</h2>
                </div>
              </div>
              <dl className="contract-metrics">
                <div><dt>IV</dt><dd>{pct(a.iv)}</dd></div>
                <div><dt>Delta</dt><dd>{decimal(a.delta)}</dd></div>
                <div><dt>Gamma</dt><dd>{decimal(a.gamma)}</dd></div>
                <div><dt>Theta/dia</dt><dd>{decimal(a.theta)}</dd></div>
                <div><dt>Vega</dt><dd>{decimal(a.vega)}</dd></div>
                <div><dt>Rho</dt><dd>{decimal(a.rho)}</dd></div>
                <div><dt>Intrínseco</dt><dd>R$ {money(a.intrinsic)}</dd></div>
                <div><dt>Extrínseco</dt><dd>R$ {money(a.extrinsic)}</dd></div>
              </dl>
            </section>
          </div>

          <section className="contract-panel contract-pricing-panel">
            <div className="contract-panel-head">
              <div>
                <div className="eyebrow">Cálculo auditável</div>
                <h2>Como esta leitura foi calculada</h2>
              </div>
            </div>

            <dl className="contract-metrics contract-metrics-wide">
              <div><dt>Preço usado</dt><dd>R$ {money(input.price)}</dd></div>
              <div><dt>Base</dt><dd>{input.price_basis ?? "—"}</dd></div>
              <div><dt>Taxa</dt><dd>{pct(input.risk_free_rate)}</dd></div>
              <div><dt>Fonte taxa</dt><dd>{data.rate_source}</dd></div>
              <div><dt>Modelo</dt><dd>{c.pricing_model ?? "—"}</dd></div>
              <div><dt>DTE corridos</dt><dd>{c.dte_calendar}</dd></div>
              <div><dt>DTE pregões</dt><dd>{c.dte_business ?? "—"}</dd></div>
              <div><dt>Fonte mercado</dt><dd>{data.market_data_source}</dd></div>
            </dl>
          </section>

          <HistoryCharts history={history} />

          <section className="contract-context">
            <h2>Sobre {c.ticker}</h2>
            <p>
              {c.ticker} é uma opção {c.type === "CALL" ? "de compra" : "de venda"} sobre{" "}
              <Link href={`/acoes/${data.underlying.ticker}/opcoes`}>
                {data.underlying.ticker}
              </Link>
              , com strike de R$ {money(c.strike)} e vencimento em{" "}
              {datePt(c.expiration)}. Os dados de mercado exibidos correspondem ao
              snapshot EOD de {datePt(data.ref_date)}. IV e Greeks são métricas
              calculadas pelo BOLSABR a partir dos inputs explicitados acima.
            </p>
            <p>
              Contratos com book unilateral, último negócio isolado ou spread
              elevado podem ter menor qualidade analítica. O estado da cotação e
              os flags permanecem visíveis para não transformar ausência de
              liquidez em falsa precisão.
            </p>

            <Link
              className="contract-primary-link"
              href={`/acoes/${data.underlying.ticker}/opcoes`}
            >
              Ver Option Chain completa de {data.underlying.ticker}
            </Link>
          </section>
        </main>
      </div>
    </>
  );
}
