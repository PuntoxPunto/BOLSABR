const DATA_URL = "./petr4-option-chain-v0.json";

const leg = (
  ticker, type, exercise_style, pricing_model,
  last, bid, ask, spread_pct, quote_state, trade_count, volume, open_interest,
  iv, delta, gamma, theta, vega, rho, price, price_basis, quality_flags = []
) => ({
  ticker, type, exercise_style, pricing_model,
  market: {
    last, bid, ask, spread_pct, quote_state, quality_flags,
    trade_count, volume, financial_volume: null, open_interest
  },
  analytics_input: {
    price, price_basis, risk_free_rate: 0.12528941297980462
  },
  analytics: {
    intrinsic: null, extrinsic: null, iv, delta, gamma, theta, vega, rho
  }
});

const DEMO_DATA = {
  schema_version: "0.1",
  ref_date: "2026-09-23",
  market_data_source: "B3_EOD",
  rate_source: "B3_DI1",
  underlying: { ticker: "PETR4", spot: 49.60 },
  fallback_risk_free_rate: 0.1279532702962247,
  dividend_yield: 0,
  expirations: [
    { date: "2026-09-25", type: "WEEKLY", dte_calendar: 2, dte_business: 2, rows: [] },
    { date: "2026-10-02", type: "WEEKLY", dte_calendar: 9, dte_business: 7, rows: [] },
    {
      date: "2026-10-16",
      type: "MONTHLY",
      dte_calendar: 23,
      dte_business: 16,
      risk_free_rate: 0.12528941297980462,
      rows: [
        {
          strike: 48.86,
          call: leg("PETRJ500","CALL","AMERICAN","BSM_AMERICAN_CALL_NO_DIVIDEND",2.75,2.73,2.75,0.73,"TWO_SIDED",648,733900,1522600,0.43414,0.60444,0.07126,-0.05461,0.04796,0.01717,2.74,"MID"),
          put: leg("PETRV500","PUT","EUROPEAN","BSM_EUROPEAN",1.53,1.48,1.62,9.03,"TWO_SIDED",491,1562300,1677500,0.42042,-0.39358,0.07349,-0.03654,0.04789,-0.01328,1.55,"MID")
        },
        {
          strike: 49.36,
          call: leg("PETRJ21","CALL","AMERICAN","BSM_AMERICAN_CALL_NO_DIVIDEND",2.48,2.05,2.55,21.74,"TWO_SIDED",396,573900,874800,0.39930,0.57035,0.07899,-0.05137,0.04890,0.01638,2.30,"MID"),
          put: leg("PETRV21","PUT","EUROPEAN","BSM_EUROPEAN",1.70,1.00,1.70,51.85,"TWO_SIDED",304,627400,778700,0.33339,-0.42303,0.09431,-0.02766,0.04874,-0.01407,1.35,"MID",["WIDE_SPREAD_GT_30PCT"])
        },
        {
          strike: 49.61,
          call: leg("PETRJ22","CALL","EUROPEAN","BSM_EUROPEAN",2.35,2.01,2.40,17.69,"TWO_SIDED",380,505300,7756100,0.40623,0.55030,0.07825,-0.05213,0.04928,0.01581,2.205,"MID"),
          put: leg("PETRV22","PUT","EUROPEAN","BSM_EUROPEAN",1.85,1.79,2.50,33.10,"TWO_SIDED",326,533000,7551100,0.47119,-0.45058,0.06748,-0.04208,0.04929,-0.01543,2.145,"MID",["WIDE_SPREAD_GT_30PCT"])
        },
        {
          strike: 49.86,
          call: leg("PETRJ510","CALL","AMERICAN","BSM_AMERICAN_CALL_NO_DIVIDEND",2.22,2.14,2.27,5.90,"TWO_SIDED",518,778500,1190500,0.43127,0.53139,0.07406,-0.05472,0.04952,0.01522,2.205,"MID"),
          put: leg("PETRV510","PUT","EUROPEAN","BSM_EUROPEAN",2.14,1.90,2.15,12.35,"TWO_SIDED",496,874200,758200,0.42160,-0.46887,0.07577,-0.03671,0.04952,-0.01593,2.025,"MID")
        },
        {
          strike: 50.36,
          call: leg("PETRJ503","CALL","EUROPEAN","BSM_EUROPEAN",1.99,1.85,2.00,7.79,"TWO_SIDED",1994,1049500,2508100,0.42183,0.49358,0.07595,-0.05329,0.04967,0.01421,1.925,"MID"),
          put: leg("PETRV503","PUT","EUROPEAN","BSM_EUROPEAN",2.25,2.16,2.40,10.53,"TWO_SIDED",384,540100,1251100,0.42002,-0.50663,0.07628,-0.03594,0.04966,-0.01727,2.28,"MID")
        },
        {
          strike: 50.86,
          call: leg("PETRJ520","CALL","AMERICAN","BSM_AMERICAN_CALL_NO_DIVIDEND",1.82,1.71,1.82,6.23,"TWO_SIDED",796,1400600,4848200,0.43292,0.45864,0.07361,-0.05370,0.04940,0.01322,1.765,"MID"),
          put: leg("PETRV520","PUT","EUROPEAN","BSM_EUROPEAN",2.48,2.41,3.70,42.23,"TWO_SIDED",208,789600,1659600,0.51980,-0.52651,0.06151,-0.04599,0.04956,-0.01838,3.055,"MID",["WIDE_SPREAD_GT_30PCT"])
        },
        {
          strike: 51.36,
          call: leg("PETRJ531","CALL","AMERICAN","BSM_AMERICAN_CALL_NO_DIVIDEND",1.58,1.56,1.58,1.27,"TWO_SIDED",325,669500,1154300,0.43346,0.42329,0.07255,-0.05261,0.04875,0.01224,1.57,"MID"),
          put: leg("PETRV531","PUT","EUROPEAN","BSM_EUROPEAN",2.77,null,null,null,"LAST_ONLY",87,82400,306000,0.40136,-0.58603,0.07797,-0.03140,0.04851,-0.02006,2.77,"LAST",["LAST_ONLY"])
        }
      ]
    },
    { date: "2026-11-19", type: "MONTHLY", dte_calendar: 57, dte_business: 39, rows: [] }
  ]
};

