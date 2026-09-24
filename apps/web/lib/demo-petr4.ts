import type { OptionChainPayload, OptionLeg, OptionType, QuoteState } from "./option-chain-types";

function leg(
  ticker: string,
  type: OptionType,
  exerciseStyle: string,
  pricingModel: string,
  last: number | null,
  bid: number | null,
  ask: number | null,
  spreadPct: number | null,
  quoteState: QuoteState,
  tradeCount: number | null,
  volume: number | null,
  openInterest: number | null,
  iv: number | null,
  delta: number | null,
  gamma: number | null,
  theta: number | null,
  vega: number | null,
  rho: number | null,
  price: number | null,
  priceBasis: "MID" | "LAST" | null,
  qualityFlags: string[] = [],
): OptionLeg {
  return {
    ticker,
    type,
    exercise_style: exerciseStyle,
    pricing_model: pricingModel,
    market: {
      last,
      bid,
      ask,
      spread_pct: spreadPct,
      quote_state: quoteState,
      quality_flags: qualityFlags,
      trade_count: tradeCount,
      volume,
      financial_volume: null,
      open_interest: openInterest,
    },
    analytics_input: {
      price,
      price_basis: priceBasis,
      risk_free_rate: 0.12528941297980462,
    },
    analytics: {
      intrinsic: null,
      extrinsic: null,
      iv,
      delta,
      gamma,
      theta,
      vega,
      rho,
    },
  };
}

export const demoPetr4: OptionChainPayload = {
  schema_version: "0.1",
  ref_date: "2026-09-23",
  market_data_source: "B3_EOD",
  rate_source: "B3_DI1",
  underlying: { ticker: "PETR4", spot: 49.6 },
  fallback_risk_free_rate: 0.1279532702962247,
  dividend_yield: 0,
  expirations: [
    { date: "2026-09-25", type: "WEEKLY", dte_calendar: 2, dte_business: 2, risk_free_rate: 0.126, rows: [] },
    { date: "2026-10-02", type: "WEEKLY", dte_calendar: 9, dte_business: 7, risk_free_rate: 0.1258, rows: [] },
    {
      date: "2026-10-16",
      type: "MONTHLY",
      dte_calendar: 23,
      dte_business: 16,
      risk_free_rate: 0.12528941297980462,
      rows: [
        {
          strike: 48.86,
          call: leg("PETRJ500", "CALL", "AMERICAN", "BSM_AMERICAN_CALL_NO_DIVIDEND", 2.75, 2.73, 2.75, 0.73, "TWO_SIDED", 648, 733900, 1522600, 0.43414, 0.60444, 0.07126, -0.05461, 0.04796, 0.01717, 2.74, "MID"),
          put: leg("PETRV500", "PUT", "EUROPEAN", "BSM_EUROPEAN", 1.53, 1.48, 1.62, 9.03, "TWO_SIDED", 491, 1562300, 1677500, 0.42042, -0.39358, 0.07349, -0.03654, 0.04789, -0.01328, 1.55, "MID"),
        },
        {
          strike: 49.36,
          call: leg("PETRJ21", "CALL", "AMERICAN", "BSM_AMERICAN_CALL_NO_DIVIDEND", 2.48, 2.05, 2.55, 21.74, "TWO_SIDED", 396, 573900, 874800, 0.3993, 0.57035, 0.07899, -0.05137, 0.0489, 0.01638, 2.3, "MID"),
          put: leg("PETRV21", "PUT", "EUROPEAN", "BSM_EUROPEAN", 1.7, 1.0, 1.7, 51.85, "TWO_SIDED", 304, 627400, 778700, 0.33339, -0.42303, 0.09431, -0.02766, 0.04874, -0.01407, 1.35, "MID", ["WIDE_SPREAD_GT_30PCT"]),
        },
        {
          strike: 49.61,
          call: leg("PETRJ22", "CALL", "EUROPEAN", "BSM_EUROPEAN", 2.35, 2.01, 2.4, 17.69, "TWO_SIDED", 380, 505300, 7756100, 0.40623, 0.5503, 0.07825, -0.05213, 0.04928, 0.01581, 2.205, "MID"),
          put: leg("PETRV22", "PUT", "EUROPEAN", "BSM_EUROPEAN", 1.85, 1.79, 2.5, 33.1, "TWO_SIDED", 326, 533000, 7551100, 0.47119, -0.45058, 0.06748, -0.04208, 0.04929, -0.01543, 2.145, "MID", ["WIDE_SPREAD_GT_30PCT"]),
        },
        {
          strike: 49.86,
          call: leg("PETRJ510", "CALL", "AMERICAN", "BSM_AMERICAN_CALL_NO_DIVIDEND", 2.22, 2.14, 2.27, 5.9, "TWO_SIDED", 518, 778500, 1190500, 0.43127, 0.53139, 0.07406, -0.05472, 0.04952, 0.01522, 2.205, "MID"),
          put: leg("PETRV510", "PUT", "EUROPEAN", "BSM_EUROPEAN", 2.14, 1.9, 2.15, 12.35, "TWO_SIDED", 496, 874200, 758200, 0.4216, -0.46887, 0.07577, -0.03671, 0.04952, -0.01593, 2.025, "MID"),
        },
        {
          strike: 50.36,
          call: leg("PETRJ503", "CALL", "EUROPEAN", "BSM_EUROPEAN", 1.99, 1.85, 2.0, 7.79, "TWO_SIDED", 1994, 1049500, 2508100, 0.42183, 0.49358, 0.07595, -0.05329, 0.04967, 0.01421, 1.925, "MID"),
          put: leg("PETRV503", "PUT", "EUROPEAN", "BSM_EUROPEAN", 2.25, 2.16, 2.4, 10.53, "TWO_SIDED", 384, 540100, 1251100, 0.42002, -0.50663, 0.07628, -0.03594, 0.04966, -0.01727, 2.28, "MID"),
        },
        {
          strike: 50.86,
          call: leg("PETRJ520", "CALL", "AMERICAN", "BSM_AMERICAN_CALL_NO_DIVIDEND", 1.82, 1.71, 1.82, 6.23, "TWO_SIDED", 796, 1400600, 4848200, 0.43292, 0.45864, 0.07361, -0.0537, 0.0494, 0.01322, 1.765, "MID"),
          put: leg("PETRV520", "PUT", "EUROPEAN", "BSM_EUROPEAN", 2.48, 2.41, 3.7, 42.23, "TWO_SIDED", 208, 789600, 1659600, 0.5198, -0.52651, 0.06151, -0.04599, 0.04956, -0.01838, 3.055, "MID", ["WIDE_SPREAD_GT_30PCT"]),
        },
        {
          strike: 51.36,
          call: leg("PETRJ531", "CALL", "AMERICAN", "BSM_AMERICAN_CALL_NO_DIVIDEND", 1.58, 1.56, 1.58, 1.27, "TWO_SIDED", 325, 669500, 1154300, 0.43346, 0.42329, 0.07255, -0.05261, 0.04875, 0.01224, 1.57, "MID"),
          put: leg("PETRV531", "PUT", "EUROPEAN", "BSM_EUROPEAN", 2.77, null, null, null, "LAST_ONLY", 87, 82400, 306000, 0.40136, -0.58603, 0.07797, -0.0314, 0.04851, -0.02006, 2.77, "LAST", ["LAST_ONLY"]),
        },
      ],
    },
    { date: "2026-11-19", type: "MONTHLY", dte_calendar: 57, dte_business: 39, risk_free_rate: 0.1238, rows: [] },
  ],
};
