"use client";

import Link from "next/link";
import { useEffect } from "react";

export default function Error({
  error,
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
      <section className="mx-auto max-w-4xl border border-red-400/30 bg-red-500/10 p-6 sm:p-8">
        <p className="text-xs font-black uppercase text-red-100">
          Ошибка интерфейса
        </p>
        <h1 className="mt-3 text-3xl font-black sm:text-4xl">
          Что‑то пошло не так.
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-7 text-red-50">
          Мы не смогли корректно отрисовать страницу. Попробуйте повторить
          загрузку или вернитесь в каталог.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={reset}
            className="inline-flex h-12 items-center bg-neon-crimson px-5 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950"
          >
            Повторить загрузку
          </button>
          <Link
            href="/catalog"
            className="inline-flex h-12 items-center border border-white/15 bg-white/5 px-5 text-sm font-semibold text-white transition hover:border-neon-teal/60 hover:bg-white/10"
          >
            В каталог
          </Link>
          <Link
            href="/"
            className="inline-flex h-12 items-center border border-white/15 bg-white/5 px-5 text-sm font-semibold text-white transition hover:border-neon-teal/60 hover:bg-white/10"
          >
            На главную
          </Link>
        </div>
      </section>
    </main>
  );
}

