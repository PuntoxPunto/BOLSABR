import { demoPetr4 } from "./demo-petr4";
import type {
  AssetCatalogPayload,
  AssetSummary,
  OptionChainPayload,
  OptionContractCatalogPayload,
  OptionContractDetailPayload,
  OptionHistoryPayload,
} from "./option-chain-types";

const SCHEMA_VERSION = "0.1";

function isOptionChainPayload(value: unknown): value is OptionChainPayload {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<OptionChainPayload>;
  return (
    candidate.schema_version === SCHEMA_VERSION &&
    typeof candidate.ref_date === "string" &&
    typeof candidate.underlying?.ticker === "string" &&
    typeof candidate.underlying?.spot === "number" &&
    Array.isArray(candidate.expirations)
  );
}

export async function getOptionChain(ticker: string): Promise<OptionChainPayload | null> {
  const normalized = ticker.trim().toUpperCase();
  const baseUrl = process.env.BOLSABR_API_BASE_URL?.replace(/\/$/, "");

  if (baseUrl) {
    const response = await fetch(
      `${baseUrl}/v1/assets/${encodeURIComponent(normalized)}/options`,
      { next: { revalidate: 300 } },
    );

    if (response.ok) {
      const payload: unknown = await response.json();
      if (!isOptionChainPayload(payload)) {
        throw new Error("BOLSABR API returned an incompatible Option Chain payload");
      }
      return payload;
    }

    if (response.status === 404) {
      return null;
    }

    throw new Error(`BOLSABR API failed with status ${response.status}`);
  }

  if (normalized === "PETR4") {
    return demoPetr4;
  }

  return null;
}


function isAssetCatalogPayload(value: unknown): value is AssetCatalogPayload {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<AssetCatalogPayload>;
  return Array.isArray(candidate.assets);
}

export async function getAssetCatalog(
  query = "",
): Promise<AssetSummary[]> {
  const baseUrl = process.env.BOLSABR_API_BASE_URL?.replace(/\/$/, "");
  const normalizedQuery = query.trim().toUpperCase();

  if (baseUrl) {
    const params = new URLSearchParams();
    if (normalizedQuery) params.set("q", normalizedQuery);
    params.set("limit", "50");

    const response = await fetch(
      `${baseUrl}/v1/assets?${params.toString()}`,
      { next: { revalidate: 300 } },
    );
    if (!response.ok) {
      throw new Error(`BOLSABR asset catalog failed with status ${response.status}`);
    }

    const payload: unknown = await response.json();
    if (!isAssetCatalogPayload(payload)) {
      throw new Error("BOLSABR API returned an incompatible asset catalog");
    }
    return payload.assets;
  }

  const fallback: AssetSummary[] = [
    {
      ticker: demoPetr4.underlying.ticker,
      ref_date: demoPetr4.ref_date,
      spot: demoPetr4.underlying.spot,
      expiration_count: demoPetr4.expirations.length,
      market_data_source: demoPetr4.market_data_source,
    },
  ];

  if (!normalizedQuery) return fallback;
  return fallback.filter((asset) => asset.ticker.includes(normalizedQuery));
}


function findDemoContract(contract: string): OptionContractDetailPayload | null {
  const wanted = contract.trim().toUpperCase();

  for (const expiration of demoPetr4.expirations) {
    for (const row of expiration.rows) {
      for (const leg of [row.call, row.put]) {
        if (!leg || leg.ticker !== wanted) continue;

        return {
          schema_version: "0.1",
          ref_date: demoPetr4.ref_date,
          market_data_source: demoPetr4.market_data_source,
          rate_source: demoPetr4.rate_source,
          underlying: demoPetr4.underlying,
          contract: {
            ticker: leg.ticker,
            type: leg.type,
            exercise_style: leg.exercise_style,
            pricing_model: leg.pricing_model,
            strike: row.strike,
            expiration: expiration.date,
            expiration_type: expiration.type,
            dte_calendar: expiration.dte_calendar,
            dte_business: expiration.dte_business,
            market: leg.market,
            analytics_input: leg.analytics_input,
            analytics: leg.analytics,
          },
        };
      }
    }
  }

  return null;
}

function isOptionContractDetailPayload(
  value: unknown,
): value is OptionContractDetailPayload {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<OptionContractDetailPayload>;
  return (
    candidate.schema_version === "0.1" &&
    typeof candidate.ref_date === "string" &&
    typeof candidate.underlying?.ticker === "string" &&
    typeof candidate.contract?.ticker === "string"
  );
}

export async function getOptionContract(
  contract: string,
): Promise<OptionContractDetailPayload | null> {
  const normalized = contract.trim().toUpperCase();
  const baseUrl = process.env.BOLSABR_API_BASE_URL?.replace(/\/$/, "");

  if (baseUrl) {
    const response = await fetch(
      `${baseUrl}/v1/options/${encodeURIComponent(normalized)}`,
      { next: { revalidate: 300 } },
    );

    if (response.status === 404) return null;
    if (!response.ok) {
      throw new Error(
        `BOLSABR option contract failed with status ${response.status}`,
      );
    }

    const payload: unknown = await response.json();
    if (!isOptionContractDetailPayload(payload)) {
      throw new Error("BOLSABR API returned incompatible option contract detail");
    }
    return payload;
  }

  return findDemoContract(normalized);
}

