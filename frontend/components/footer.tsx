import Image from "next/image";

const footerLinks = ["Размеры", "Доставка", "Возврат", "Дропы", "Оферта"];

export function Footer() {
  return (
    <footer className="border-t border-white/10 bg-ink-950">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:px-6 md:grid-cols-[1fr_auto] lg:px-8">
        <div>
          <Image
            src="/brand/animeattire-logo.svg"
            alt="AnimeAttire"
            width={960}
            height={240}
            className="h-auto w-44"
          />
          <p className="mt-4 max-w-md text-sm leading-6 text-slate-400">
            Аниме-стритвир для ночного города, лимитированных дропов и образов,
            которые не теряются в толпе.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-5 text-sm font-semibold text-slate-300">
          {footerLinks.map((link) => (
            <a key={link} href="#" className="transition hover:text-white">
              {link}
            </a>
          ))}
        </div>
      </div>
    </footer>
  );
}
