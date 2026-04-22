import Image from "next/image";
import Link from "next/link";

const footerLinks = [
  { label: "Доставка", href: "/delivery" },
  { label: "Возврат", href: "/returns" },
  { label: "Оферта", href: "/offer" },
  { label: "Конфиденциальность", href: "/privacy" },
  { label: "Контакты", href: "/contacts" }
];

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
            Аниме-стритвир для магазина в СНГ: полезные правила, контакты и
            условия работы собраны здесь без лишнего шума.
          </p>
          <p className="mt-3 max-w-md text-xs leading-6 uppercase text-slate-500">
            Реквизиты и операционные данные: требуется настройка
          </p>
        </div>

        <nav
          aria-label="Служебные ссылки"
          className="grid gap-3 text-sm font-semibold text-slate-300 sm:grid-cols-2"
        >
          {footerLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="transition hover:text-white"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </footer>
  );
}
