export type OptionType = "CALL" | "PUT";
export type QuoteState = "TWO_SIDED" | "ONE_SIDED" | "LAST_ONLY" | "NO_PRICE";
export type ExpirationType = "WEEKLY" | "MONTHLY";

export interface OptionMarket {
  last: number | null;
  bid: number | null;
  ask: number | null;
  spread_pct: number | null;
  quote_state: QuoteState;
  quality_flags: string[];
  trade_count: number | null;
  volume: number | null;
  financial_volume: number | null;
  open_interest: number | null;
}

export interface OptionAnalyticsInput {
  price: number | null;
  price_basis: "MID" | "LAST" | null;
  risk_free_rate: number;
}

export interface OptionAnalytics {
  intrinsic: number | null;
  extrinsic: number | null;
  iv: number | null;
  delta: number | null;
  gamma: number | null;
  theta: number | null;
  vega: number | null;
  rho: number | null;
}

export interface OptionLeg {
  ticker: string;
  type: OptionType;
  exercise_style: string;
  pricing_model: string | null;
  market: OptionMarket;
  analytics_input: OptionAnalyticsInput;
  analytics: OptionAnalytics;
}

export interface StrikeRow {
  strike: number;
  call: OptionLeg | null;
  put: OptionLeg | null;
}

export interface ExpirationChain {
  date: string;
  type: ExpirationType;
  dte_calendar: number;
  dte_business: number | null;
  risk_free_rate: number;
  rows: StrikeRow[];
}

export interface OptionChainPayload {
  schema_version: "0.1";
  ref_date: string;
  market_data_source: string;
  rate_source: string;
  underlying: {
    ticker: string;
    spot: number;
  };
  fallback_risk_free_rate: number;
  dividend_yield: number;
  expirations: ExpirationChain[];
}


export interface AssetSummary {
  ticker: string;
  ref_date: string;
  spot: number | null;
  expiration_count: number;
  market_data_source: string | null;
}

export interface AssetCatalogPayload {
  assets: AssetSummary[];
}


export interface OptionContractDetailPayload {
  schema_version: "0.1";
  ref_date: string;
  market_data_source: string;
  rate_source: string;
  underlying: {
    ticker: string;
    spot: number;
  };
  contract: {
    ticker: string;
    type: OptionType;
    exercise_style: string;
    pricing_model: string | null;
    strike: number;
    expiration: string;
    expiration_type: ExpirationType;
    dte_calendar: number;
    dte_business: number | null;
    market: OptionMarket;
    analytics_input: OptionAnalyticsInput;
    analytics: OptionAnalytics;
  };
}

export interface OptionContractSummary {
  ticker: string;
  underlying: string;
  ref_date: string;
  expiration: string;
  expiration_type: ExpirationType;
  strike: number;
  type: OptionType;
  exercise_style: string;
  quote_state: QuoteState;
  last: number | null;
  bid: number | null;
  ask: number | null;
  open_interest: number | null;
  volume: number | null;
  iv: number | null;
}

export interface OptionContractCatalogPayload {
  contracts: OptionContractSummary[];
  offset: number;
  limit: number;
  total: number;
  next_offset: number | null;
}
