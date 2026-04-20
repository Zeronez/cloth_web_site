"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { fetchProduct, type Product, type ProductVariant } from "../../lib/api";
import { InlineNotice, ProductDetailSkeleton } from "../loading-states";
import { ProductImagePlaceholder } from "../product-image-placeholder";
import { useCartStore } from "../../stores/cart-store";

const fallbackProduct = (slug: string): Product => ({
  id: 999,
  name: slug
    .split("-")
    .map((word) => word.slice(0, 1).toUpperCase() + word.slice(1))
    .join(" "),
  slug,
  category: { id: 1, name: "Дроп", slug: "drop", description: "" },
  franchise: { id: 1, name: "AnimeAttire", slug: "animeattire", description: "" },
  base_price: "12800.00",
  is_featured: true,
  main_image: null,
  total_stock: 12,
  description:
    "Лимитированная вещь AnimeAttire со структурным стритвир-кроем, акцентной отделкой и силуэтом для движения по ночному городу.",
  variants: [
    {
      id: 1,
      sku: `${slug}-m-black`,
      size: "M",
      color: "Black",
      stock_quantity: 4,
      price_delta: "0.00",
      price: "12800.00",
      is_active: true
    },
    {
      id: 2,
      sku: `${slug}-l-black`,
      size: "L",
      color: "Black",
      stock_quantity: 8,
      price_delta: "0.00",
      price: "12800.00",
      is_active: true
    }
  ],
  images: []
});

const money = new Intl.NumberFormat("ru-RU", {
  currency: "RUB",
  style: "currency"
});

export function ProductDetailPage({ slug }: { slug: string }) {
  const addItem = useCartStore((state) => state.addItem);
  const productQuery = useQuery({
    queryKey: ["product", slug],
    queryFn: () => fetchProduct(slug)
  });
  const isInitialLoading = productQuery.isLoading && !productQuery.data;
  const isUsingFallback = productQuery.isError && !productQuery.data;
  const product = productQuery.data ?? fallbackProduct(slug);
  const availableVariants = useMemo(
    () =>
      (product.variants ?? []).filter(
        (variant) => variant.is_active && variant.stock_quantity > 0
      ),
    [product.variants]
  );
  const [selectedVariantId, setSelectedVariantId] = useState<number | null>(null);
  const selectedVariant =
    availableVariants.find((variant) => variant.id === selectedVariantId) ??
    availableVariants[0];

  const addSelected = (variant: ProductVariant) => {
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

  return (
    <main className="min-h-screen bg-ink-950 px-4 pb-20 pt-28 text-white sm:px-6 lg:px-8">
      <section className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[1fr_0.82fr]">
        <div className="relative min-h-[620px] overflow-hidden border border-white/10 bg-white/[0.04]">
          <ProductImagePlaceholder
            label={product.category.name}
            variant="jacket"
            className="absolute inset-0"
          />
          <div className="absolute bottom-12 left-8 border border-white/10 bg-ink-950/80 px-4 py-3">
            <p className="text-sm font-bold text-slate-300">
              {product.franchise?.name ?? "AnimeAttire"}
            </p>
          </div>
        </div>

        <div>
          {isUsingFallback ? (
            <div className="mb-6">
              <InlineNotice
                title="Карточка открыта в demo-режиме"
                text="Backend API не ответил, поэтому показываем временные данные и плейсхолдер изображения."
                tone="warning"
              />
            </div>
          ) : null}

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
            <p className="text-3xl font-black">
              {money.format(Number(selectedVariant?.price ?? product.base_price))}
            </p>
            <p className="mt-2 text-sm text-slate-400">
              {selectedVariant
                ? `В наличии: ${selectedVariant.stock_quantity}, цвет: ${selectedVariant.color}`
                : "Нет в наличии"}
            </p>
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

          <button
            type="button"
            disabled={!selectedVariant}
            onClick={() => selectedVariant && addSelected(selectedVariant)}
            className="mt-8 h-14 w-full bg-neon-crimson px-6 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-slate-500 disabled:shadow-none"
          >
            Добавить выбранный размер
          </button>
        </div>
      </section>
    </main>
  );
}
