import { demoPetr4 } from "./demo-petr4";
import type {
  AssetCatalogPayload,
  AssetSummary,
  OptionChainPayload,
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
