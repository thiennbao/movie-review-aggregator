import type { Metadata } from "next";
import { Montserrat } from "next/font/google";
import "./globals.css";

const montserrat = Montserrat({
  weight: ["400", "700"],
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Rotten Apple",
  description: "A tool for collecting and statisticizing movie reviews from IMDb, Rotten Tomatoes and Metacritic",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${montserrat.className} antialiased overflow-x-hidden`}>{children}</body>
    </html>
  );
}