const state = {
  data: null,
  expiryDate: null,
  preset: "basic",
  strikeWindow: 10,
  priceOnly: false,
  twoSidedOnly: false,
  hideWide: false,
  showAllExpiries: false,
  drawerLeg: null,
  drawerStrike: null,
  selected: new Map()
};

const $ = (selector) => document.querySelector(selector);

const formatMoney = (value) =>
  value == null ? "—" : value.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const formatCompact = (value) => {
  if (value == null) return "—";
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `${(value / 1_000_000).toLocaleString("pt-BR", { maximumFractionDigits: 2 })}M`;
  if (abs >= 1_000) return `${(value / 1_000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}k`;
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
};

const formatPct = (value, scale = 100) =>
  value == null ? "—" : `${(value * scale).toLocaleString("pt-BR", { maximumFractionDigits: 2 })}%`;

const formatSpread = (value) =>
  value == null ? "—" : `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;

const formatDelta = (value) =>
  value == null ? "—" : value.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const formatGreek = (value, digits = 4) =>
  value == null ? "—" : value.toLocaleString("pt-BR", { maximumFractionDigits: digits });

const expiryType = (expiry) => {
  if (expiry.type) return expiry.type;
  const ticker = expiry.rows
    ?.flatMap((row) => [row.call?.ticker, row.put?.ticker])
    .find(Boolean);
  return ticker && /W[1-5]$/.test(ticker) ? "WEEKLY" : "MONTHLY";
};

const twoSidedCount = (expiry) =>
  expiry.rows.reduce(
    (count, row) =>
      count +
      [row.call, row.put].filter((x) => x?.market?.quote_state === "TWO_SIDED").length,
    0
  );

const chooseDefaultExpiry = (data) => {
  const liquidMonthly = data.expirations.find(
    (expiry) => expiryType(expiry) === "MONTHLY" && twoSidedCount(expiry) >= 10
  );
  return liquidMonthly || data.expirations.find((expiry) => expiryType(expiry) === "MONTHLY") || data.expirations[0];
};

const currentExpiry = () =>
  state.data.expirations.find((expiry) => expiry.date === state.expiryDate) || state.data.expirations[0];

const getMetric = (legData, key) => {
  if (!legData) return null;
  const market = legData.market || {};
  const analytics = legData.analytics || {};
  const values = {
    ticker: legData.ticker,
    oi: market.open_interest,
    volume: market.volume,
    trades: market.trade_count,
    last: market.last,
    bid: market.bid,
    ask: market.ask,
    spread: market.spread_pct,
    iv: analytics.iv,
    delta: analytics.delta,
    gamma: analytics.gamma,
    theta: analytics.theta,
    vega: analytics.vega
  };
  return values[key];
};

const displayMetric = (key, value) => {
  if (key === "ticker") return value || "—";
  if (["bid", "ask", "last"].includes(key)) return formatMoney(value);
  if (["oi", "volume", "trades"].includes(key)) return formatCompact(value);
  if (key === "spread") return formatSpread(value);
  if (key === "iv") return formatPct(value);
  if (key === "delta") return formatDelta(value);
  if (["gamma", "theta", "vega"].includes(key)) return formatGreek(value);
  return value ?? "—";
};

const PRESETS = {
  basic: {
    call: [
      ["ticker", "Código"], ["oi", "OI"], ["volume", "Vol"], ["last", "Últ."], ["bid", "Bid"], ["ask", "Ask"]
    ],
    put: [
      ["bid", "Bid"], ["ask", "Ask"], ["last", "Últ."], ["volume", "Vol"], ["oi", "OI"], ["ticker", "Código"]
    ]
  },
  liquidity: {
    call: [
      ["ticker", "Código"], ["oi", "OI"], ["volume", "Vol"], ["trades", "Neg."], ["spread", "Spread"], ["bid", "Bid"], ["ask", "Ask"]
    ],
    put: [
      ["bid", "Bid"], ["ask", "Ask"], ["spread", "Spread"], ["trades", "Neg."], ["volume", "Vol"], ["oi", "OI"], ["ticker", "Código"]
    ]
  },
  greeks: {
    call: [
      ["ticker", "Código"], ["oi", "OI"], ["delta", "Delta"], ["iv", "IV"], ["bid", "Bid"], ["ask", "Ask"]
    ],
    put: [
      ["bid", "Bid"], ["ask", "Ask"], ["iv", "IV"], ["delta", "Delta"], ["oi", "OI"], ["ticker", "Código"]
    ]
  }
};

function loadData() {
  return fetch(DATA_URL, { cache: "no-store" })
    .then((response) => {
      if (!response.ok) throw new Error("fixture não encontrado");
      return response.json();
    })
    .catch(() => {
      console.info("BOLSABR prototype: usando fixture PETR4 embutida.");
      return DEMO_DATA;
    });
}

function renderHeader() {
  $("#spot").textContent = `R$ ${formatMoney(state.data.underlying.spot)}`;
  $("#freshness").textContent = `B3 · EOD ${formatDate(state.data.ref_date)}`;
}

function formatDate(iso) {
  if (!iso) return "—";
  const [year, month, day] = iso.split("-");
  return `${day}/${month}/${year}`;
}

function formatExpiryLabel(iso) {
  const d = new Date(`${iso}T12:00:00`);
  const month = d.toLocaleDateString("pt-BR", { month: "short" }).replace(".", "").toUpperCase();
  return `${String(d.getDate()).padStart(2, "0")} ${month}`;
}

function renderExpiries() {
  const strip = $("#expiry-strip");
  const expiries = state.showAllExpiries ? state.data.expirations : state.data.expirations.slice(0, 8);
  strip.innerHTML = expiries.map((expiry) => {
    const type = expiryType(expiry);
    const hasRows = expiry.rows?.length > 0;
    const active = expiry.date === state.expiryDate;
    const label = type === "MONTHLY" ? "M" : "S";
    return `
      <button
        class="expiry-chip ${active ? "active" : ""}"
        data-expiry="${expiry.date}"
        ${!hasRows && state.data === DEMO_DATA ? "disabled" : ""}
        title="${type === "MONTHLY" ? "Vencimento mensal" : "Vencimento semanal"}"
      >
        <span class="expiry-date">${formatExpiryLabel(expiry.date)}${active && type === "MONTHLY" ? " ★" : ""}</span>
        <span class="expiry-type">${label}</span>
        <span class="expiry-dte">${expiry.dte_calendar ?? "—"}d · ${expiry.dte_business ?? "—"} pregões</span>
      </button>
    `;
  }).join("");

  strip.querySelectorAll("[data-expiry]").forEach((button) => {
    button.addEventListener("click", () => {
      state.expiryDate = button.dataset.expiry;
      renderExpiries();
      renderChain();
    });
  });

  $("#all-expiries-btn").textContent = state.showAllExpiries ? "Menos" : "Todos";
}

function getVisibleRows(expiry) {
  let rows = [...(expiry.rows || [])].sort((a, b) => a.strike - b.strike);

  if (state.priceOnly) {
    rows = rows.filter((row) =>
      [row.call, row.put].some((x) => x && x.market?.quote_state !== "NO_PRICE")
    );
  }

  if (state.twoSidedOnly) {
    rows = rows.filter((row) =>
      [row.call, row.put].some((x) => x?.market?.quote_state === "TWO_SIDED")
    );
  }

  if (state.hideWide) {
    rows = rows.filter((row) =>
      [row.call, row.put].some((x) => x && !(x.market?.quality_flags || []).includes("WIDE_SPREAD_GT_30PCT"))
    );
  }

  if (state.strikeWindow < 999 && rows.length) {
    const spot = state.data.underlying.spot;
    let nearest = 0;
    rows.forEach((row, index) => {
      if (Math.abs(row.strike - spot) < Math.abs(rows[nearest].strike - spot)) nearest = index;
    });
    const start = Math.max(0, nearest - state.strikeWindow);
    const end = Math.min(rows.length, nearest + state.strikeWindow + 1);
    rows = rows.slice(start, end);
  }

  return rows;
}

function renderChainHead() {
  const config = PRESETS[state.preset];
  const callHeaders = config.call.map(([, label]) => `<th>${label}</th>`).join("");
  const putHeaders = config.put.map(([, label]) => `<th>${label}</th>`).join("");

  $("#chain-head").innerHTML = `
    <tr>
      <th class="group-head" colspan="${config.call.length}">CALLS</th>
      <th class="group-head strike-head" rowspan="2">Strike</th>
      <th class="group-head" colspan="${config.put.length}">PUTS</th>
    </tr>
    <tr>
      ${callHeaders}
      ${putHeaders}
    </tr>
  `;
}

function qualityClass(legData) {
  if (!legData) return "no-price";
  const stateName = legData.market?.quote_state;
  if (stateName === "NO_PRICE") return "no-price";
  if (stateName !== "TWO_SIDED") return "quality-muted";
  return "";
}

function metricCell(legData, key, strike, expiry) {
  const value = getMetric(legData, key);
  const flags = legData?.market?.quality_flags || [];
  const wide = flags.includes("WIDE_SPREAD_GT_30PCT") && ["spread", "bid", "ask", "iv"].includes(key);
  const ticker = key === "ticker" ? " ticker-cell" : "";
  return `
    <td
      class="metric-cell option-side ${qualityClass(legData)}${ticker} ${wide ? "wide-spread" : ""}"
      data-ticker="${legData?.ticker || ""}"
      data-strike="${strike}"
      data-expiry="${expiry.date}"
      title="${legData ? tooltipForLeg(legData) : "Sem contrato"}"
    >${displayMetric(key, value)}</td>
  `;
}

function tooltipForLeg(legData) {
  const basis = legData.analytics_input?.price_basis || "—";
  const qs = legData.market?.quote_state || "—";
  return `${legData.ticker} · ${qs} · IV via ${basis}`;
}

function renderChain() {
  const expiry = currentExpiry();
  const rows = getVisibleRows(expiry);
  const config = PRESETS[state.preset];
  const totalColumns = config.call.length + config.put.length + 1;
  const spot = state.data.underlying.spot;

  renderChainHead();

  $("#expiry-meta").textContent =
    `${formatExpiryLabel(expiry.date)} · ${expiryType(expiry) === "MONTHLY" ? "mensal" : "semanal"} · ` +
    `${expiry.dte_calendar ?? "—"} dias · ${expiry.dte_business ?? "—"} pregões · ` +
    `taxa DI1 ${formatPct(expiry.risk_free_rate ?? state.data.fallback_risk_free_rate)}`;

  const body = $("#chain-body");

  if (!rows.length) {
    body.innerHTML = `<tr><td class="empty-state" colspan="${totalColumns}">Sem linhas neste fixture. Use o JSON live para navegar este vencimento.</td></tr>`;
    return;
  }

  let html = "";
  let spotInserted = false;

  rows.forEach((row) => {
    if (!spotInserted && row.strike >= spot) {
      html += `
        <tr class="spot-row">
          <td colspan="${totalColumns}" class="spot-row-cell">
            <span><i></i>PETR4 · R$ ${formatMoney(spot)}</span>
          </td>
        </tr>
      `;
      spotInserted = true;
    }

    const callCells = config.call.map(([key]) => metricCell(row.call, key, row.strike, expiry)).join("");
    const putCells = config.put.map(([key]) => metricCell(row.put, key, row.strike, expiry)).join("");

    html += `
      <tr>
        ${callCells}
        <td class="strike-cell">${formatMoney(row.strike)}</td>
        ${putCells}
      </tr>
    `;
  });

  if (!spotInserted) {
    html += `
      <tr class="spot-row">
        <td colspan="${totalColumns}" class="spot-row-cell">
          <span><i></i>PETR4 · R$ ${formatMoney(spot)}</span>
        </td>
      </tr>
    `;
  }

  body.innerHTML = html;

  body.querySelectorAll("[data-ticker]").forEach((cell) => {
    if (!cell.dataset.ticker) return;
    cell.addEventListener("click", () => {
      const row = expiry.rows.find((r) => Number(r.strike) === Number(cell.dataset.strike));
      const selectedLeg = [row?.call, row?.put].find((x) => x?.ticker === cell.dataset.ticker);
      if (selectedLeg) openDrawer(selectedLeg, row.strike, expiry);
    });
  });
}

function detailRows(items) {
  return `
    <dl class="detail-grid">
      ${items.map(([label, value]) => `<dt>${label}</dt><dd>${value}</dd>`).join("")}
    </dl>
  `;
}

function openDrawer(legData, strike, expiry) {
  state.drawerLeg = legData;
  state.drawerStrike = strike;

  $("#drawer-type").textContent =
    `${legData.type} · ${legData.exercise_style} · strike R$ ${formatMoney(strike)}`;
  $("#drawer-ticker").textContent = legData.ticker;

  const market = legData.market || {};
  const analytics = legData.analytics || {};
  const input = legData.analytics_input || {};
  const flags = market.quality_flags || [];

  $("#drawer-content").innerHTML = `
    <section class="detail-section">
      <h3>Mercado</h3>
      ${detailRows([
        ["Vencimento", formatDate(expiry.date)],
        ["Bid", `R$ ${formatMoney(market.bid)}`],
        ["Ask", `R$ ${formatMoney(market.ask)}`],
        ["Último", `R$ ${formatMoney(market.last)}`],
        ["Spread", formatSpread(market.spread_pct)],
        ["Negócios", formatCompact(market.trade_count)],
        ["Volume", formatCompact(market.volume)],
        ["OI", formatCompact(market.open_interest)]
      ])}
    </section>

    <section class="detail-section">
      <h3>Analytics</h3>
      ${detailRows([
        ["IV", formatPct(analytics.iv)],
        ["Delta", formatDelta(analytics.delta)],
        ["Gamma", formatGreek(analytics.gamma)],
        ["Theta/dia", formatGreek(analytics.theta)],
        ["Vega", formatGreek(analytics.vega)],
        ["Intrínseco", `R$ ${formatMoney(analytics.intrinsic)}`],
        ["Extrínseco", `R$ ${formatMoney(analytics.extrinsic)}`]
      ])}
    </section>

    <section class="detail-section">
      <h3>Cálculo auditável</h3>
      ${detailRows([
        ["Preço usado", `R$ ${formatMoney(input.price)}`],
        ["Base", input.price_basis || "—"],
        ["Taxa DI1", formatPct(input.risk_free_rate)],
        ["Modelo", legData.pricing_model || "—"],
        ["Quote state", market.quote_state || "—"]
      ])}
      <div class="quality-list">
        ${flags.length ? flags.map((flag) => `<span class="quality-pill">${flag}</span>`).join("") : '<span class="quality-pill">SEM FLAGS</span>'}
      </div>
    </section>
  `;

  $("#select-leg").textContent =
    state.selected.has(legData.ticker) ? "Remover da estratégia" : "Selecionar para estratégia";

  $("#drawer").classList.add("open");
  $("#drawer").setAttribute("aria-hidden", "false");
  $("#scrim").classList.add("open");
}

function closeDrawer() {
  $("#drawer").classList.remove("open");
  $("#drawer").setAttribute("aria-hidden", "true");
  $("#scrim").classList.remove("open");
}

function updateSelectionBar() {
  const entries = [...state.selected.values()];
  const bar = $("#selection-bar");
  bar.hidden = entries.length === 0;

  if (!entries.length) return;

  $("#selection-count").textContent =
    `${entries.length} ${entries.length === 1 ? "contrato selecionado" : "contratos selecionados"}`;
  $("#selection-labels").textContent = entries.map((x) => x.ticker).join(" · ");
}

function bindControls() {
  document.querySelectorAll(".preset").forEach((button) => {
    button.addEventListener("click", () => {
      state.preset = button.dataset.preset;
      document.querySelectorAll(".preset").forEach((x) => x.classList.toggle("active", x === button));
      renderChain();
    });
  });

  $("#strike-window").addEventListener("change", (event) => {
    state.strikeWindow = Number(event.target.value);
    renderChain();
  });

  $("#price-only").addEventListener("change", (event) => {
    state.priceOnly = event.target.checked;
    renderChain();
  });

  $("#two-sided-only").addEventListener("change", (event) => {
    state.twoSidedOnly = event.target.checked;
    renderChain();
  });

  $("#hide-wide").addEventListener("change", (event) => {
    state.hideWide = event.target.checked;
    renderChain();
  });

  $("#all-expiries-btn").addEventListener("click", () => {
    state.showAllExpiries = !state.showAllExpiries;
    renderExpiries();
  });

  $("#drawer-close").addEventListener("click", closeDrawer);
  $("#scrim").addEventListener("click", closeDrawer);
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeDrawer();
  });

  $("#select-leg").addEventListener("click", () => {
    const option = state.drawerLeg;
    if (!option) return;
    if (state.selected.has(option.ticker)) state.selected.delete(option.ticker);
    else state.selected.set(option.ticker, option);

    $("#select-leg").textContent =
      state.selected.has(option.ticker) ? "Remover da estratégia" : "Selecionar para estratégia";
    updateSelectionBar();
  });

  $("#clear-selection").addEventListener("click", () => {
    state.selected.clear();
    updateSelectionBar();
  });

  $("#asset-search").addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    const value = event.currentTarget.value.trim().toUpperCase();
    if (value !== "PETR4") {
      event.currentTarget.value = "PETR4";
      event.currentTarget.select();
    }
  });
}

async function init() {
  state.data = await loadData();
  const defaultExpiry = chooseDefaultExpiry(state.data);
  state.expiryDate = defaultExpiry.date;

  renderHeader();
  renderExpiries();
  renderChain();
  bindControls();
}

init();
