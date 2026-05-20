"use client";

import { MouseEvent, useState } from "react";

import {
  addFavorite,
  removeFavorite,
  type FavoriteProductEntry,
  type Product
} from "../../lib/api";
import { useFavoritesStore } from "../../stores/favorites-store";
import { useUserStore } from "../../stores/user-store";

type FavoriteToggleButtonProps = {
  product: Product;
  className?: string;
  compact?: boolean;
  stopPropagation?: boolean;
};

export function FavoriteToggleButton({
  product,
  className = "",
  compact = false,
  stopPropagation = false
}: FavoriteToggleButtonProps) {
  const accessToken = useUserStore((state) => state.accessToken);
  const favorite = useFavoritesStore((state) =>
    state.favorites.find((item) => item.product_id === product.id)
  );
  const upsertFavorite = useFavoritesStore((state) => state.upsertFavorite);
  const removeFavoriteByProductId = useFavoritesStore(
    (state) => state.removeFavoriteByProductId
  );
  const [isPending, setIsPending] = useState(false);

  const isFavorite = Boolean(favorite);

  function redirectToRegister(nextPathname: string) {
    if (typeof window === "undefined") return;
    const url = `/register?next=${encodeURIComponent(nextPathname)}`;
    const anyWindow = window as unknown as { __APP_REDIRECT__?: (to: string) => void };
    if (typeof anyWindow.__APP_REDIRECT__ === "function") {
      anyWindow.__APP_REDIRECT__(url);
      return;
    }
    window.location.assign(url);
  }

  async function handleClick(event: MouseEvent<HTMLButtonElement>) {
    if (stopPropagation) {
      event.preventDefault();
      event.stopPropagation();
    }

    if (!accessToken) {
      const nextPath =
        typeof window !== "undefined" && window.location?.pathname
          ? window.location.pathname
          : "/";
      redirectToRegister(nextPath);
      return;
    }

    if (isPending) {
      return;
    }

    setIsPending(true);

    try {
      if (isFavorite) {
        await removeFavorite(accessToken, product.id);
        removeFavoriteByProductId(product.id);
        return;
      }

      const response = await addFavorite(accessToken, product.id);
      upsertFavorite(response as FavoriteProductEntry);
    } finally {
      setIsPending(false);
    }
  }

  const label = !accessToken
    ? `Войдите, чтобы добавить "${product.name}" в избранное`
    : isFavorite
      ? `Убрать "${product.name}" из избранного`
      : `Добавить "${product.name}" в избранное`;

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isPending}
      aria-label={label}
      title={label}
      className={`inline-flex items-center justify-center transition focus:outline-none focus:ring-2 focus:ring-white/20 disabled:cursor-not-allowed disabled:opacity-60 ${
        compact
          ? `h-10 w-10 rounded-full bg-transparent text-base ${
              isFavorite ? "text-white" : "text-slate-200 hover:text-white"
            }`
          : `h-11 min-w-11 rounded-full border border-white/15 bg-white/10 px-3 text-sm font-black uppercase text-white hover:border-white/25 hover:bg-white/15`
      } ${className}`}
    >
      <span aria-hidden="true" className="text-base leading-none">
        {isFavorite ? "♥" : "♡"}
      </span>
      {!compact ? (
        <span className="ml-2">
          {isPending ? "..." : isFavorite ? "В избранном" : "В избранное"}
        </span>
      ) : null}
    </button>
  );
}
