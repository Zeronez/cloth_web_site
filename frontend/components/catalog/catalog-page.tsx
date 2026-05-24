"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";

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
const tagSearchSuggestions = [
  "Новый дроп",
  "Бестселлер",
  "Лимитированная серия",
  "Стритвир",
  "Оверсайз",
  "Коллекционная позиция"
];

const money = new Intl.NumberFormat("ru-RU", {
  currency: "RUB",
  style: "currency"
});

function getNextPageNumber(nextPageUrl: string | null) {
  if (!nextPageUrl) {
    return undefined;
  }

  try {
    const parsedUrl = new URL(nextPageUrl, "http://127.0.0.1");
    const page = parsedUrl.searchParams.get("page");

    if (!page) {
      return undefined;
    }

    const parsedPage = Number(page);
    return Number.isNaN(parsedPage) ? undefined : parsedPage;
  } catch {
    return undefined;
  }
}

export function CatalogPage() {
  const accessToken = useUserStore((state) => state.accessToken);
  const clearSession = useUserStore((state) => state.clearSession);
  const setFavorites = useFavoritesStore((state) => state.setFavorites);

  const [category, setCategory] = useState("");
  const [franchise, setFranchise] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [size, setSize] = useState("");
  const [inStock, setInStock] = useState(true);

  const productParams = useMemo(() => {
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (franchise) params.set("franchise", franchise);
    if (searchQuery.trim()) params.set("search", searchQuery.trim());
    if (size) params.set("size", size);
    if (inStock) params.set("in_stock", "true");
    return params;
  }, [category, franchise, inStock, searchQuery, size]);

  const productsQuery = useInfiniteQuery({
    queryKey: ["products", productParams.toString()],
    initialPageParam: 1,
    queryFn: ({ pageParam }) => {
      const params = new URLSearchParams(productParams);
      params.set("page", String(pageParam));
      return fetchProducts(params);
    },
    getNextPageParam: (lastPage) => getNextPageNumber(lastPage.next),
    refetchOnMount: "always",
    refetchOnWindowFocus: true
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

  const products = useMemo(() => {
    const seenSlugs = new Set<string>();
    const mergedProducts = productsQuery.data?.pages.flatMap((page) => page.results) ?? [];

    return mergedProducts.filter((product) => {
      if (seenSlugs.has(product.slug)) {
        return false;
      }

      seenSlugs.add(product.slug);
      return true;
    });
  }, [productsQuery.data]);

  const categories = categoriesQuery.data?.results ?? [];
  const franchises = franchisesQuery.data?.results ?? [];
  const isInitialLoading = productsQuery.isLoading && !productsQuery.data;
  const isProductsError = productsQuery.isError && !productsQuery.data;
  const hasNoResults = Boolean(productsQuery.data && products.length === 0);
  const hasNextPage = Boolean(productsQuery.hasNextPage);
  const isFetchingNextPage = productsQuery.isFetchingNextPage;

  return (
    <main className="min-h-screen bg-ink-950 px-4 pb-20 pt-28 text-white sm:px-6 lg:px-8">
      <section className="w-full">
        <div className="mx-auto grid w-full max-w-[1480px] gap-8 lg:grid-cols-[320px_minmax(0,1120px)] lg:justify-center">
          <aside className="h-fit border border-white/10 bg-white/[0.04] p-4 lg:justify-self-end">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-black">Каталог</h1>
              <button
                type="button"
                onClick={() => {
                  setCategory("");
                  setFranchise("");
                  setSearchQuery("");
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
                <span className="text-sm font-bold text-slate-300">
                  Поиск по названию и тегам
                </span>
                <input
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="Например: Наруто, Бестселлер, Оверсайз"
                  className="mt-2 h-11 w-full border border-white/10 bg-ink-900 px-3 text-sm text-white placeholder:text-slate-500"
                />
                <div className="mt-3 flex flex-wrap gap-2">
                  {tagSearchSuggestions.map((tagLabel) => (
                    <button
                      key={tagLabel}
                      type="button"
                      onClick={() => setSearchQuery(tagLabel)}
                      className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold text-slate-200 transition hover:border-white/25 hover:text-white"
                    >
                      {tagLabel}
                    </button>
                  ))}
                </div>
              </label>

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
                  className="h-5 w-5 accent-[#ED254E]"
                />
              </label>
            </div>
          </aside>

          <section className="w-full min-w-0 lg:justify-self-center">
            <div className="mb-5 flex items-end justify-between gap-4">
              <div>
                <p className="text-sm font-bold uppercase text-neon-teal">
                  Актуальная подборка
                </p>
                <h2 className="mt-2 text-3xl font-black sm:text-4xl">
                  Bento-витрина аниме-стритвира.
                </h2>
              </div>
              <p className="hidden text-sm text-slate-400 md:block">
                {productsQuery.isFetching ? "Обновляем каталог" : `${products.length} позиций`}
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
                  Попробуйте сбросить фильтры, сменить тег в поиске или выбрать другой размер,
                  категорию или франшизу.
                </p>
              </div>
            ) : null}

            {!isInitialLoading && !hasNoResults && !isProductsError ? (
              <>
                <div className="grid auto-rows-[minmax(320px,_auto)] gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {products.map((product, index) => {
                    const mediaHeight = "h-[300px] md:h-[340px]";

                    return (
                      <Link
                        key={product.slug}
                        href={`/products/${product.slug}`}
                        className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] transition hover:-translate-y-0.5 hover:border-white/25 hover:bg-white/[0.06] hover:shadow-[0_26px_80px_rgba(0,0,0,0.55)]"
                      >
                        <div className="relative flex h-full flex-col">
                          <div
                            className={`relative overflow-hidden border-b border-white/10 bg-black/20 ${mediaHeight}`}
                          >
                            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.14),transparent_55%),linear-gradient(180deg,rgba(0,0,0,0.04),rgba(0,0,0,0.36))] opacity-70 transition duration-500 group-hover:opacity-55" />
                            <CatalogProductMedia
                              product={product}
                              placeholderVariant={
                                placeholderVariants[index % placeholderVariants.length]
                              }
                            />

                            <div className="absolute right-4 top-4 flex items-center gap-3">
                              {product.total_stock <= 0 ? (
                                <span className="rounded-full border border-white/10 bg-ink-950/70 px-3 py-1.5 text-xs font-black text-white">
                                  Нет в наличии
                                </span>
                              ) : null}
                              <FavoriteToggleButton product={product} compact stopPropagation />
                            </div>

                            <div className="absolute inset-x-0 bottom-0 h-24 bg-[linear-gradient(180deg,transparent,rgba(2,6,23,0.78))]" />
                          </div>

                          <div className="flex flex-1 flex-col p-6">
                            <div className="min-h-0">
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="rounded-full border border-white/10 bg-ink-950/60 px-3 py-1.5 text-xs font-bold text-slate-200">
                                  {product.category.name}
                                </span>
                                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-slate-200">
                                  {product.franchise?.name ?? "AnimeAttire"}
                                </span>
                              </div>
                              <h3 className="mt-3 line-clamp-2 text-lg font-black leading-snug sm:text-xl">
                                {product.name}
                              </h3>
                              <p className="mt-2 line-clamp-2 text-sm text-slate-300">
                                {product.category.description}
                              </p>
                              {product.tags?.length ? (
                                <div className="mt-4 flex flex-wrap gap-2">
                                  {product.tags.slice(0, 2).map((tag) => (
                                    <span
                                      key={`${product.slug}-${tag.slug}`}
                                      className="rounded-full border border-neon-teal/20 bg-neon-teal/10 px-3 py-1 text-[11px] font-semibold text-neon-teal"
                                    >
                                      {tag.label}
                                    </span>
                                  ))}
                                </div>
                              ) : null}
                            </div>

                            <div className="mt-auto flex items-end justify-between gap-3 pt-6">
                              <div>
                                <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-400">
                                  Цена
                                </p>
                                <p className="mt-1 text-2xl font-black">
                                  {money.format(Number(product.base_price))}
                                </p>
                              </div>
                              <span
                                aria-label="Открыть"
                                className="inline-flex shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/5 p-3 text-white transition group-hover:border-white/25 group-hover:bg-white/10"
                              >
                                <span className="sr-only">Открыть</span>
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

                {hasNextPage ? (
                  <div className="mt-8 flex justify-center">
                    <button
                      type="button"
                      onClick={() => productsQuery.fetchNextPage()}
                      disabled={isFetchingNextPage}
                      className="h-12 rounded-full border border-white/15 bg-white/5 px-7 text-sm font-black uppercase tracking-[0.18em] text-white transition hover:border-white/30 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {isFetchingNextPage ? "Загружаем ещё" : "Ещё"}
                    </button>
                  </div>
                ) : null}
              </>
            ) : null}
          </section>
        </div>
      </section>
    </main>
  );
}
