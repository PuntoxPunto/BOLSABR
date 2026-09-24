import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "BOLSABR",
    template: "%s | BOLSABR",
  },
  description:
    "Option Chain, volatilidade, carteira e inteligência para ações e opções da B3.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
