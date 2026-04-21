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

  async function handleClick(event: MouseEvent<HTMLButtonElement>) {
    if (stopPropagation) {
      event.preventDefault();
      event.stopPropagation();
    }

    if (!accessToken || isPending) {
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

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={!accessToken || isPending}
      className={`inline-flex items-center justify-center border transition focus:outline-none focus:ring-2 focus:ring-neon-teal disabled:cursor-not-allowed disabled:opacity-60 ${
        compact ? "h-10 w-10 text-sm" : "h-11 min-w-11 px-3 text-sm font-black uppercase"
      } ${
        isFavorite
          ? "border-neon-crimson bg-neon-crimson text-white shadow-neon-crimson"
          : "border-white/15 bg-white/10 text-white hover:border-neon-crimson/70 hover:bg-neon-crimson/10"
      } ${className}`}
      aria-label={
        !accessToken
          ? `Войдите, чтобы добавить "${product.name}" в избранное`
          : isFavorite
            ? `Убрать "${product.name}" из избранного`
            : `Добавить "${product.name}" в избранное`
      }
      title={
        !accessToken
          ? "Войдите, чтобы использовать избранное"
          : isFavorite
            ? "Убрать из избранного"
            : "Добавить в избранное"
      }
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
