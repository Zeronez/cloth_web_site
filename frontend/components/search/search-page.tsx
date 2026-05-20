"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchProducts, type Product } from "../../lib/api";
import { ProductImagePlaceholder } from "../product-image-placeholder";

function buildParams(query: string) {
  const params = new URLSearchParams();
  const trimmed = query.trim();
  if (trimmed) {
    params.set("search", trimmed);
  }
  params.set("page_size", "12");
  return params;
}

export function SearchPage() {
  const [query, setQuery] = useState("");
  const params = useMemo(() => buildParams(query), [query]);
  const productsQuery = useQuery({
    queryKey: ["search", params.toString()],
    queryFn: () => fetchProducts(params),
    retry: false
  });

  const products = productsQuery.data?.results ?? [];
  const isEmpty = !productsQuery.isLoading && !productsQuery.isError && products.length === 0;

  const suggestions = useMemo(
    () => ["Атака титанов", "Наруто", "Куртка", "Худи", "Черный", "M"],
    []
  );

  return (
    <main className="bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
      <section className="mx-auto max-w-7xl">
        <div className="max-w-3xl">
          <p className="text-xs font-black uppercase tracking-[0.24em] text-neon-teal">
            Поиск
          </p>
          <h1 className="mt-4 text-4xl font-black leading-tight sm:text-5xl">
            Найдите нужный дроп
          </h1>
          <p className="mt-5 text-base leading-8 text-slate-300 sm:text-lg">
            Введите запрос — мы покажем подходящие позиции по названию и описанию.
          </p>
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-[minmax(0,1fr)_18rem]">
          <div>
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-slate-200">
                Запрос
              </span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Например: Akira, куртка, XL…"
                className="h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition placeholder:text-slate-500 focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30"
              />
            </label>

            {productsQuery.isError ? (
              <div className="mt-4 border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
                Не удалось выполнить поиск. Попробуйте обновить страницу.
              </div>
            ) : null}

            {isEmpty ? (
              <div className="mt-4 border border-neon-amber/30 bg-neon-amber/10 px-4 py-3 text-sm leading-6 text-orange-100">
                Ничего не найдено. Попробуйте другой запрос.
              </div>
            ) : null}

            <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {products.map((product: Product) => (
                <Link
                  key={product.id}
                  href={`/products/${product.slug}`}
                  className="group border border-white/10 bg-white/[0.04] p-4 transition hover:border-white/25"
                >
                  <div className="aspect-[4/5] overflow-hidden border border-white/10 bg-black/20">
                    <ProductImagePlaceholder
                      alt={product.name}
                      variant="jacket"
                      className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.02]"
                    />
                  </div>
                  <div className="mt-4">
                    <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">
                      {product.franchise?.name ?? "AnimeAttire"}
                    </p>
                    <p className="mt-2 text-lg font-black">{product.name}</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          <aside className="space-y-6 border-t border-white/10 pt-6 lg:border-l lg:border-t-0 lg:pl-8 lg:pt-0">
            <div>
              <h2 className="text-2xl font-black text-white">Подсказки</h2>
              <p className="mt-3 text-sm leading-7 text-slate-300">
                Попробуйте один из быстрых запросов:
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {suggestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => setQuery(suggestion)}
                    className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs font-bold text-slate-200 transition hover:border-white/25 hover:text-white"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}

