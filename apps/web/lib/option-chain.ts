import { demoPetr4 } from "./demo-petr4";
import type { OptionChainPayload } from "./option-chain-types";

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
