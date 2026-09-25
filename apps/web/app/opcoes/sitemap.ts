import type { MetadataRoute } from "next";

import {
  getAssetCatalog,
  getOptionContractCatalog,
} from "@/lib/option-chain";
import { getSiteUrl } from "@/lib/site";

const PAGE_SIZE = 500;

export const dynamic = "force-dynamic";
export const revalidate = 300;

export async function generateSitemaps() {
  const assets = await getAssetCatalog();
  return assets.map((asset) => ({ id: asset.ticker }));
}

export default async function sitemap(props: {
  id: Promise<string>;
}): Promise<MetadataRoute.Sitemap> {
  const underlying = (await props.id).trim().toUpperCase();
  const assets = await getAssetCatalog(underlying);

  if (!assets.some((asset) => asset.ticker === underlying)) {
    return [];
  }

  const contracts = [];
  let offset = 0;

  while (true) {
    const page = await getOptionContractCatalog({
      underlying,
      offset,
      limit: PAGE_SIZE,
    });
    contracts.push(...page.contracts);

    if (page.next_offset == null) break;
    offset = page.next_offset;
  }

  const base = getSiteUrl();
  return contracts.map((contract) => ({
    url: new URL(
      `/opcoes/${encodeURIComponent(contract.ticker)}`,
      base,
    ).toString(),
    lastModified: contract.ref_date,
    changeFrequency: "daily" as const,
    priority: 0.7,
  }));
}
