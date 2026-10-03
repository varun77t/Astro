import type { Metadata } from "next";
import { Geist, Geist_Mono, Instrument_Serif, Kalam, Tiro_Devanagari_Sanskrit } from "next/font/google";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });
const instrumentSerif = Instrument_Serif({
  variable: "--font-instrument-serif",
  subsets: ["latin"],
  weight: "400",
});
const kalam = Kalam({ variable: "--font-kalam", subsets: ["latin"], weight: ["400", "700"] });
const tiroDeva = Tiro_Devanagari_Sanskrit({
  variable: "--font-tiro-deva",
  subsets: ["devanagari"],
  weight: "400",
});

export const metadata: Metadata = {
  title: "Vedic Astro",
  description: "Vedic astrology readings that show their working: every insight traced to the placement behind it.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  const fonts = [geistSans, geistMono, instrumentSerif, kalam, tiroDeva].map((f) => f.variable).join(" ");
  return (
    <html lang="en" className={`${fonts} h-full`}>
      <body className="flex min-h-full flex-col">{children}</body>
    </html>
  );
}
