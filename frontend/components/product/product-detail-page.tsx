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
import { trackEvent } from "../../lib/analytics";
import { useCartSync } from "../../lib/use-cart-sync";
import { useFavoritesStore } from "../../stores/favorites-store";
import { useUserStore } from "../../stores/user-store";
import { FavoriteToggleButton } from "../catalog/favorite-toggle-button";
import { InlineNotice, ProductDetailSkeleton } from "../loading-states";
import { ProductMediaGallery } from "../product-media";

const money = new Intl.NumberFormat("ru-RU", {
  currency: "RUB",
  style: "currency"
});

const LOW_STOCK_THRESHOLD = 3;
const FIT_PROFILE_FIELD_LABELS: Record<string, string> = {
  height_cm: "рост",
  weight_kg: "вес",
  chest_cm: "обхват груди",
  waist_cm: "обхват талии",
  hips_cm: "обхват бёдер",
  inseam_cm: "длина по внутреннему шву",
  preferred_fit: "предпочтительная посадка",
  preferred_style: "любимый стиль",
  preferred_season: "предпочтительный сезон",
  tops_usual_size: "обычный размер верха",
  bottoms_usual_size: "обычный размер низа",
  budget_min_rub: "минимальный бюджет",
  budget_max_rub: "максимальный бюджет"
};
const FIT_RECOMMENDATION_TONE: Record<string, string> = {
  none: "border-white/10 bg-white/[0.04]",
  low: "border-neon-amber/30 bg-neon-amber/10",
  medium: "border-neon-teal/30 bg-neon-teal/10",
  high: "border-neon-crimson/30 bg-neon-crimson/10"
};

function formatMissingFitFields(fields: string[]) {
  return fields
    .map((field) => FIT_PROFILE_FIELD_LABELS[field] ?? field)
    .join(", ");
}

function availabilityText(variant: ProductVariant | null | undefined) {
  if (!variant) {
    return "Нет активных размеров";
  }

  if (variant.stock_quantity <= 0) {
    return "Нет в наличии";
  }

  if (variant.stock_quantity <= LOW_STOCK_THRESHOLD) {
    return `Заканчивается: ${variant.stock_quantity} шт., цвет: ${variant.color}`;
  }

  return `В наличии: ${variant.stock_quantity}, цвет: ${variant.color}`;
}

