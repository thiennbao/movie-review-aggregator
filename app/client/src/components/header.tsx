export default function Header() {
  return (
    <header>
      <div className="container mx-auto px-8 h-20 flex items-center justify-center">
        {/* eslint-disable @next/next/no-img-element */}
        <img src="logo.svg" alt="Rotten Potatoes" className="h-3/5" />
      </div>
    </header>
  );
}
