"use client";

import { useRouter } from "next/navigation";
import { KeyboardEvent, useState } from "react";
import { Icon } from "@iconify/react";
import Light from "./light";

export default function UrlInput() {
  const router = useRouter();
  const [url, setUrl] = useState("");

  const handleSubmit = () => {
    if (url.trim()) {
      router.push(`?url=${encodeURIComponent(url)}`);
    }
  };

  const handleKeydown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex justify-center items-center h-screen absolute top-0 w-full overflow-hidden">
      <div className="lg:w-1/2 px-4">
        <div className="text-3xl text-center mb-8 text-gradient font-bold">Enter an URL to start aggregating</div>
        <div className="flex bg-formground rounded-2xl items-end">
          <textarea
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => handleKeydown(e)}
            placeholder="https://www.rottentomatoes.com/m/a_nightmare_semester_at_hcmus"
            className="w-full h-32 md:h-auto resize-none p-4 border-none outline-none overflow-y-scroll [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-thumb]:bg-primary"
          />
          <button onClick={handleSubmit} type="button" title="Go" className="p-4">
            <Icon icon="formkit:submit" className="text-3xl cursor-pointer hover:text-secondary transition" />
          </button>
        </div>
      </div>
      <Light className="left-0 top-full bg-gradient w-32 md:w-72" />
      <Light className="left-full top-0 bg-gradient w-32 md:w-72" />
    </div>
  );
}
