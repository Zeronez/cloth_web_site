"use client";

import { useCallback, useState } from "react";

import { type AddCartItemInput, type CartItem, useCartStore } from "../stores/cart-store";
import { useUserStore } from "../stores/user-store";
import { ApiError } from "./api";
import {
  addServerCartVariant,
  clearServerCart,
  fetchServerCartItems,
  getVariantId,
  removeServerCartVariant,
  updateServerCartVariantQuantity
} from "./cart-sync";

export function useCartSync() {
  const accessToken = useUserStore((state) => state.accessToken);
  const clearSession = useUserStore((state) => state.clearSession);
  const items = useCartStore((state) => state.items);
  const setItems = useCartStore((state) => state.setItems);
  const addItemLocal = useCartStore((state) => state.addItem);
  const removeItemLocal = useCartStore((state) => state.removeItem);
  const setItemQuantityLocal = useCartStore((state) => state.setItemQuantity);
  const clearCartLocal = useCartStore((state) => state.clearCart);
  const openCart = useCartStore((state) => state.openCart);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);

  const handleAuthError = useCallback(
    (error: unknown) => {
      if (error instanceof ApiError && error.status === 401) {
        clearSession();
      }
    },
    [clearSession]
  );

  const refreshCart = useCallback(async () => {
    if (!accessToken) {
      return;
    }

    setIsSyncing(true);
    setSyncError(null);

    try {
      const nextItems = await fetchServerCartItems(accessToken);
      setItems(nextItems);
    } catch (error) {
      handleAuthError(error);
      setSyncError(
        error instanceof Error
          ? error.message
          : "Не удалось синхронизировать корзину."
      );
    } finally {
      setIsSyncing(false);
    }
  }, [accessToken, handleAuthError, setItems]);

  const addItem = useCallback(
    async (item: AddCartItemInput) => {
      const variantId = getVariantId(item.id);

      if (!accessToken || variantId === null) {
        addItemLocal(item);
        return;
      }

      setIsSyncing(true);
      setSyncError(null);

      try {
        const nextItems = await addServerCartVariant(
          accessToken,
          variantId,
          item.quantity ?? 1
        );
        setItems(nextItems);
        openCart();
      } catch (error) {
        handleAuthError(error);
        setSyncError(
          error instanceof Error
            ? error.message
            : "Не удалось добавить товар в корзину."
        );
      } finally {
        setIsSyncing(false);
      }
    },
    [accessToken, addItemLocal, handleAuthError, openCart, setItems]
  );

  const removeItem = useCallback(
    async (item: CartItem) => {
      if (!accessToken || !item.serverItemId) {
        removeItemLocal(item.id, item.size);
        return;
      }

      setIsSyncing(true);
      setSyncError(null);

      try {
        const nextItems = await removeServerCartVariant(accessToken, item.serverItemId);
        setItems(nextItems);
      } catch (error) {
        handleAuthError(error);
        setSyncError(
          error instanceof Error
            ? error.message
            : "Не удалось удалить товар из корзины."
        );
      } finally {
        setIsSyncing(false);
      }
    },
    [accessToken, handleAuthError, removeItemLocal, setItems]
  );

  const setItemQuantity = useCallback(
    async (item: CartItem, quantity: number) => {
      if (!accessToken || !item.serverItemId) {
        setItemQuantityLocal(item.id, item.size, quantity);
        return;
      }

      if (quantity <= 0) {
        await removeItem(item);
        return;
      }

      setIsSyncing(true);
      setSyncError(null);

      try {
        const nextItems = await updateServerCartVariantQuantity(
          accessToken,
          item.serverItemId,
          quantity
        );
        setItems(nextItems);
      } catch (error) {
        handleAuthError(error);
        setSyncError(
          error instanceof Error
            ? error.message
            : "Не удалось обновить количество товара."
        );
      } finally {
        setIsSyncing(false);
      }
    },
    [accessToken, handleAuthError, removeItem, setItemQuantityLocal, setItems]
  );

  const clearCart = useCallback(async () => {
    if (!accessToken || items.some((item) => !item.serverItemId)) {
      clearCartLocal();
      return;
    }

    setIsSyncing(true);
    setSyncError(null);

    try {
      const nextItems = await clearServerCart(accessToken, items);
      setItems(nextItems);
    } catch (error) {
      handleAuthError(error);
      setSyncError(
        error instanceof Error
          ? error.message
          : "Не удалось очистить корзину."
      );
    } finally {
      setIsSyncing(false);
    }
  }, [accessToken, clearCartLocal, handleAuthError, items, setItems]);

  return {
    accessToken,
    isSyncing,
    syncError,
    addItem,
    removeItem,
    setItemQuantity,
    clearCart,
    refreshCart
  };
}
