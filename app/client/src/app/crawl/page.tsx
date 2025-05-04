"use client";

import Reviews from "@/components/reviews";
import UrlInput from "@/components/url-input";
import { useSearchParams } from "next/navigation";

export default function Crawl() {
  const searchParams = useSearchParams();
  const url = searchParams.get("url");

  return <main>{url ? <Reviews url={url} /> : <UrlInput />}</main>;
}
