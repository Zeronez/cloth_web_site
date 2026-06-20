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

const fitRecommendationTone: Record<string, string> = {
  none: "border-white/10 bg-white/5 text-slate-300",
  low: "border-neon-amber/20 bg-neon-amber/10 text-orange-100",
  medium: "border-neon-teal/20 bg-neon-teal/10 text-neon-teal",
  high: "border-neon-crimson/20 bg-neon-crimson/10 text-white"
};

const STYLE_TOKENS: Record<string, string[]> = {
  minimal: ["minimal", "clean", "basic", "essential"],
  streetwear: ["streetwear", "oversized", "cargo", "jersey", "hoodie"],
  dark_fantasy: ["dark", "fantasy", "gothic", "berserk", "chainsaw"],
  sport: ["sport", "jersey", "track", "training"],
  casual: ["casual", "daily", "everyday", "basic"]
};

const personalFilterBlockingWarnings = new Set([
  "fit_profile_incomplete",
  "no_active_sizes",
  "recommended_size_out_of_stock",
  "style_fit_mismatch",
  "season_mismatch",
  "style_mismatch"
]);

function isPersonalMatch(product: {
  fit_recommendation?: {
    recommended_size: string | null;
    warnings: Array<string | number>;
  } | null;
}) {
  const recommendation = product.fit_recommendation;
  if (!recommendation?.recommended_size) {
    return false;
  }

  const warnings = recommendation.warnings.map(String);
  return !warnings.some((warning) => personalFilterBlockingWarnings.has(warning));
}

function productMatchesQuiz(
  product: {
    fit_recommendation?: { warnings: Array<string | number> } | null;
    recommendation_metadata?: {
      recommendation_style_tags?: string[];
      recommendation_seasonality?: string;
      recommendation_fit_tendency?: string;
      recommendation_fit_confidence?: number;
    };
  },
  quizProfile: { preferred_style: string; preferred_season: string; preferred_fit: string }
) {
  const metadata = product.recommendation_metadata;
  if (!metadata) {
    return false;
  }

  const style = String(quizProfile.preferred_style || "").toLowerCase();
  const season = String(quizProfile.preferred_season || "").toLowerCase();
  const fit = String(quizProfile.preferred_fit || "").toLowerCase();

  const styleTokens = (metadata.recommendation_style_tags ?? []).map((token) =>
    String(token).toLowerCase()
  );
  const expectedStyle = STYLE_TOKENS[style] ?? [];
  const hasStyleMatch = expectedStyle.length
    ? expectedStyle.some((token) => styleTokens.includes(token))
    : true;

  const seasonality = String(metadata.recommendation_seasonality ?? "").toLowerCase();
  const hasSeasonMatch = season
    ? seasonality.includes(season) ||
      seasonality.includes("all_season") ||
      seasonality.includes("all")
    : true;

  const tendency = String(metadata.recommendation_fit_tendency ?? "").toLowerCase();
  const hasFitHint = fit ? tendency.includes(fit) : true;

  const confidenceHint = Number(metadata.recommendation_fit_confidence ?? 0);
  const hasMetadataConfidence = confidenceHint >= 3;

  const warnings = (product.fit_recommendation?.warnings ?? []).map(String);
  const hasNoHardWarnings = !warnings.includes("fit_profile_incomplete");

  return hasStyleMatch && hasSeasonMatch && hasFitHint && hasMetadataConfidence && hasNoHardWarnings;
}

