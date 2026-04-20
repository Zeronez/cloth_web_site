"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
import { selectCartCount, useCartStore } from "../stores/cart-store";
import { useUserStore } from "../stores/user-store";

const navigationItems = [
  { label: "Каталог", href: "/catalog" },
  { label: "Лукбук", href: "/#lookbook" },
  { label: "Крой", href: "/#craft" }
];

export function Header() {
  const [scrolled, setScrolled] = useState(false);
  const cartCount = useCartStore(selectCartCount);
  const openCart = useCartStore((state) => state.openCart);
  const profile = useUserStore((state) => state.profile);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });

    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-40 border-b transition-all duration-300 ${
        scrolled
          ? "border-white/10 bg-ink-950/80 shadow-[0_16px_48px_rgba(0,0,0,0.28)] backdrop-blur-xl"
          : "border-transparent bg-transparent"
      }`}
    >
      <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link
          href="/"
          aria-label="На главную AnimeAttire"
          className="flex h-12 w-44 items-center"
        >
          <Image
            src="/brand/animeattire-logo.svg"
            alt="AnimeAttire"
            width={960}
            height={240}
            priority
            className="h-auto w-full"
          />
        </Link>

        <nav
          aria-label="Основная навигация"
          className="hidden items-center gap-8 md:flex"
        >
          {navigationItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-sm font-semibold uppercase text-slate-200/80 transition hover:text-white"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <Link
            href={profile ? "/account" : "/login"}
            className="grid h-11 w-11 place-items-center border border-white/15 bg-white/10 text-white transition hover:border-neon-teal/70 hover:bg-neon-teal/10 focus:outline-none focus:ring-2 focus:ring-neon-teal"
            aria-label={profile ? "Открыть аккаунт" : "Войти"}
          >
            <span className="relative block h-5 w-5">
              <span className="absolute left-1/2 top-0 h-2.5 w-2.5 -translate-x-1/2 rounded-full border-2 border-current" />
              <span className="absolute bottom-0 left-1/2 h-2.5 w-4 -translate-x-1/2 rounded-t-full border-2 border-b-0 border-current" />
            </span>
          </Link>

          <button
            type="button"
            onClick={openCart}
            className="group relative grid h-11 w-11 place-items-center border border-white/15 bg-white/10 text-white transition hover:border-neon-crimson/70 hover:bg-neon-crimson/10 focus:outline-none focus:ring-2 focus:ring-neon-teal"
            aria-label={`Открыть корзину, товаров: ${cartCount}`}
          >
            <span className="h-5 w-5 border-2 border-current border-t-0" />
            <span className="absolute top-2 h-2 w-3 rounded-t-full border-2 border-b-0 border-current" />
            {cartCount > 0 ? (
              <span className="absolute -right-2 -top-2 grid h-6 min-w-6 place-items-center rounded-full bg-neon-crimson px-1 text-xs font-bold text-white shadow-neon-crimson">
                {cartCount}
              </span>
            ) : null}
          </button>
        </div>
      </div>
    </header>
  );
}
