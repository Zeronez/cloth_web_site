"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  ApiError,
  fetchFavorites,
  fetchCategories,
  fetchFranchises,
  fetchProducts,
  type Product
} from "../../lib/api";
import { CatalogGridSkeleton, InlineNotice } from "../loading-states";
import { ProductImagePlaceholder } from "../product-image-placeholder";
import { FavoriteToggleButton } from "./favorite-toggle-button";
import { useFavoritesStore } from "../../stores/favorites-store";
import { useUserStore } from "../../stores/user-store";

const fallbackProducts: Product[] = [
  {
    id: 1,
    name: "Куртка Neon Ronin",
    slug: "neon-ronin-shell",
    category: { id: 1, name: "Куртки", slug: "jackets", description: "" },
    franchise: { id: 1, name: "Оригинал", slug: "original", description: "" },
    base_price: "14800.00",
    is_featured: true,
    main_image: null,
    total_stock: 24
  },
  {
    id: 2,
    name: "Худи Arcade Alley",
    slug: "arcade-alley-hoodie",
    category: { id: 2, name: "Худи", slug: "hoodies", description: "" },
    franchise: { id: 2, name: "Сёнен Core", slug: "shonen-core", description: "" },
    base_price: "9600.00",
    is_featured: false,
    main_image: null,
    total_stock: 42
  },
  {
    id: 3,
    name: "Карго Signal",
    slug: "signal-cargo-pant",
    category: { id: 3, name: "Брюки", slug: "pants", description: "" },
    franchise: { id: 3, name: "Кибер Сага", slug: "cyber-saga", description: "" },
    base_price: "11800.00",
    is_featured: false,
    main_image: null,
    total_stock: 17
  }
];

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

  const products = productsQuery.data?.results ?? fallbackProducts;
  const categories = categoriesQuery.data?.results ?? [];
  const franchises = franchisesQuery.data?.results ?? [];
  const isInitialLoading = productsQuery.isLoading && !productsQuery.data;
  const isUsingFallback = productsQuery.isError && !productsQuery.data;
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
                {productsQuery.isFetching
                  ? "Обновляем дропы"
                  : `${products.length} позиций`}
              </p>
            </div>

            {isUsingFallback ? (
              <div className="mb-4">
                <InlineNotice
                  title="API временно недоступен"
                  text="Показываем демонстрационную витрину, чтобы интерфейс оставался проверяемым до запуска backend-сервиса."
                  tone="warning"
                />
              </div>
            ) : null}

            {isInitialLoading ? <CatalogGridSkeleton /> : null}

            {hasNoResults ? (
              <div className="border border-white/10 bg-white/[0.04] p-10 text-center">
                <h3 className="text-2xl font-black">Ничего не найдено</h3>
                <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-slate-400">
                  Попробуйте сбросить фильтры или выбрать другой размер, категорию
                  или франшизу.
                </p>
              </div>
            ) : null}

            {!isInitialLoading && !hasNoResults ? (
              <div className="grid auto-rows-[260px] gap-4 md:grid-cols-2 xl:grid-cols-3">
                {products.map((product, index) => (
                  <Link
                    key={product.slug}
                    href={`/products/${product.slug}`}
                    className={`group relative overflow-hidden border border-white/10 bg-white/[0.04] p-5 transition hover:border-neon-crimson/70 ${
                      index === 0 ? "md:col-span-2 md:row-span-2" : ""
                    }`}
                  >
                    <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(255,56,92,0.2),transparent_42%,rgba(20,184,166,0.18))] opacity-70 transition group-hover:scale-105" />
                    <ProductImagePlaceholder
                      label={product.category.name}
                      variant={placeholderVariants[index % placeholderVariants.length]}
                      className="absolute inset-0 opacity-80 transition duration-500 group-hover:scale-[1.03] group-hover:opacity-100"
                    />
                    <div className="relative flex h-full flex-col justify-between">
                      <div className="flex items-start justify-between gap-3">
                        <span className="bg-ink-950/80 px-3 py-2 text-sm font-bold text-slate-200">
                          {product.category.name}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="bg-neon-teal px-3 py-2 text-sm font-black text-ink-950">
                            Осталось: {product.total_stock}
                          </span>
                          <FavoriteToggleButton
                            product={product}
                            compact
                            stopPropagation
                          />
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-bold text-neon-crimson">
                          {product.franchise?.name ?? "AnimeAttire"}
                        </p>
                        <h3 className="mt-2 text-2xl font-black">{product.name}</h3>
                        <div className="mt-4 flex items-center justify-between">
                          <span className="text-xl font-black">
                            {money.format(Number(product.base_price))}
                          </span>
                          <span className="translate-y-2 bg-white px-4 py-2 text-sm font-black uppercase text-ink-950 opacity-0 transition group-hover:translate-y-0 group-hover:opacity-100">
                            Открыть
                          </span>
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            ) : null}
          </section>
        </div>
      </section>
    </main>
  );
}