export function ProductDetailPage({ slug }: { slug: string }) {
  const { addItem } = useCartSync();
  const accessToken = useUserStore((state) => state.accessToken);
  const clearSession = useUserStore((state) => state.clearSession);
  const setFavorites = useFavoritesStore((state) => state.setFavorites);
  const productQuery = useQuery({
    queryKey: ["product", slug, accessToken],
    queryFn: async () => {
      try {
        return await fetchProduct(slug, accessToken);
      } catch (error) {
        if (accessToken && error instanceof ApiError && error.status === 401) {
          clearSession();
          return fetchProduct(slug);
        }

        throw error;
      }
    }
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
  const fitRecommendation = product?.fit_recommendation ?? null;
  const [trackedProductId, setTrackedProductId] = useState<number | null>(null);

  const selectableVariants = useMemo(
    () => (product?.variants ?? []).filter((variant) => variant.is_active),
    [product?.variants]
  );
  const availableVariants = useMemo(
    () => selectableVariants.filter((variant) => variant.stock_quantity > 0),
    [selectableVariants]
  );
  const [selectedVariantId, setSelectedVariantId] = useState<number | null>(null);
  const selectedVariant =
    selectableVariants.find((variant) => variant.id === selectedVariantId) ??
    availableVariants[0] ??
    selectableVariants[0] ??
    null;
  const selectedVariantInStock = Boolean(
    selectedVariant && selectedVariant.stock_quantity > 0
  );

  useEffect(() => {
    if (selectedVariantId || !fitRecommendation?.recommended_size) {
      return;
    }

    const recommendedVariant = selectableVariants.find(
      (variant) => variant.size === fitRecommendation.recommended_size
    );

    if (recommendedVariant) {
      setSelectedVariantId(recommendedVariant.id);
    }
  }, [fitRecommendation?.recommended_size, selectableVariants, selectedVariantId]);

  useEffect(() => {
    if (favoritesQuery.data) {
      setFavorites(favoritesQuery.data);
    }
  }, [favoritesQuery.data, setFavorites]);

  useEffect(() => {
    if (!product) {
      return;
    }

    if (trackedProductId === product.id) {
      return;
    }

    setTrackedProductId(product.id);
    trackEvent("product_view", {
      product_id: product.id,
      product_slug: product.slug,
      product_name: product.name
    });
  }, [product, trackedProductId]);

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
      size: variant.size,
      image: product.main_image?.url,
      imageAlt: product.main_image?.alt_text || product.name,
      productSlug: product.slug
    });
    trackEvent("add_to_cart", {
      product_id: product.id,
      product_slug: product.slug,
      variant_id: variant.id,
      size: variant.size,
      price: Number(variant.price),
      currency: "RUB"
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
                <p
                  className={`mt-2 text-sm ${
                    selectedVariantInStock ? "text-slate-400" : "text-red-200"
                  }`}
                >
                  {availabilityText(selectedVariant)}
                </p>
              </div>
              <FavoriteToggleButton product={product} compact />
            </div>
          </div>

          <div className="mt-8">
            <h2 className="text-sm font-bold text-slate-300">Выберите размер</h2>
            <div className="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-4">
              {selectableVariants.map((variant) => {
                const isOutOfStock = variant.stock_quantity <= 0;
                const isLowStock =
                  variant.stock_quantity > 0 &&
                  variant.stock_quantity <= LOW_STOCK_THRESHOLD;

                return (
                  <button
                    key={variant.id}
                    type="button"
                    onClick={() => setSelectedVariantId(variant.id)}
                    aria-pressed={selectedVariant?.id === variant.id}
                    aria-label={
                      isOutOfStock
                        ? `Размер ${variant.size}, нет в наличии`
                        : isLowStock
                          ? `Размер ${variant.size}, заканчивается`
                          : `Размер ${variant.size}, в наличии`
                    }
                    className={`h-12 border text-sm font-black transition ${
                      selectedVariant?.id === variant.id
                        ? "border-neon-crimson bg-neon-crimson text-white"
                        : isOutOfStock
                          ? "border-white/10 bg-white/[0.03] text-slate-500"
                          : isLowStock
                            ? "border-neon-amber/50 bg-neon-amber/10 text-orange-100 hover:border-neon-amber"
                            : "border-white/10 bg-white/5 text-slate-300 hover:border-white/30"
                    }`}
                  >
                    {variant.size}
                    {isOutOfStock ? " ×" : isLowStock ? " !" : ""}
                  </button>
                );
              })}
            </div>
            <div className="mt-3 flex flex-wrap gap-3 text-xs font-semibold text-slate-400">
              <span>Весь размерный ряд отображается прямо с остатками.</span>
              <span>! Заканчивается</span>
              <span>× Нет в наличии</span>
            </div>
          </div>

          {fitRecommendation ? (
            <section
              aria-label="Рекомендация по размеру"
              className={`mt-8 border p-5 ${FIT_RECOMMENDATION_TONE[fitRecommendation.confidence] ?? FIT_RECOMMENDATION_TONE.none}`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-300">
                    Рекомендация по размеру
                  </p>
                  <h2 className="mt-2 text-2xl font-black text-white">
                    {fitRecommendation.recommended_size
                      ? `Рекомендуем размер ${fitRecommendation.recommended_size}`
                      : "Подберём размер точнее после заполнения fit-профиля"}
                  </h2>
                </div>
                <span className="border border-white/10 bg-black/20 px-3 py-1 text-xs font-bold uppercase text-slate-200">
                  {fitRecommendation.confidence === "high"
                    ? "Высокая точность"
                    : fitRecommendation.confidence === "medium"
                      ? "Хорошее совпадение"
                      : fitRecommendation.confidence === "low"
                        ? "Предварительно"
                        : "Нужны данные"}
                </span>
              </div>

              <p className="mt-3 text-sm leading-6 text-slate-200">
                {fitRecommendation.summary}
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-300">
                {fitRecommendation.explanation}
              </p>

              {fitRecommendation.warnings.length > 0 ? (
                <div className="mt-4 flex flex-wrap gap-2">
                  {fitRecommendation.warnings.map((warning) => (
                    <span
                      key={warning}
                      className="border border-white/10 bg-black/20 px-2 py-1 text-xs font-semibold uppercase text-slate-200"
                    >
                      {warning === "recommended_size_out_of_stock"
                        ? "Размер заканчивается"
                        : warning === "closest_available_size_selected"
                          ? "Подобран ближайший размер"
                          : warning === "style_fit_mismatch"
                            ? "Посадка отличается от предпочтений"
                            : warning === "season_mismatch"
                              ? "Сезон не совпадает"
                              : warning === "style_mismatch"
                                ? "Стиль может не совпасть"
                                : warning === "fit_profile_incomplete"
                                  ? "Нужны дополнительные данные"
                                  : warning === "one_size_only"
                                    ? "One size"
                                    : warning}
                    </span>
                  ))}
                </div>
              ) : null}

              {!fitRecommendation.profile_ready &&
              fitRecommendation.missing_profile_fields.length > 0 ? (
                <p className="mt-3 text-xs font-semibold text-slate-300">
                  {accessToken
                    ? `Чтобы рекомендация стала точнее, добавьте в fit-профиль: ${formatMissingFitFields(
                        fitRecommendation.missing_profile_fields
                      )}.`
                    : "Войдите в аккаунт и заполните fit-профиль, чтобы получить персональную рекомендацию по размеру."}
                </p>
              ) : null}

              {fitRecommendation.outfit.items.length > 0 ? (
                <div className="mt-5 border-t border-white/10 pt-5">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-300">
                        Капсульный образ
                      </p>
                      <p className="mt-2 text-sm leading-6 text-slate-300">
                        Система собрала вещи, которые сочетаются с этой позицией.
                      </p>
                    </div>
                    {fitRecommendation.outfit.total_price ? (
                      <p className="text-sm font-semibold text-white">
                        Итого: {money.format(Number(fitRecommendation.outfit.total_price))}
                      </p>
                    ) : null}
                  </div>

                  <div className="mt-4 space-y-3">
                    {fitRecommendation.outfit.items.map((item) => (
                      <Link
                        key={item.id}
                        href={`/products/${item.slug}`}
                        className="flex items-center justify-between gap-4 border border-white/10 bg-black/10 p-3 transition hover:border-neon-teal/40 hover:bg-black/20"
                      >
                        <div>
                          <p className="text-xs font-black uppercase text-neon-teal">
                            {item.category}
                          </p>
                          <p className="mt-1 text-sm font-semibold text-white">
                            {item.name}
                          </p>
                          <p className="mt-1 text-xs leading-5 text-slate-400">
                            {item.reason}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-semibold text-white">
                            {money.format(Number(item.base_price))}
                          </p>
                          <p className="mt-1 text-xs uppercase text-slate-500">
                            К карточке
                          </p>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              ) : null}
            </section>
          ) : null}

          <div className="mt-8 grid gap-3 sm:grid-cols-[1fr_auto]">
            <button
              type="button"
              disabled={!selectedVariant || !selectedVariantInStock}
              onClick={() => selectedVariantInStock && selectedVariant && addSelected(selectedVariant)}
              className="h-14 w-full bg-neon-crimson px-6 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-slate-500 disabled:shadow-none"
            >
              {selectedVariantInStock
                ? "Добавить выбранный размер"
                : "Выбранный размер недоступен"}
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
