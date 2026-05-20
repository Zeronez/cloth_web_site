"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  ApiError,
  fetchCategories,
  fetchFavorites,
  fetchFranchises,
  fetchProducts
} from "../../lib/api";
import { useFavoritesStore } from "../../stores/favorites-store";
import { useUserStore } from "../../stores/user-store";
import { CatalogGridSkeleton, InlineNotice } from "../loading-states";
import { CatalogProductMedia } from "../product-media";
import { FavoriteToggleButton } from "./favorite-toggle-button";

const sizes = ["XS", "S", "M", "L", "XL", "XXL"];
const placeholderVariants = ["jacket", "hoodie", "pants"] as const;

const money = new Intl.NumberFormat("ru-RU", {
  currency: "RUB",
  style: "currency"
});

export function CatalogPage() {
  const accessToken = useUserStore((state) => state.accessToken);
  const clearSession = useUserStore((state) => state.clearSession);
  const setFavorites = useFavoritesStore((state) => state.setFavorites);

  const [category, setCategory] = useState("");
  const [franchise, setFranchise] = useState("");
  const [size, setSize] = useState("");
  const [inStock, setInStock] = useState(true);

  const productParams = useMemo(() => {
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (franchise) params.set("franchise", franchise);
    if (size) params.set("size", size);
    if (inStock) params.set("in_stock", "true");
    return params;
  }, [category, franchise, size, inStock]);

  const productsQuery = useQuery({
    queryKey: ["products", productParams.toString()],
    queryFn: () => fetchProducts(productParams)
  });
  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: fetchCategories
  });
  const franchisesQuery = useQuery({
    queryKey: ["franchises"],
    queryFn: fetchFranchises
  });
  const favoritesQuery = useQuery({
    queryKey: ["favorites", accessToken, "catalog"],
    enabled: Boolean(accessToken),
    queryFn: () => fetchFavorites(accessToken ?? ""),
    retry: false
  });

  useEffect(() => {
    if (favoritesQuery.data) {
      setFavorites(favoritesQuery.data);
    }
  }, [favoritesQuery.data, setFavorites]);

  useEffect(() => {
    if (favoritesQuery.error instanceof ApiError && favoritesQuery.error.status === 401) {
      clearSession();
    }
  }, [clearSession, favoritesQuery.error]);

  const products = productsQuery.data?.results ?? [];
  const categories = categoriesQuery.data?.results ?? [];
  const franchises = franchisesQuery.data?.results ?? [];
  const isInitialLoading = productsQuery.isLoading && !productsQuery.data;
  const isProductsError = productsQuery.isError && !productsQuery.data;
  const hasNoResults = Boolean(productsQuery.data && products.length === 0);

  return (
    <main className="min-h-screen bg-ink-950 px-4 pb-20 pt-28 text-white sm:px-6 lg:px-8">
      <section className="mx-auto max-w-7xl">
        <div className="grid gap-8 lg:grid-cols-[320px_1fr]">
          <aside className="h-fit border border-white/10 bg-white/[0.04] p-4">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-black">Каталог</h1>
              <button
                type="button"
                onClick={() => {
                  setCategory("");
                  setFranchise("");
                  setSize("");
                  setInStock(true);
                }}
                className="text-sm font-semibold text-slate-300 transition hover:text-white"
              >
                Сбросить
              </button>
            </div>

            <div className="mt-6 space-y-5">
              <label className="block">
                <span className="text-sm font-bold text-slate-300">Категория</span>
                <select
                  value={category}
                  onChange={(event) => setCategory(event.target.value)}
                  className="mt-2 h-11 w-full border border-white/10 bg-ink-900 px-3 text-sm text-white"
                >
                  <option value="">Все категории</option>
                  {categories.map((item) => (
                    <option key={item.slug} value={item.slug}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <span className="text-sm font-bold text-slate-300">Франшиза</span>
                <select
                  value={franchise}
                  onChange={(event) => setFranchise(event.target.value)}
                  className="mt-2 h-11 w-full border border-white/10 bg-ink-900 px-3 text-sm text-white"
                >
                  <option value="">Все вселенные</option>
                  {franchises.map((item) => (
                    <option key={item.slug} value={item.slug}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>

              <div>
                <span className="text-sm font-bold text-slate-300">Размер</span>
                <div className="mt-2 grid grid-cols-3 gap-2">
                  {sizes.map((item) => (
                    <button
                      key={item}
                      type="button"
                      onClick={() => setSize(size === item ? "" : item)}
                      className={`h-10 border text-sm font-bold transition ${
                        size === item
                          ? "border-neon-crimson bg-neon-crimson text-white"
                          : "border-white/10 bg-white/5 text-slate-300 hover:border-white/30"
                      }`}
                    >
                      {item}
                    </button>
                  ))}
                </div>
              </div>

              <label className="flex items-center justify-between border border-white/10 bg-white/5 px-3 py-3 text-sm font-bold text-slate-200">
                В наличии
                <input
                  type="checkbox"
                  checked={inStock}
                  onChange={(event) => setInStock(event.target.checked)}
                  className="h-5 w-5 accent-[#ff385c]"
                />
              </label>
            </div>
          </aside>

          <section>
            <div className="mb-5 flex items-end justify-between gap-4">
              <div>
                <p className="text-sm font-bold uppercase text-neon-teal">
                  Актуальная подборка
                </p>
                <h2 className="mt-2 text-3xl font-black sm:text-4xl">
                  Bento-витрина лимитированной anime-одежды.
                </h2>
              </div>
              <p className="hidden text-sm text-slate-400 md:block">
                {productsQuery.isFetching ? "Обновляем дропы" : `${products.length} позиций`}
              </p>
            </div>

            {isProductsError ? (
              <div className="mb-4">
                <InlineNotice
                  title="Каталог временно недоступен"
                  text="Не удалось загрузить товары из API. Попробуйте обновить страницу чуть позже."
                  tone="warning"
                />
              </div>
            ) : null}

            {isInitialLoading ? <CatalogGridSkeleton /> : null}

            {hasNoResults ? (
              <div className="border border-white/10 bg-white/[0.04] p-10 text-center">
                <h3 className="text-2xl font-black">Ничего не найдено</h3>
                <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-slate-400">
                  Попробуйте сбросить фильтры или выбрать другой размер, категорию или
                  франшизу.
                </p>
              </div>
            ) : null}

            {!isInitialLoading && !hasNoResults && !isProductsError ? (
              <div className="grid auto-rows-[260px] gap-4 md:grid-cols-2 xl:grid-cols-3">
                {products.map((product, index) => {
                  const isHero = index === 0;
                  const mediaHeight = isHero ? "h-[340px] md:h-[420px]" : "h-[240px]";

                  return (
                    <Link
                      key={product.slug}
                      href={`/products/${product.slug}`}
                      className={`group relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] transition hover:-translate-y-0.5 hover:border-neon-crimson/60 hover:bg-white/[0.06] ${
                        isHero ? "md:col-span-2 md:row-span-2" : ""
                      }`}
                    >
                      <div className="relative h-full">
                        <div
                          className={`relative overflow-hidden border-b border-white/10 bg-black/20 ${mediaHeight}`}
                        >
                          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.10),transparent_45%),linear-gradient(135deg,rgba(255,56,92,0.22),transparent_42%,rgba(20,184,166,0.16))] opacity-80 transition duration-500 group-hover:scale-[1.02]" />
                          <CatalogProductMedia
                            product={product}
                            placeholderVariant={
                              placeholderVariants[index % placeholderVariants.length]
                            }
                          />

                          <div className="absolute left-4 top-4 flex flex-wrap items-center gap-2">
                            <span className="rounded-full border border-white/10 bg-ink-950/80 px-3 py-1.5 text-xs font-bold text-slate-200">
                              {product.category.name}
                            </span>
                            <span className="rounded-full border border-white/10 bg-white/10 px-3 py-1.5 text-xs font-semibold text-slate-200">
                              {product.franchise?.name ?? "AnimeAttire"}
                            </span>
                          </div>

                          <div className="absolute right-4 top-4 flex items-center gap-2">
                            <span
                              className={`rounded-full px-3 py-1.5 text-xs font-black ${
                                product.total_stock > 0
                                  ? "bg-neon-teal text-ink-950"
                                  : "bg-white/10 text-slate-200"
                              }`}
                            >
                              {product.total_stock > 0
                                ? `В наличии: ${product.total_stock}`
                                : "Нет в наличии"}
                            </span>
                            <div className="rounded-full border border-white/10 bg-ink-950/70 p-1">
                              <FavoriteToggleButton
                                product={product}
                                compact
                                stopPropagation
                              />
                            </div>
                          </div>

                          <div className="absolute inset-x-0 bottom-0 h-24 bg-[linear-gradient(180deg,transparent,rgba(2,6,23,0.92))]" />
                        </div>

                        <div className="flex flex-col justify-between p-5">
                          <div>
                            <h3 className="text-lg font-black leading-snug sm:text-xl">
                              {product.name}
                            </h3>
                            <p className="mt-2 line-clamp-2 text-sm text-slate-300">
                              {product.category.description}
                            </p>
                          </div>

                          <div className="mt-5 flex items-end justify-between gap-3">
                            <div>
                              <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-400">
                                Цена
                              </p>
                              <p className="mt-1 text-2xl font-black">
                                {money.format(Number(product.base_price))}
                              </p>
                            </div>
                            <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-black uppercase text-white transition group-hover:border-neon-crimson/60 group-hover:bg-neon-crimson/10">
                              Открыть
                              <svg
                                viewBox="0 0 24 24"
                                fill="none"
                                aria-hidden="true"
                                className="h-4 w-4"
                              >
                                <path
                                  d="M7 17L17 7"
                                  stroke="currentColor"
                                  strokeWidth="2"
                                  strokeLinecap="round"
                                />
                                <path
                                  d="M9 7h8v8"
                                  stroke="currentColor"
                                  strokeWidth="2"
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                />
                              </svg>
                            </span>
                          </div>
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            ) : null}
          </section>
        </div>
      </section>
    </main>
  );
}

