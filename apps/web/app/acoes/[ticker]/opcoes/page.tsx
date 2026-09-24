import type { Metadata } from "next";
import { notFound } from "next/navigation";
import OptionChainClient from "@/components/option-chain/OptionChainClient";
import { getAssetCatalog, getOptionChain } from "@/lib/option-chain";

type PageProps = {
  params: Promise<{ ticker: string }>;
};

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { ticker } = await params;
  const normalized = ticker.toUpperCase();

  return {
    title: `${normalized} Opções`,
    description: `Option Chain de ${normalized} com Bid/Ask, volume, open interest, IV e Greeks.`,
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
