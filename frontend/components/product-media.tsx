"use client";

import { useEffect, useMemo, useState } from "react";

import type { Product, ProductImage } from "../lib/api";
import { ProductImagePlaceholder } from "./product-image-placeholder";

type PlaceholderVariant = "jacket" | "hoodie" | "pants";

type MediaAsset = {
  id: string;
  alt: string;
  type: "image" | "video" | "placeholder";
  url: string | null;
  placeholderVariant: PlaceholderVariant;
};

const videoPattern = /\.(mp4|webm|ogg|mov)(?:$|[?#])/i;

function isVideoUrl(url: string) {
  return videoPattern.test(url);
}

function toMediaAsset(
  image: ProductImage,
  fallbackLabel: string,
  placeholderVariant: PlaceholderVariant
): MediaAsset {
  const alt = image.alt_text?.trim() || fallbackLabel;

  return {
    id: `media-${image.id}`,
    alt,
    type: isVideoUrl(image.url) ? "video" : "image",
    url: image.url,
    placeholderVariant
  };
}

export function buildProductMediaAssets(
  product: Pick<Product, "name" | "main_image" | "images">,
  placeholderVariant: PlaceholderVariant = "jacket"
) {
  const assets: MediaAsset[] = [];
  const seen = new Set<string>();

  const pushImage = (image: ProductImage | null | undefined) => {
    if (!image?.url || seen.has(image.url)) {
      return;
    }

    seen.add(image.url);
    assets.push(toMediaAsset(image, product.name, placeholderVariant));
  };

  pushImage(product.main_image);
  for (const image of product.images ?? []) {
    pushImage(image);
  }

  if (assets.length > 0) {
    return assets;
  }

  return [
    {
      id: "placeholder",
      alt: product.name,
      type: "placeholder" as const,
      url: null,
      placeholderVariant
    }
  ];
}

function ProductMediaSurface({
  asset,
  label,
  className = "",
  mediaClassName = "",
  priority = false
}: {
  asset: MediaAsset;
  label: string;
  className?: string;
  mediaClassName?: string;
  priority?: boolean;
}) {
  if (asset.type === "placeholder" || !asset.url) {
    return (
      <ProductImagePlaceholder
        label={label}
        variant={asset.placeholderVariant}
        className={className}
      />
    );
  }

  if (asset.type === "video") {
    return (
      <div className={`bg-ink-900 ${className}`}>
        <video
          aria-label={asset.alt}
          className={`h-full w-full object-cover ${mediaClassName}`}
          autoPlay
          loop
          muted
          playsInline
          preload="metadata"
          src={asset.url}
        />
      </div>
    );
  }

  return (
    <div className={`bg-ink-900 ${className}`}>
      {/* Dynamic product media can come from backend/S3 hosts that are not fixed at build time. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        alt={asset.alt}
        className={`h-full w-full object-cover ${mediaClassName}`}
        loading={priority ? "eager" : "lazy"}
        src={asset.url}
      />
    </div>
  );
}

function ProductMediaLightbox({
  asset,
  label,
  open,
  onClose
}: {
  asset: MediaAsset;
  label: string;
  open: boolean;
  onClose: () => void;
}) {
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    if (!open) return;
    setZoom(1);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose, open]);

  if (!open) return null;

  const isZoomed = zoom > 1;

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label={`Просмотр медиа для ${label}`}
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-5xl overflow-hidden rounded-2xl border border-white/10 bg-ink-950 shadow-[0_26px_90px_rgba(0,0,0,0.70)]"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between gap-3 border-b border-white/10 bg-white/[0.04] px-4 py-3">
          <div className="min-w-0">
            <div className="truncate text-sm font-black text-white">{label}</div>
            <div className="truncate text-xs font-semibold text-slate-400">
              {asset.alt}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setZoom((value) => Math.min(3, Number((value + 0.25).toFixed(2))))}
              className="h-9 rounded-full border border-white/15 bg-white/5 px-4 text-xs font-black uppercase tracking-[0.18em] text-white transition hover:border-white/30 hover:bg-white/10"
            >
              +
            </button>
            <button
              type="button"
              onClick={() => setZoom((value) => Math.max(1, Number((value - 0.25).toFixed(2))))}
              className="h-9 rounded-full border border-white/15 bg-white/5 px-4 text-xs font-black uppercase tracking-[0.18em] text-white transition hover:border-white/30 hover:bg-white/10"
            >
              −
            </button>
            <button
              type="button"
              onClick={() => setZoom(1)}
              disabled={!isZoomed}
              className="h-9 rounded-full border border-white/15 bg-white/5 px-4 text-xs font-black uppercase tracking-[0.18em] text-white transition hover:border-white/30 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-60"
            >
              1:1
            </button>
            <button
              type="button"
              onClick={onClose}
              className="h-9 rounded-full border border-white/15 bg-white/5 px-4 text-xs font-black uppercase tracking-[0.18em] text-white transition hover:border-white/30 hover:bg-white/10"
            >
              Закрыть
            </button>
          </div>
        </div>

        <div
          className="relative grid max-h-[78vh] min-h-[420px] place-items-center overflow-auto bg-black/20"
          onWheel={(event) => {
            if (!event.ctrlKey && !event.metaKey) return;
            event.preventDefault();
            const delta = event.deltaY > 0 ? -0.25 : 0.25;
            setZoom((value) => {
              const next = Math.max(1, Math.min(3, value + delta));
              return Number(next.toFixed(2));
            });
          }}
        >
          {asset.type === "video" && asset.url ? (
            <video
              aria-label={asset.alt}
              className="h-full w-full max-h-[78vh] object-contain"
              controls
              playsInline
              preload="metadata"
              src={asset.url}
            />
          ) : asset.type === "image" && asset.url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              alt={asset.alt}
              src={asset.url}
              className={`max-h-[78vh] max-w-full object-contain transition ${
                isZoomed ? "cursor-zoom-out" : "cursor-zoom-in"
              }`}
              style={{ transform: `scale(${zoom})`, transformOrigin: "center" }}
              onClick={() => setZoom((value) => (value > 1 ? 1 : 2))}
              draggable={false}
            />
          ) : (
            <div className="p-12">
              <ProductImagePlaceholder label={label} variant={asset.placeholderVariant} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function CatalogProductMedia({
  product,
  placeholderVariant = "jacket"
}: {
  product: Pick<Product, "name" | "main_image" | "images">;
  placeholderVariant?: PlaceholderVariant;
}) {
  const assets = useMemo(
    () => buildProductMediaAssets(product, placeholderVariant),
    [placeholderVariant, product]
  );
  const primaryAsset = assets[0];
  const hoverAsset = assets[1] ?? assets[0];

  return (
    <>
      <ProductMediaSurface
        asset={primaryAsset}
        label={product.name}
        className="absolute inset-0 opacity-90 transition duration-500 group-hover:scale-[1.02] group-hover:opacity-0"
        mediaClassName="transition duration-700 group-hover:scale-[1.04]"
        priority
      />
      <ProductMediaSurface
        asset={hoverAsset}
        label={product.name}
        className="absolute inset-0 opacity-0 transition duration-500 group-hover:opacity-100"
        mediaClassName="transition duration-700 group-hover:scale-[1.04]"
      />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.1),transparent_38%),linear-gradient(180deg,transparent,rgba(2,6,23,0.72))]" />
    </>
  );
}

export function ProductMediaGallery({
  product,
  placeholderVariant = "jacket"
}: {
  product: Pick<Product, "name" | "main_image" | "images">;
  placeholderVariant?: PlaceholderVariant;
}) {
  const assets = useMemo(
    () => buildProductMediaAssets(product, placeholderVariant),
    [placeholderVariant, product]
  );
  const [selectedAssetId, setSelectedAssetId] = useState(assets[0]?.id ?? "placeholder");
  const [isLightboxOpen, setIsLightboxOpen] = useState(false);

  useEffect(() => {
    setSelectedAssetId(assets[0]?.id ?? "placeholder");
  }, [assets]);

  const selectedAsset =
    assets.find((asset) => asset.id === selectedAssetId) ?? assets[0];

  return (
    <div className="grid gap-4 lg:grid-cols-[96px_minmax(0,1fr)]">
      <div className="order-2 flex gap-3 overflow-x-auto lg:order-1 lg:flex-col">
        {assets.map((asset, index) => (
          <button
            key={asset.id}
            type="button"
            onClick={() => setSelectedAssetId(asset.id)}
            aria-pressed={selectedAsset.id === asset.id}
            aria-label={`Показать медиа ${index + 1} для ${product.name}`}
            className={`relative h-24 min-w-24 overflow-hidden border transition ${
              selectedAsset.id === asset.id
                ? "border-neon-crimson bg-neon-crimson/10"
                : "border-white/10 bg-white/5 hover:border-white/30"
            }`}
          >
            <ProductMediaSurface
              asset={asset}
              label={product.name}
              className="absolute inset-0"
            />
          </button>
        ))}
      </div>

      <div className="order-1 relative min-h-[620px] overflow-hidden border border-white/10 bg-white/[0.04] lg:order-2">
        <button
          type="button"
          onClick={() => {
            if (selectedAsset.type === "placeholder") return;
            setIsLightboxOpen(true);
          }}
          className="absolute inset-0 cursor-zoom-in text-left"
          aria-label={`Открыть фото товара ${product.name} для просмотра`}
        >
          <ProductMediaSurface
            asset={selectedAsset}
            label={product.name}
            className="absolute inset-0"
            mediaClassName="transition duration-700 hover:scale-[1.02]"
            priority
          />
        </button>
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,transparent_0%,rgba(2,6,23,0.14)_48%,rgba(2,6,23,0.82)_100%)]" />
        <div className="pointer-events-none absolute bottom-6 left-6 flex items-center gap-3">
          <span className="border border-white/10 bg-ink-950/80 px-4 py-3 text-xs font-black uppercase tracking-[0.24em] text-white">
            {selectedAsset.type === "video" ? "Motion" : "Lookbook"}
          </span>
          <span className="border border-white/10 bg-white/10 px-4 py-3 text-sm font-semibold text-slate-200">
            {selectedAsset.alt}
          </span>
        </div>
      </div>

      <ProductMediaLightbox
        asset={selectedAsset}
        label={product.name}
        open={isLightboxOpen}
        onClose={() => setIsLightboxOpen(false)}
      />
    </div>
  );
}
