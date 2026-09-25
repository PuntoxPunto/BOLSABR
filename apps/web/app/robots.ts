import type { MetadataRoute } from "next";

import { getAssetCatalog } from "@/lib/option-chain";
import { getSiteUrl } from "@/lib/site";

export const dynamic = "force-dynamic";
export const revalidate = 300;

export default async function robots(): Promise<MetadataRoute.Robots> {
  const base = getSiteUrl();
  const assets = await getAssetCatalog();

  return {
    rules: {
      userAgent: "*",
      allow: "/",
    },
    sitemap: [
      new URL("/sitemap.xml", base).toString(),
      ...assets.map((asset) =>
        new URL(
          `/opcoes/sitemap/${encodeURIComponent(asset.ticker)}.xml`,
          base,
        ).toString(),
      ),
    ],
  };
}
