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
  const supportEmail = process.env.NEXT_PUBLIC_SUPPORT_EMAIL ?? "";
  const supportPhone = process.env.NEXT_PUBLIC_SUPPORT_PHONE ?? "";
  const supportTelegram = process.env.NEXT_PUBLIC_SUPPORT_TELEGRAM ?? "";

  return (
    <footer className="border-t border-white/10 bg-ink-950">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:px-6 md:grid-cols-[1fr_auto] lg:px-8">
        <div>
          <Image
            src="/brand/animeattire-logo.png"
            alt="AnimeAttire"
            width={2172}
            height={724}
            className="h-auto w-44"
          />
          <p className="mt-4 max-w-md text-sm leading-6 text-slate-400">
            Аниме-стритвир для России: доставка, возвраты и поддержка — без
            лишнего шума.
          </p>
          <p className="mt-3 max-w-md text-xs leading-6 uppercase text-slate-500">
            {supportEmail || supportPhone || supportTelegram
              ? "Поддержка"
              : "Контакты поддержки: требуется настройка"}
          </p>
          {supportEmail || supportPhone || supportTelegram ? (
            <ul className="mt-3 space-y-1 text-sm text-slate-300">
              {supportEmail ? (
                <li>
                  Email:{" "}
                  <a
                    className="underline underline-offset-4 hover:text-white"
                    href={`mailto:${supportEmail}`}
                  >
                    {supportEmail}
                  </a>
                </li>
              ) : null}
              {supportPhone ? <li>Телефон: {supportPhone}</li> : null}
              {supportTelegram ? (
                <li>
                  Telegram:{" "}
                  <a
                    className="underline underline-offset-4 hover:text-white"
                    href={supportTelegram}
                    rel="noreferrer"
                    target="_blank"
                  >
                    {supportTelegram}
                  </a>
                </li>
              ) : null}
            </ul>
          ) : null}
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
