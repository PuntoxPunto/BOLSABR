"use client";

import {
  type FormEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type {
  AssetSummary,
  ExpirationChain,
  OptionChainPayload,
  OptionLeg,
  StrikeRow,
} from "@/lib/option-chain-types";

type PresetName = "basic" | "liquidity" | "greeks";
type MetricKey =
  | "ticker"
  | "oi"
  | "volume"
  | "trades"
  | "last"
  | "bid"
  | "ask"
  | "spread"
  | "iv"
  | "delta";

const PRESETS: Record<
  PresetName,
  { call: Array<[MetricKey, string]>; put: Array<[MetricKey, string]> }
> = {
  basic: {
    call: [
      ["ticker", "Código"],
      ["oi", "OI"],
      ["volume", "Vol"],
      ["last", "Últ."],
      ["bid", "Bid"],
      ["ask", "Ask"],
    ],
    put: [
      ["bid", "Bid"],
      ["ask", "Ask"],
      ["last", "Últ."],
      ["volume", "Vol"],
      ["oi", "OI"],
      ["ticker", "Código"],
    ],
  },
  liquidity: {
    call: [
      ["ticker", "Código"],
      ["oi", "OI"],
      ["volume", "Vol"],
      ["trades", "Neg."],
      ["spread", "Spread"],
      ["bid", "Bid"],
      ["ask", "Ask"],
    ],
    put: [
      ["bid", "Bid"],
      ["ask", "Ask"],
      ["spread", "Spread"],
      ["trades", "Neg."],
      ["volume", "Vol"],
      ["oi", "OI"],
      ["ticker", "Código"],
    ],
  },
  greeks: {
    call: [
      ["ticker", "Código"],
      ["oi", "OI"],
      ["delta", "Delta"],
      ["iv", "IV"],
      ["bid", "Bid"],
      ["ask", "Ask"],
    ],
    put: [
      ["bid", "Bid"],
      ["ask", "Ask"],
      ["iv", "IV"],
      ["delta", "Delta"],
      ["oi", "OI"],
      ["ticker", "Código"],
    ],
  },
};

function formatMoney(value: number | null | undefined) {
  return value == null
    ? "—"
    : value.toLocaleString("pt-BR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
}

function formatCompact(value: number | null | undefined) {
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

function formatPct(value: number | null | undefined, scale = 100) {
  return value == null
    ? "—"
    : `${(value * scale).toLocaleString("pt-BR", {
        maximumFractionDigits: 2,
      })}%`;
}

function formatSpread(value: number | null | undefined) {
  return value == null
    ? "—"
    : `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
}

function formatDelta(value: number | null | undefined) {
  return value == null
    ? "—"
    : value.toLocaleString("pt-BR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
}

function formatGreek(value: number | null | undefined, digits = 4) {
  return value == null
    ? "—"
    : value.toLocaleString("pt-BR", { maximumFractionDigits: digits });
}

function formatDate(iso: string) {
  const [year, month, day] = iso.split("-");
  return `${day}/${month}/${year}`;
}

function formatExpiryLabel(iso: string) {
  const value = new Date(`${iso}T12:00:00`);
  const month = value
    .toLocaleDateString("pt-BR", { month: "short" })
    .replace(".", "")
    .toUpperCase();
  return `${String(value.getDate()).padStart(2, "0")} ${month}`;
}

function twoSidedCount(expiry: ExpirationChain) {
  return expiry.rows.reduce(
    (count, row) =>
      count +
      [row.call, row.put].filter(
        (leg) => leg?.market.quote_state === "TWO_SIDED",
      ).length,
    0,
  );
}

function chooseDefaultExpiry(data: OptionChainPayload) {
  return (
    data.expirations.find(
      (expiry) =>
        expiry.type === "MONTHLY" && twoSidedCount(expiry) >= 10,
    ) ??
    data.expirations.find((expiry) => expiry.type === "MONTHLY") ??
    data.expirations[0]
  );
}

function qualityClass(leg: OptionLeg | null) {
  if (!leg || leg.market.quote_state === "NO_PRICE") return "no-price";
  if (leg.market.quote_state !== "TWO_SIDED") return "quality-muted";
  return "";
}

function metricValue(leg: OptionLeg | null, key: MetricKey) {
  if (!leg) return null;
  const market = leg.market;
  const analytics = leg.analytics;
  switch (key) {
    case "ticker":
      return leg.ticker;
    case "oi":
      return market.open_interest;
    case "volume":
      return market.volume;
    case "trades":
      return market.trade_count;
    case "last":
      return market.last;
    case "bid":
      return market.bid;
    case "ask":
      return market.ask;
    case "spread":
      return market.spread_pct;
    case "iv":
      return analytics.iv;
    case "delta":
      return analytics.delta;
  }
}

function displayMetric(key: MetricKey, value: string | number | null) {
  if (key === "ticker") return typeof value === "string" ? value : "—";
  const numeric = typeof value === "number" ? value : null;
  if (["bid", "ask", "last"].includes(key)) return formatMoney(numeric);
  if (["oi", "volume", "trades"].includes(key)) return formatCompact(numeric);
  if (key === "spread") return formatSpread(numeric);
  if (key === "iv") return formatPct(numeric);
  if (key === "delta") return formatDelta(numeric);
  return "—";
}

interface MetricCellProps {
  leg: OptionLeg | null;
  metric: MetricKey;
  onOpen: () => void;
}

function MetricCell({ leg, metric, onOpen }: MetricCellProps) {
  const value = metricValue(leg, metric);
  const wide =
    leg?.market.quality_flags.includes("WIDE_SPREAD_GT_30PCT") &&
    ["spread", "bid", "ask", "iv"].includes(metric);

  return (
    <td
      className={[
        "metric-cell",
        "option-side",
        qualityClass(leg),
        metric === "ticker" ? "ticker-cell" : "",
        wide ? "wide-spread" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {leg ? (
        <button
          className="cell-button"
          type="button"
          onClick={onOpen}
          title={`${leg.ticker} · ${leg.market.quote_state} · IV via ${leg.analytics_input.price_basis ?? "—"}`}
        >
          {displayMetric(metric, value)}
        </button>
      ) : (
        "—"
      )}
    </td>
  );
}

interface DrawerProps {
  leg: OptionLeg | null;
  strike: number | null;
  expiry: ExpirationChain;
  selected: boolean;
  onClose: () => void;
  onToggleSelection: () => void;
}

function DetailRows({
  items,
}: {
  items: Array<[string, string]>;
}) {
  return (
    <dl className="detail-grid">
      {items.map(([label, value]) => (
        <div className="detail-row" key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function OptionDrawer({
  leg,
  strike,
  expiry,
  selected,
  onClose,
  onToggleSelection,
}: DrawerProps) {
  const open = Boolean(leg && strike != null);
  return (
    <>
      <aside className={`drawer ${open ? "open" : ""}`} aria-hidden={!open}>
        {leg && strike != null ? (
          <>
            <div className="drawer-head">
              <div>
                <div className="eyebrow">
                  {leg.type} · {leg.exercise_style} · strike R$ {formatMoney(strike)}
                </div>
                <h2>{leg.ticker}</h2>
              </div>
              <button
                className="icon-btn"
                type="button"
                onClick={onClose}
                aria-label="Fechar detalhes"
              >
                ×
              </button>
            </div>

            <section className="detail-section">
              <h3>Mercado</h3>
              <DetailRows
                items={[
                  ["Vencimento", formatDate(expiry.date)],
                  ["Bid", `R$ ${formatMoney(leg.market.bid)}`],
                  ["Ask", `R$ ${formatMoney(leg.market.ask)}`],
                  ["Último", `R$ ${formatMoney(leg.market.last)}`],
                  ["Spread", formatSpread(leg.market.spread_pct)],
                  ["Negócios", formatCompact(leg.market.trade_count)],
                  ["Volume", formatCompact(leg.market.volume)],
                  ["OI", formatCompact(leg.market.open_interest)],
                ]}
              />
            </section>

            <section className="detail-section">
              <h3>Analytics</h3>
              <DetailRows
                items={[
                  ["IV", formatPct(leg.analytics.iv)],
                  ["Delta", formatDelta(leg.analytics.delta)],
                  ["Gamma", formatGreek(leg.analytics.gamma)],
                  ["Theta/dia", formatGreek(leg.analytics.theta)],
                  ["Vega", formatGreek(leg.analytics.vega)],
                  ["Intrínseco", `R$ ${formatMoney(leg.analytics.intrinsic)}`],
                  ["Extrínseco", `R$ ${formatMoney(leg.analytics.extrinsic)}`],
                ]}
              />
            </section>

            <section className="detail-section">
              <h3>Cálculo auditável</h3>
              <DetailRows
                items={[
                  ["Preço usado", `R$ ${formatMoney(leg.analytics_input.price)}`],
                  ["Base", leg.analytics_input.price_basis ?? "—"],
                  ["Taxa DI1", formatPct(leg.analytics_input.risk_free_rate)],
                  ["Modelo", leg.pricing_model ?? "—"],
                  ["Quote state", leg.market.quote_state],
                ]}
              />
              <div className="quality-list">
                {leg.market.quality_flags.length ? (
                  leg.market.quality_flags.map((flag) => (
                    <span className="quality-pill" key={flag}>
                      {flag}
                    </span>
                  ))
                ) : (
                  <span className="quality-pill">SEM FLAGS</span>
                )}
              </div>
            </section>

            <button
              className="select-leg"
              type="button"
              onClick={onToggleSelection}
            >
              {selected ? "Remover da estratégia" : "Selecionar para estratégia"}
            </button>

            <Link
              className="contract-page-link"
              href={`/opcoes/${leg.ticker}`}
            >
              Ver página do contrato
            </Link>
          </>
        ) : null}
      </aside>
      <button
        className={`scrim ${open ? "open" : ""}`}
        type="button"
        aria-label="Fechar detalhes"
        onClick={onClose}
      />
    </>
  );
}

export default function OptionChainClient({
  data,
  assets,
}: {
  data: OptionChainPayload;
  assets: AssetSummary[];
}) {
  const router = useRouter();
  const searchInputRef = useRef<HTMLInputElement>(null);
  const initialExpiry = chooseDefaultExpiry(data);
  const [searchTerm, setSearchTerm] = useState(data.underlying.ticker);
  const [searchOpen, setSearchOpen] = useState(false);
  const [expiryDate, setExpiryDate] = useState(initialExpiry.date);
  const [preset, setPreset] = useState<PresetName>("basic");
  const [strikeWindow, setStrikeWindow] = useState(10);
  const [priceOnly, setPriceOnly] = useState(false);
  const [twoSidedOnly, setTwoSidedOnly] = useState(false);
  const [hideWide, setHideWide] = useState(false);
  const [showAllExpiries, setShowAllExpiries] = useState(false);
  const [mobileSide, setMobileSide] = useState<"CALL" | "PUT">("CALL");
  const [drawer, setDrawer] = useState<{
    leg: OptionLeg;
    strike: number;
  } | null>(null);
  const [selected, setSelected] = useState<string[]>([]);

  const assetSuggestions = useMemo(() => {
    const query = searchTerm.trim().toUpperCase();
    const filtered = query
      ? assets.filter((asset) => asset.ticker.includes(query))
      : assets;
    return filtered.slice(0, 6);
  }, [assets, searchTerm]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        searchInputRef.current?.focus();
        searchInputRef.current?.select();
        setSearchOpen(true);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const expiry =
    data.expirations.find((item) => item.date === expiryDate) ??
    data.expirations[0];

  const rows = useMemo(() => {
    let visible = [...expiry.rows].sort((a, b) => a.strike - b.strike);

    if (priceOnly) {
      visible = visible.filter((row) =>
        [row.call, row.put].some(
          (leg) => leg && leg.market.quote_state !== "NO_PRICE",
        ),
      );
    }

    if (twoSidedOnly) {
      visible = visible.filter((row) =>
        [row.call, row.put].some(
          (leg) => leg?.market.quote_state === "TWO_SIDED",
        ),
      );
    }

    if (hideWide) {
      visible = visible.filter((row) =>
        [row.call, row.put].some(
          (leg) =>
            leg &&
            !leg.market.quality_flags.includes("WIDE_SPREAD_GT_30PCT"),
        ),
      );
    }

    if (strikeWindow < 999 && visible.length) {
      const nearest = visible.reduce(
        (best, row, index) =>
          Math.abs(row.strike - data.underlying.spot) <
          Math.abs(visible[best].strike - data.underlying.spot)
            ? index
            : best,
        0,
      );
      const start = Math.max(0, nearest - strikeWindow);
      const end = Math.min(visible.length, nearest + strikeWindow + 1);
      visible = visible.slice(start, end);
    }

    return visible;
  }, [
    expiry.rows,
    priceOnly,
    twoSidedOnly,
    hideWide,
    strikeWindow,
    data.underlying.spot,
  ]);

  const expiryChoices = showAllExpiries
    ? data.expirations
    : data.expirations.slice(0, 8);

  const config = PRESETS[preset];
  const totalColumns = config.call.length + config.put.length + 1;
  const spot = data.underlying.spot;

  function openLeg(leg: OptionLeg | null, strike: number) {
    if (leg) setDrawer({ leg, strike });
  }

  function toggleSelected(ticker: string) {
    setSelected((current) =>
      current.includes(ticker)
        ? current.filter((item) => item !== ticker)
        : [...current, ticker],
    );
  }

  function navigateToAsset(ticker: string) {
    const normalized = ticker.trim().toUpperCase();
    if (!assets.some((asset) => asset.ticker === normalized)) return;
    setSearchOpen(false);
    setSearchTerm(normalized);
    router.push(`/acoes/${encodeURIComponent(normalized)}/opcoes`);
  }

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = searchTerm.trim().toUpperCase();
    const exact = assets.find((asset) => asset.ticker === normalized);
    const target = exact ?? assetSuggestions[0];
    if (target) navigateToAsset(target.ticker);
  }

  return (
    <>
      <div className="app-shell">
        <header className="topbar">
          <div className="brand">
            BOLSA<span>BR</span>
          </div>
          <div className="search-wrap">
            <form className="search" onSubmit={submitSearch}>
              <label className="sr-only" htmlFor="asset-search">
                Buscar ativo publicado
              </label>
              <input
                id="asset-search"
                ref={searchInputRef}
                value={searchTerm}
                onChange={(event) => {
                  setSearchTerm(event.target.value.toUpperCase());
                  setSearchOpen(true);
                }}
                onFocus={() => setSearchOpen(true)}
                onBlur={() => {
                  window.setTimeout(() => setSearchOpen(false), 120);
                }}
                autoComplete="off"
                aria-label="Buscar ativo publicado"
                aria-expanded={searchOpen}
              />
              <kbd>⌘K</kbd>
            </form>
            {searchOpen ? (
              <div className="asset-suggestions" role="listbox">
                {assetSuggestions.length ? (
                  assetSuggestions.map((asset) => (
                    <button
                      type="button"
                      className="asset-suggestion"
                      key={asset.ticker}
                      onMouseDown={(event) => event.preventDefault()}
                      onClick={() => navigateToAsset(asset.ticker)}
                    >
                      <strong>{asset.ticker}</strong>
                      <span>
                        {asset.spot == null ? "—" : `R$ ${formatMoney(asset.spot)}`}
                      </span>
                      <small>
                        {formatDate(asset.ref_date)} · {asset.expiration_count} venc.
                      </small>
                    </button>
                  ))
                ) : (
                  <div className="asset-suggestion-empty">
                    Nenhum snapshot publicado
                  </div>
                )}
              </div>
            ) : null}
          </div>
          <div className="freshness">
            B3 · EOD {formatDate(data.ref_date)}
          </div>
        </header>

        <main>
          <section className="asset-header">
            <div>
              <div className="eyebrow">Ativo · B3</div>
              <div className="asset-title-row">
                <h1>{data.underlying.ticker}</h1>
                <span className="asset-name">Option Chain EOD</span>
              </div>
            </div>
            <div className="spot-block">
              <div className="spot">R$ {formatMoney(spot)}</div>
              <div className="spot-label">fechamento B3</div>
            </div>
          </section>

          <nav className="asset-tabs" aria-label="Seções do ativo">
            <button type="button" className="tab active">
              Opções
            </button>
            <button type="button" className="tab" disabled>
              Volatilidade
            </button>
            <button type="button" className="tab" disabled>
              Dividendos
            </button>
            <button type="button" className="tab" disabled>
              Eventos
            </button>
          </nav>

          <section className="expiry-section" aria-labelledby="expiry-heading">
            <div className="section-heading">
              <div>
                <div className="eyebrow" id="expiry-heading">
                  Vencimentos
                </div>
                <div className="section-caption">
                  Mensal líquido selecionado por padrão
                </div>
              </div>
              <button
                className="ghost-btn"
                type="button"
                onClick={() => setShowAllExpiries((value) => !value)}
              >
                {showAllExpiries ? "Menos" : "Todos"}
              </button>
            </div>

            <div className="expiry-strip">
              {expiryChoices.map((item) => {
                const active = item.date === expiry.date;
                return (
                  <button
                    className={`expiry-chip ${active ? "active" : ""}`}
                    type="button"
                    key={item.date}
                    onClick={() => setExpiryDate(item.date)}
                    disabled={item.rows.length === 0}
                    title={
                      item.type === "MONTHLY"
                        ? "Vencimento mensal"
                        : "Vencimento semanal"
                    }
                  >
                    <span className="expiry-date">
                      {formatExpiryLabel(item.date)}
                      {active && item.type === "MONTHLY" ? " ★" : ""}
                    </span>
                    <span className="expiry-type">
                      {item.type === "MONTHLY" ? "M" : "S"}
                    </span>
                    <span className="expiry-dte">
                      {item.dte_calendar}d · {item.dte_business ?? "—"} pregões
                    </span>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="chain-panel">
            <div className="toolbar">
              <div className="preset-group" aria-label="Preset de colunas">
                {(["basic", "liquidity", "greeks"] as PresetName[]).map(
                  (name) => (
                    <button
                      className={`preset ${preset === name ? "active" : ""}`}
                      type="button"
                      key={name}
                      onClick={() => setPreset(name)}
                    >
                      {name === "basic"
                        ? "Básico"
                        : name === "liquidity"
                          ? "Liquidez"
                          : "Greeks"}
                    </button>
                  ),
                )}
              </div>

              <div className="toolbar-controls">
                <label>
                  <span>Strikes</span>
                  <select
                    value={strikeWindow}
                    onChange={(event) =>
                      setStrikeWindow(Number(event.target.value))
                    }
                  >
                    <option value={5}>±5</option>
                    <option value={10}>±10</option>
                    <option value={20}>±20</option>
                    <option value={999}>Todos</option>
                  </select>
                </label>

                <label className="check">
                  <input
                    type="checkbox"
                    checked={priceOnly}
                    onChange={(event) => setPriceOnly(event.target.checked)}
                  />
                  <span>Só com preço</span>
                </label>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={twoSidedOnly}
                    onChange={(event) => setTwoSidedOnly(event.target.checked)}
                  />
                  <span>Mercado bilateral</span>
                </label>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={hideWide}
                    onChange={(event) => setHideWide(event.target.checked)}
                  />
                  <span>Ocultar spread &gt;30%</span>
                </label>
              </div>
            </div>

            <div className="chain-meta">
              <div>
                {formatExpiryLabel(expiry.date)} ·{" "}
                {expiry.type === "MONTHLY" ? "mensal" : "semanal"} ·{" "}
                {expiry.dte_calendar} dias · {expiry.dte_business ?? "—"} pregões
                · taxa DI1 {formatPct(expiry.risk_free_rate)}
              </div>
              <div className="legend">
                <span>
                  <i className="quality-dot good" /> Bilateral
                </span>
                <span>
                  <i className="quality-dot muted" /> Qualidade reduzida
                </span>
              </div>
            </div>

            <div className="mobile-side-switch" aria-label="Lado da cadeia">
              {(["CALL", "PUT"] as const).map((side) => (
                <button
                  type="button"
                  className={`mobile-side ${mobileSide === side ? "active" : ""}`}
                  key={side}
                  onClick={() => setMobileSide(side)}
                >
                  {side}
                </button>
              ))}
            </div>

            <div className="mobile-chain">
              {rows.map((row, index) => {
                const previous = rows[index - 1];
                const showSpot =
                  row.strike >= spot &&
                  (!previous || previous.strike < spot);
                const leg = mobileSide === "CALL" ? row.call : row.put;
                return (
                  <div key={`${row.strike}-mobile`}>
                    {showSpot ? (
                      <div className="mobile-spot-marker">
                        <i /> {data.underlying.ticker} · R$ {formatMoney(spot)}
                      </div>
                    ) : null}
                    {leg ? (
                      <button
                        className={`mobile-option-card ${qualityClass(leg)}`}
                        type="button"
                        onClick={() => openLeg(leg, row.strike)}
                      >
                        <div className="mobile-option-head">
                          <span className="mobile-strike">
                            Strike R$ {formatMoney(row.strike)}
                          </span>
                          <span className="mobile-ticker">{leg.ticker}</span>
                        </div>
                        <div className="mobile-option-grid">
                          <div className="mobile-metric">
                            <span>Bid</span>
                            <strong>{formatMoney(leg.market.bid)}</strong>
                          </div>
                          <div className="mobile-metric">
                            <span>Ask</span>
                            <strong>{formatMoney(leg.market.ask)}</strong>
                          </div>
                          <div className="mobile-metric">
                            <span>Últ.</span>
                            <strong>{formatMoney(leg.market.last)}</strong>
                          </div>
                          <div className="mobile-metric">
                            <span>IV</span>
                            <strong>{formatPct(leg.analytics.iv)}</strong>
                          </div>
                          <div className="mobile-metric">
                            <span>Delta</span>
                            <strong>{formatDelta(leg.analytics.delta)}</strong>
                          </div>
                          <div className="mobile-metric">
                            <span>OI</span>
                            <strong>{formatCompact(leg.market.open_interest)}</strong>
                          </div>
                        </div>
                        <div className="mobile-quality">
                          <span>{leg.market.quote_state}</span>
                          <span>
                            spread {formatSpread(leg.market.spread_pct)}
                          </span>
                          <span>
                            {leg.market.quality_flags.includes(
                              "WIDE_SPREAD_GT_30PCT",
                            )
                              ? "spread largo"
                              : (leg.analytics_input.price_basis ?? "—")}
                          </span>
                        </div>
                      </button>
                    ) : null}
                  </div>
                );
              })}
            </div>

            <div className="table-wrap">
              <table className="chain-table">
                <thead>
                  <tr>
                    <th className="group-head" colSpan={config.call.length}>
                      CALLS
                    </th>
                    <th className="group-head strike-head" rowSpan={2}>
                      Strike
                    </th>
                    <th className="group-head" colSpan={config.put.length}>
                      PUTS
                    </th>
                  </tr>
                  <tr>
                    {config.call.map(([, label]) => (
                      <th key={`call-${label}`}>{label}</th>
                    ))}
                    {config.put.map(([, label]) => (
                      <th key={`put-${label}`}>{label}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.length ? (
                    rows.map((row, index) => {
                      const previous = rows[index - 1];
                      const showSpot =
                        row.strike >= spot &&
                        (!previous || previous.strike < spot);
                      return (
                        <FragmentRow
                          key={row.strike}
                          row={row}
                          showSpot={showSpot}
                          spot={spot}
                          totalColumns={totalColumns}
                          config={config}
                          onOpen={openLeg}
                          underlyingTicker={data.underlying.ticker}
                        />
                      );
                    })
                  ) : (
                    <tr>
                      <td className="empty-state" colSpan={totalColumns}>
                        Sem contratos neste vencimento.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </main>
      </div>

      <OptionDrawer
        leg={drawer?.leg ?? null}
        strike={drawer?.strike ?? null}
        expiry={expiry}
        selected={drawer ? selected.includes(drawer.leg.ticker) : false}
        onClose={() => setDrawer(null)}
        onToggleSelection={() => {
          if (drawer) toggleSelected(drawer.leg.ticker);
        }}
      />

      {selected.length ? (
        <div className="selection-bar">
          <div>
            <strong>
              {selected.length}{" "}
              {selected.length === 1
                ? "contrato selecionado"
                : "contratos selecionados"}
            </strong>
            <span>{selected.join(" · ")}</span>
          </div>
          <div className="selection-actions">
            <button
              className="ghost-btn"
              type="button"
              onClick={() => setSelected([])}
            >
              Limpar
            </button>
            <button className="primary-btn" type="button" disabled>
              Analisar estratégia · próximo módulo
            </button>
          </div>
        </div>
      ) : null}
    </>
  );
}

function FragmentRow({
  row,
  showSpot,
  spot,
  totalColumns,
  config,
  onOpen,
  underlyingTicker,
}: {
  row: StrikeRow;
  showSpot: boolean;
  spot: number;
  totalColumns: number;
  config: (typeof PRESETS)[PresetName];
  onOpen: (leg: OptionLeg | null, strike: number) => void;
  underlyingTicker: string;
}) {
  return (
    <>
      {showSpot ? (
        <tr className="spot-row">
          <td colSpan={totalColumns} className="spot-row-cell">
            <span>
              <i /> {underlyingTicker} · R$ {formatMoney(spot)}
            </span>
          </td>
        </tr>
      ) : null}
      <tr>
        {config.call.map(([metric, label]) => (
          <MetricCell
            key={`call-${label}`}
            leg={row.call}
            metric={metric}
            onOpen={() => onOpen(row.call, row.strike)}
          />
        ))}
        <td className="strike-cell">{formatMoney(row.strike)}</td>
        {config.put.map(([metric, label]) => (
          <MetricCell
            key={`put-${label}`}
            leg={row.put}
            metric={metric}
            onOpen={() => onOpen(row.put, row.strike)}
          />
        ))}
      </tr>
    </>
  );
}
