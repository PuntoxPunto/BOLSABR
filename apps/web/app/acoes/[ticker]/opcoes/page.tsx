import type { Metadata } from "next";
import { notFound } from "next/navigation";
import OptionChainClient from "@/components/option-chain/OptionChainClient";
import { getAssetCatalog, getOptionChain } from "@/lib/option-chain";
import { getSiteUrl } from "@/lib/site";

type PageProps = {
  params: Promise<{ ticker: string }>;
};

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { ticker } = await params;
  const normalized = ticker.toUpperCase();

  const url = new URL(
    `/acoes/${encodeURIComponent(normalized)}/opcoes`,
    getSiteUrl(),
  ).toString();

  return {
    title: `${normalized} Opções`,
    description: `Option Chain de ${normalized} com Bid/Ask, volume, open interest, IV e Greeks.`,
    alternates: {
      canonical: url,
    },
    openGraph: {
      type: "website",
      title: `${normalized} Opções`,
      description: `Option Chain de ${normalized} com Bid/Ask, volume, open interest, IV e Greeks.`,
      url,
    },
  };
}

export default async function AssetOptionsPage({ params }: PageProps) {
  const { ticker } = await params;
  const [data, assets] = await Promise.all([
    getOptionChain(ticker),
    getAssetCatalog(),
  ]);

  if (!data) {
    notFound();
  }

  return <OptionChainClient data={data} assets={assets} />;
}
