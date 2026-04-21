import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { FavoriteProductEntry } from "../lib/api";

type FavoritesState = {
  favorites: FavoriteProductEntry[];
  setFavorites: (favorites: FavoriteProductEntry[]) => void;
  upsertFavorite: (favorite: FavoriteProductEntry) => void;
  removeFavoriteByProductId: (productId: number) => void;
  clearFavorites: () => void;
};

export const useFavoritesStore = create<FavoritesState>()(
  persist(
    (set) => ({
      favorites: [],
      setFavorites: (favorites) => set({ favorites }),
      upsertFavorite: (favorite) =>
        set((state) => {
          const existingIndex = state.favorites.findIndex(
            (item) => item.product_id === favorite.product_id
          );

          if (existingIndex === -1) {
            return { favorites: [favorite, ...state.favorites] };
          }

          const nextFavorites = [...state.favorites];
          nextFavorites[existingIndex] = favorite;

          return { favorites: nextFavorites };
        }),
      removeFavoriteByProductId: (productId) =>
        set((state) => ({
          favorites: state.favorites.filter(
            (favorite) => favorite.product_id !== productId
          )
        })),
      clearFavorites: () => set({ favorites: [] })
    }),
    {
      name: "animeattire-favorites"
    }
  )
);
