import Link from "next/link";

export default function Header() {
  return (
    <header>
      <div className="container mx-auto px-8 h-20 flex items-center justify-center relative z-1">
        <Link href="/" className="h-3/5">
          {/* eslint-disable @next/next/no-img-element */}
          <img src="logo.png" alt="Rotten Potatoes" className="h-full" />
        </Link>
      </div>
    </header>
  );
}
