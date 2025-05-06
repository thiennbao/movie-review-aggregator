import { HTMLAttributes } from "react";

export default function Light({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div {...props} className={`absolute -translate-x-1/2 -translate-y-1/2 aspect-square bg-white rounded-full blur-3xl ${className}`}></div>;
}
