"use client";

import Footer from "@/components/footer";
import Header from "@/components/header";
import Reviews from "@/components/reviews";
import UrlInput from "@/components/url-input";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

export default function Crawl() {
  return (
    <div className="flex flex-col justify-between min-h-screen">
      <Header />
      <Suspense>
        <Main />
      </Suspense>
      <Footer />
    </div>
  );
}

function Main() {
  const searchParams = useSearchParams();
  const url = searchParams.get("url");

  return <main>{url ? <Reviews url={url} /> : <UrlInput />}</main>;
}
