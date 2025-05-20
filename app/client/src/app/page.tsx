import Footer from "@/components/footer";
import Light from "@/components/light";
import { Icon } from "@iconify/react/dist/iconify.js";
import Link from "next/link";

export default function Home() {
  return (
    <main className="h-screen flex flex-col text-center lg:text-left">
      <div className="xl:max-w-screen-lg lg:max-w-screen-md w-full m-auto flex">
        <div className="flex-grow flex flex-col justify-center items-center lg:items-start gap-y-4">
          <h1 className="text-6xl lg:text-8xl text-gradient">Rotten Apple</h1>
          <p className="md:text-xl">NLP-based Movie Entertainment Review Aggregator</p>
          <div className="flex mt-8 gap-4">
            <Link
              href="/crawl"
              className="px-4 py-2 cursor-pointer rounded border-2 border-primary hover:bg-primary hover:text-background transition flex items-center gap-2"
            >
              <span>Getting started</span>
              <Icon icon="fluent:arrow-right-12-filled" />
            </Link>
          </div>
        </div>
        <div className="hidden w-1/3 lg:flex justify-end items-center relative">
          {/* eslint-disable @next/next/no-img-element */}
          <img src="/logo.png" alt="Rotten potatoes" className="z-10 scale-125" />
          <Light className="top-1/2 left-1/2 w-full bg-gradient" />
        </div>
      </div>
      <Footer />
    </main>
  );
}

