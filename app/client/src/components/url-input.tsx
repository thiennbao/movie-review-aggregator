import { Icon } from "@iconify/react";
import Light from "./light";

export default function UrlInput() {
  return (
    <div className="h-screen -mt-20 flex justify-center items-center">
      <div className="w-1/2">
        <div className="text-3xl text-center mb-8 text-gradient font-bold">Enter an URL to start aggregating</div>
        <div className="flex bg-formground rounded-2xl items-end">
          <textarea placeholder="https://www.rottentomatoes.com/m/a_nightmare_semester_at_hcmus" className="w-full resize-none p-4 border-none outline-none overflow-y-scroll [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-thumb]:bg-primary" />
          <button type="button" title="Go" className="p-4">
            <Icon icon="formkit:submit" className="text-3xl cursor-pointer" />
          </button>
        </div>
      </div>
      <Light className="left-0 top-full bg-gradient" />
      <Light className="left-full top-0 bg-gradient" />
    </div>
  );
}
