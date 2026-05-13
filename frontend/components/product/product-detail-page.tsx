"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  ApiError,
  fetchFavorites,
  fetchProduct,
  type ProductVariant
} from "../../lib/api";
import { useCartStore } from "../../stores/cart-store";
import { useFavoritesStore } from "../../stores/favorites-store";
import { useUserStore } from "../../stores/user-store";
import { FavoriteToggleButton } from "../catalog/favorite-toggle-button";
import { InlineNotice, ProductDetailSkeleton } from "../loading-states";
import { ProductMediaGallery } from "../product-media";

const money = new Intl.NumberFormat("ru-RU", {
  currency: "RUB",
  style: "currency"
});

export function ProductDetailPage({ slug }: { slug: string }) {
  const addItem = useCartStore((state) => state.addItem);
  const accessToken = useUserStore((state) => state.accessToken);
  const clearSession = useUserStore((state) => state.clearSession);
  const setFavorites = useFavoritesStore((state) => state.setFavorites);
  const productQuery = useQuery({
    queryKey: ["product", slug],
    queryFn: () => fetchProduct(slug)
  });
  const favoritesQuery = useQuery({
    queryKey: ["favorites", accessToken, slug],
    enabled: Boolean(accessToken),
    queryFn: () => fetchFavorites(accessToken ?? ""),
    retry: false
  });

  const isInitialLoading = productQuery.isLoading && !productQuery.data;
  const isMissingProduct =
    productQuery.error instanceof ApiError && productQuery.error.status === 404;
  const hasLoadError = productQuery.isError && !productQuery.data && !isMissingProduct;
  const product = productQuery.data ?? null;

  const availableVariants = useMemo(
    () =>
      (product?.variants ?? []).filter(
        (variant) => variant.is_active && variant.stock_quantity > 0
      ),
    [product?.variants]
  );
  const [selectedVariantId, setSelectedVariantId] = useState<number | null>(null);
  const selectedVariant =
    availableVariants.find((variant) => variant.id === selectedVariantId) ??
    availableVariants[0];

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

  const addSelected = (variant: ProductVariant) => {
    if (!product) {
      return;
    }

    addItem({
      id: String(variant.id),
      name: product.name,
      price: Number(variant.price),
      size: variant.size
    });
  };

  if (isInitialLoading) {
    return <ProductDetailSkeleton />;
  }

  if (isMissingProduct) {
    return (
      <main className="min-h-screen bg-ink-950 px-4 pb-20 pt-28 text-white sm:px-6 lg:px-8">
        <section className="mx-auto max-w-3xl border border-white/10 bg-white/[0.04] p-8">
          <InlineNotice
            title="Товар недоступен"
            text="Эта позиция снята с публикации или ее больше нет в каталоге."
            tone="warning"
          />
          <div className="mt-6">
            <Link
              href="/catalog"
              className="text-sm font-bold text-slate-300 transition hover:text-white"
            >
              Назад в каталог
            </Link>
          </div>
        </section>
      </main>
    );
  }

  if (hasLoadError || !product) {
    return (
      <main className="min-h-screen bg-ink-950 px-4 pb-20 pt-28 text-white sm:px-6 lg:px-8">
        <section className="mx-auto max-w-3xl border border-red-400/30 bg-red-500/10 p-8">
          <InlineNotice
            title="Карточка товара временно недоступна"
            text="Не удалось загрузить данные товара из API. Попробуйте открыть страницу позже."
            tone="warning"
          />
          <div className="mt-6">
            <Link
              href="/catalog"
              className="text-sm font-bold text-slate-300 transition hover:text-white"
            >
              Назад в каталог
            </Link>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-ink-950 px-4 pb-20 pt-28 text-white sm:px-6 lg:px-8">
      <section className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[1fr_0.82fr]">
        <ProductMediaGallery product={product} placeholderVariant="jacket" />

        <div>
          <Link
            href="/catalog"
            className="text-sm font-bold text-slate-300 transition hover:text-white"
          >
            Назад в каталог
          </Link>
          <p className="mt-8 text-sm font-black uppercase text-neon-teal">
            {product.category.name}
          </p>
          <h1 className="mt-3 text-4xl font-black sm:text-6xl">{product.name}</h1>
          <p className="mt-6 text-lg leading-8 text-slate-300">
            {product.description}
          </p>

          <div className="mt-8 border-y border-white/10 py-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-3xl font-black">
                  {money.format(Number(selectedVariant?.price ?? product.base_price))}
                </p>
                <p className="mt-2 text-sm text-slate-400">
                  {selectedVariant
                    ? `В наличии: ${selectedVariant.stock_quantity}, цвет: ${selectedVariant.color}`
                    : "Нет в наличии"}
                </p>
              </div>
              <FavoriteToggleButton product={product} compact />
            </div>
          </div>

          <div className="mt-8">
            <h2 className="text-sm font-bold text-slate-300">Выберите размер</h2>
            <div className="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-4">
              {availableVariants.map((variant) => (
                <button
                  key={variant.id}
                  type="button"
                  onClick={() => setSelectedVariantId(variant.id)}
                  className={`h-12 border text-sm font-black transition ${
                    selectedVariant?.id === variant.id
                      ? "border-neon-crimson bg-neon-crimson text-white"
                      : "border-white/10 bg-white/5 text-slate-300 hover:border-white/30"
                  }`}
                >
                  {variant.size}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-8 grid gap-3 sm:grid-cols-[1fr_auto]">
            <button
              type="button"
              disabled={!selectedVariant}
              onClick={() => selectedVariant && addSelected(selectedVariant)}
              className="h-14 w-full bg-neon-crimson px-6 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-slate-500 disabled:shadow-none"
            >
              Добавить выбранный размер
            </button>
            <div className="sm:justify-self-end">
              <FavoriteToggleButton product={product} />
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