function getWarningLabel(warning: string) {
  if (warning === "recommended_size_out_of_stock") {
    return "Размер заканчивается";
  }
  if (warning === "closest_available_size_selected") {
    return "Ближайший размер";
  }
  if (warning === "style_fit_mismatch") {
    return "Посадка отличается";
  }
  if (warning === "season_mismatch") {
    return "Сезон не совпадает";
  }
  if (warning === "style_mismatch") {
    return "Стиль может не совпасть";
  }
  if (warning === "fit_profile_incomplete") {
    return "Нужны ещё данные";
  }
  if (warning === "one_size_only") {
    return "One size";
  }
  if (warning === "runs_small") {
    return "Маломерит";
  }
  if (warning === "runs_large") {
    return "Большемерит";
  }
  if (warning === "oversized_by_design") {
    return "Оверсайз по дизайну";
  }
  if (warning === "no_active_sizes") {
    return "Нет активных размеров";
  }
  return warning;
}

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
  const [onlyPersonal, setOnlyPersonal] = useState(false);

  const productParams = useMemo(() => {
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (franchise) params.set("franchise", franchise);
    if (searchQuery.trim()) params.set("search", searchQuery.trim());
    if (size) params.set("size", size);
    if (inStock) params.set("in_stock", "true");
    if (onlyPersonal) params.set("personal", "true");
    return params;
  }, [category, franchise, inStock, onlyPersonal, searchQuery, size]);

  const productsQuery = useInfiniteQuery({
    queryKey: ["products", productParams.toString()],
    initialPageParam: 1,
    queryFn: async ({ pageParam }) => {
      const params = new URLSearchParams(productParams);
      params.set("page", String(pageParam));

      try {
        return await fetchProducts(params, accessToken);
      } catch (error) {
        if (accessToken && error instanceof ApiError && error.status === 401) {
          clearSession();
          return fetchProducts(params);
        }

        throw error;
      }
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

  const filteredProducts = useMemo(() => {
    if (!onlyPersonal) {
      return products;
    }

    if (!accessToken) {
      return [];
    }

    return products.filter(isPersonalMatch);
  }, [accessToken, onlyPersonal, products]);

  const categories = categoriesQuery.data?.results ?? [];
  const franchises = franchisesQuery.data?.results ?? [];
  const isInitialLoading = productsQuery.isLoading && !productsQuery.data;
  const isProductsError = productsQuery.isError && !productsQuery.data;
  const hasNoCatalogResults = Boolean(productsQuery.data && products.length === 0);
  const hasNoFilteredResults = Boolean(productsQuery.data && filteredProducts.length === 0);
  const hasNextPage = Boolean(productsQuery.hasNextPage);
  const canLoadMore = hasNextPage && filteredProducts.length > 0;
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
                  setOnlyPersonal(false);
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

              <label className="flex items-center justify-between border border-white/10 bg-white/5 px-3 py-3 text-sm font-bold text-slate-200">
                Подходящие товары именно вам
                <input
                  type="checkbox"
                  checked={onlyPersonal}
                  onChange={(event) => setOnlyPersonal(event.target.checked)}
                  className="h-5 w-5 accent-[#ED254E]"
                />
              </label>
              <p className="text-xs leading-5 text-slate-400">
                Работает по данным теста из{" "}
                <Link href="/fitting" className="font-semibold text-neon-teal hover:text-white">
                  рекомендаций
                </Link>
                .
              </p>
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
                {productsQuery.isFetching
                  ? "Обновляем каталог"
                  : `${filteredProducts.length} позиций`}
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

            {hasNoCatalogResults ? (
              <div className="border border-white/10 bg-white/[0.04] p-10 text-center">
                <h3 className="text-2xl font-black">Ничего не найдено</h3>
                <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-slate-400">
                  Попробуйте сбросить фильтры, сменить тег в поиске или выбрать другой размер,
                  категорию или франшизу.
                </p>
              </div>
            ) : null}

            {!isInitialLoading && !hasNoCatalogResults && !isProductsError ? (
              <>
                {onlyPersonal && !accessToken ? (
                  <div className="mb-4">
                    <InlineNotice
                      title="Нужен тест для персональной подборки"
                      text="Войдите в аккаунт, пройдите тест на странице рекомендаций и вернитесь сюда — после этого фильтр «Подходящие товары именно вам» начнёт работать."
                      tone="info"
                    />
                    <div className="mt-3">
                      <Link
                        href="/login"
                        className="inline-flex h-10 items-center border border-neon-teal/30 bg-neon-teal/10 px-4 text-xs font-black uppercase tracking-[0.18em] text-ice transition hover:bg-neon-teal/20"
                      >
                        Войти
                      </Link>
                    </div>
                  </div>
                ) : null}

                {onlyPersonal && accessToken && hasNoFilteredResults ? (
                  <div className="mb-4">
                    <InlineNotice
                      title="Пока нет точных совпадений"
                      text="Похоже, тест ещё не заполнен или данных недостаточно. Пройдите тест на странице рекомендаций и вернитесь сюда."
                      tone="warning"
                    />
                    <div className="mt-3">
                      <Link
                        href="/fitting"
                        className="inline-flex h-10 items-center border border-white/15 bg-white/5 px-4 text-xs font-black uppercase tracking-[0.18em] text-white transition hover:border-white/30 hover:bg-white/10"
                      >
                        Перепройти тест
                      </Link>
                    </div>
                  </div>
                ) : null}

                <div className="grid auto-rows-[minmax(320px,_auto)] gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {filteredProducts.map((product, index) => {
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

                              {product.fit_recommendation && false ? (
                                <div
                                  className={`mt-4 rounded-2xl border p-3 ${fitRecommendationTone[product.fit_recommendation!.confidence] ?? fitRecommendationTone.none}`}
                                >
                                  <div className="flex flex-wrap items-center justify-between gap-2">
                                    <p className="text-[11px] font-black uppercase tracking-[0.18em]">
                                      Умная примерочная
                                    </p>
                                    <span className="text-xs font-semibold uppercase">
                                      {product.fit_recommendation!.recommended_size
                                        ? `Размер ${product.fit_recommendation!.recommended_size}`
                                        : "Нужны данные"}
                                    </span>
                                  </div>
                                  <p className="mt-2 line-clamp-2 text-sm leading-5">
                                    {product.fit_recommendation!.summary}
                                  </p>
                                  {product.fit_recommendation!.warnings.length > 0 ? (
                                    <div className="mt-3 flex flex-wrap gap-2">
                                      {product.fit_recommendation!.warnings
                                        .slice(0, 2)
                                        .map((warning) => (
                                          <span
                                            key={`${product.slug}-${warning}`}
                                            className="rounded-full border border-white/10 bg-black/15 px-2 py-1 text-[10px] font-semibold uppercase text-slate-100"
                                          >
                                            {getWarningLabel(warning)}
                                          </span>
                                        ))}
                                    </div>
                                  ) : null}
                                  {product.fit_recommendation!.warnings
                                    .map(String)
                                    .includes("fit_profile_incomplete") ? (
                                    <button
                                      type="button"
                                      onClick={(event) => {
                                        event.preventDefault();
                                        event.stopPropagation();
                                        return;
                                      }}
                                      className="mt-3 inline-flex h-9 items-center rounded-full border border-white/15 bg-white/5 px-4 text-xs font-black uppercase tracking-[0.18em] text-white transition hover:border-white/30 hover:bg-white/10"
                                    >
                                      Пройти тест
                                    </button>
                                  ) : null}
                                  {product.fit_recommendation!.outfit.items.length > 0 ? (
                                    <p className="mt-3 text-xs leading-5 text-slate-200">
                                      Капсула:{" "}
                                      <span className="font-semibold">
                                        {product.fit_recommendation!.outfit.items.length}{" "}
                                        {product.fit_recommendation!.outfit.items.length === 1
                                          ? "вещь"
                                          : product.fit_recommendation!.outfit.items.length < 5
                                            ? "вещи"
                                            : "вещей"}
                                      </span>
                                      {product.fit_recommendation!.outfit.total_price ? (
                                        <>
                                          {" "}
                                          · Итого{" "}
                                          <span className="font-semibold">
                                            {money.format(
                                              Number(
                                                product.fit_recommendation!.outfit.total_price
                                              )
                                            )}
                                          </span>
                                        </>
                                      ) : null}
                                    </p>
                                  ) : null}
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

                {canLoadMore ? (
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