export async function getOptionContractCatalog(
  {
    underlying,
    query,
    offset = 0,
    limit = 500,
  }: {
    underlying?: string;
    query?: string;
    offset?: number;
    limit?: number;
  } = {},
): Promise<OptionContractCatalogPayload> {
  const baseUrl = process.env.BOLSABR_API_BASE_URL?.replace(/\/$/, "");

  if (baseUrl) {
    const params = new URLSearchParams({
      offset: String(offset),
      limit: String(limit),
    });
    if (underlying) params.set("underlying", underlying.trim().toUpperCase());
    if (query) params.set("q", query.trim().toUpperCase());

    const response = await fetch(
      `${baseUrl}/v1/options?${params.toString()}`,
      { next: { revalidate: 300 } },
    );
    if (!response.ok) {
      throw new Error(
        `BOLSABR option catalog failed with status ${response.status}`,
      );
    }

    return (await response.json()) as OptionContractCatalogPayload;
  }

  const contracts = demoPetr4.expirations.flatMap((expiration) =>
    expiration.rows.flatMap((row) =>
      [row.call, row.put]
        .filter((leg): leg is NonNullable<typeof leg> => Boolean(leg))
        .map((leg) => ({
          ticker: leg.ticker,
          underlying: demoPetr4.underlying.ticker,
          ref_date: demoPetr4.ref_date,
          expiration: expiration.date,
          expiration_type: expiration.type,
          strike: row.strike,
          type: leg.type,
          exercise_style: leg.exercise_style,
          quote_state: leg.market.quote_state,
          last: leg.market.last,
          bid: leg.market.bid,
          ask: leg.market.ask,
          open_interest: leg.market.open_interest,
          volume: leg.market.volume,
          iv: leg.analytics.iv,
        })),
    ),
  );

  const filtered = contracts.filter((item) => {
    if (underlying && item.underlying !== underlying.trim().toUpperCase()) {
      return false;
    }
    if (query && !item.ticker.includes(query.trim().toUpperCase())) {
      return false;
    }
    return true;
  });

  return {
    contracts: filtered.slice(offset, offset + limit),
    offset,
    limit,
    total: filtered.length,
    next_offset:
      offset + limit < filtered.length ? offset + limit : null,
  };
}


function historyPointFromDetail(
  detail: OptionContractDetailPayload,
): OptionHistoryPayload {
  const contract = detail.contract;
  const market = contract.market;
  const analyticsInput = contract.analytics_input;
  const analytics = contract.analytics;

  return {
    schema_version: "0.1",
    contract: contract.ticker,
    underlying: detail.underlying.ticker,
    start_date: detail.ref_date,
    end_date: detail.ref_date,
    observations: 1,
    points: [
      {
        ref_date: detail.ref_date,
        source: "BOLSABR_SNAPSHOT",
        underlying_spot: detail.underlying.spot,
        last: market.last,
        bid: market.bid,
        ask: market.ask,
        spread_pct: market.spread_pct,
        quote_state: market.quote_state,
        quality_flags: market.quality_flags,
        trade_count: market.trade_count,
        volume: market.volume,
        financial_volume: market.financial_volume,
        open_interest: market.open_interest,
        price_for_model: analyticsInput.price,
        price_basis: analyticsInput.price_basis,
        risk_free_rate: analyticsInput.risk_free_rate,
        iv: analytics.iv,
        delta: analytics.delta,
        gamma: analytics.gamma,
        theta: analytics.theta,
        vega: analytics.vega,
        rho: analytics.rho,
        intrinsic: analytics.intrinsic,
        extrinsic: analytics.extrinsic,
      },
    ],
  };
}

export async function getOptionContractHistory(
  contract: string,
  {
    start,
    end,
    limit = 500,
  }: {
    start?: string;
    end?: string;
    limit?: number;
  } = {},
): Promise<OptionHistoryPayload | null> {
  const normalized = contract.trim().toUpperCase();
  const baseUrl = process.env.BOLSABR_API_BASE_URL?.replace(/\/$/, "");

  if (baseUrl) {
    const params = new URLSearchParams({ limit: String(limit) });
    if (start) params.set("start", start);
    if (end) params.set("end", end);

    const response = await fetch(
      `${baseUrl}/v1/options/${encodeURIComponent(normalized)}/history?${params.toString()}`,
      { next: { revalidate: 300 } },
    );

    if (response.status === 404) return null;
    if (!response.ok) {
      throw new Error(
        `BOLSABR option history failed with status ${response.status}`,
      );
    }
    return (await response.json()) as OptionHistoryPayload;
  }

  const detail = findDemoContract(normalized);
  return detail ? historyPointFromDetail(detail) : null;
}
