import type { MetadataRoute } from "next";

import { getAssetCatalog } from "@/lib/option-chain";
import { getSiteUrl } from "@/lib/site";

export const dynamic = "force-dynamic";
export const revalidate = 300;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = getSiteUrl();
  const assets = await getAssetCatalog();

  return [
    {
      url: new URL("/", base).toString(),
      changeFrequency: "daily",
      priority: 1,
    },
    ...assets.map((asset) => ({
      url: new URL(
        `/acoes/${encodeURIComponent(asset.ticker)}/opcoes`,
        base,
      ).toString(),
      lastModified: asset.ref_date,
      changeFrequency: "daily" as const,
      priority: 0.9,
    })),
  ];
}
