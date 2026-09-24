import type { MetadataRoute } from "next";

import {
  getAssetCatalog,
  getOptionContractCatalog,
} from "@/lib/option-chain";
import { getSiteUrl } from "@/lib/site";

export const dynamic = "force-dynamic";
export const revalidate = 300;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = getSiteUrl();
  const [assets, firstContracts] = await Promise.all([
    getAssetCatalog(),
    getOptionContractCatalog({ offset: 0, limit: 500 }),
  ]);

  const contracts = [...firstContracts.contracts];
  let nextOffset = firstContracts.next_offset;

  while (nextOffset != null) {
    const page = await getOptionContractCatalog({
      offset: nextOffset,
      limit: 500,
    });
    contracts.push(...page.contracts);
    nextOffset = page.next_offset;
  }

  const entries: MetadataRoute.Sitemap = [
    {
      url: new URL("/", base).toString(),
      changeFrequency: "daily",
      priority: 1,
    },
  ];

  for (const asset of assets) {
    entries.push({
      url: new URL(
        `/acoes/${encodeURIComponent(asset.ticker)}/opcoes`,
        base,
      ).toString(),
      lastModified: asset.ref_date,
      changeFrequency: "daily",
      priority: 0.9,
    });
  }

  for (const contract of contracts) {
    entries.push({
      url: new URL(
        `/opcoes/${encodeURIComponent(contract.ticker)}`,
        base,
      ).toString(),
      lastModified: contract.ref_date,
      changeFrequency: "daily",
      priority: 0.7,
    });
  }

  return entries;
}
