"use client";

import Footer from "@/components/footer";
import Header from "@/components/header";
import Reviews from "@/components/reviews";
import UrlInput from "@/components/url-input";
import { useSearchParams } from "next/navigation";

export default function Crawl() {
  const searchParams = useSearchParams();
  const url = searchParams.get("url");

  return (
    <div className="flex flex-col justify-between min-h-screen">
      <Header />
      <main>{url ? <Reviews url={url} /> : <UrlInput />}</main>
      <Footer />
    </div>
  );
}
