import {
  addCartItem,
  deleteCartItem,
  fetchCart,
  updateCartItemQuantity,
  type ServerCart,
  type ServerCartItem
} from "./api";
import type { CartItem } from "../stores/cart-store";

function toAmount(value: string | number | null | undefined) {
  const amount = Number(value ?? 0);
  return Number.isFinite(amount) ? amount : 0;
}

export function toLocalCartItem(item: ServerCartItem): CartItem {
  return {
    id: String(item.variant.id),
    serverItemId: item.id,
    name: item.product.name,
    price: toAmount(item.unit_price),
    size: item.variant.size,
    image: undefined,
    quantity: item.quantity
  };
}

export function toLocalCartItems(cart: ServerCart) {
  return cart.items.map(toLocalCartItem);
}

export function getVariantId(value: string) {
  const variantId = Number(value);
  return Number.isInteger(variantId) && variantId > 0 ? variantId : null;
}

function getMergeableGuestQuantities(items: CartItem[]) {
  const quantities = new Map<number, number>();
  const skippedItems: CartItem[] = [];

  for (const item of items) {
    const variantId = getVariantId(item.id);

    if (variantId === null) {
      skippedItems.push(item);
      continue;
    }

    quantities.set(variantId, (quantities.get(variantId) ?? 0) + item.quantity);
  }

  return { quantities, skippedItems };
}

export async function fetchServerCartItems(token: string) {
  const cart = await fetchCart(token);
  return toLocalCartItems(cart);
}

export async function addServerCartVariant(
  token: string,
  variantId: number,
  quantity: number
) {
  const cart = await addCartItem(token, variantId, quantity);
  return toLocalCartItems(cart);
}

export async function updateServerCartVariantQuantity(
  token: string,
  serverItemId: number,
  quantity: number
) {
  const cart = await updateCartItemQuantity(token, serverItemId, quantity);
  return toLocalCartItems(cart);
}

export async function removeServerCartVariant(token: string, serverItemId: number) {
  const cart = await deleteCartItem(token, serverItemId);
  return toLocalCartItems(cart);
}

export async function clearServerCart(token: string, items: CartItem[]) {
  let currentItems = items;

  for (const item of items) {
    if (!item.serverItemId) {
      continue;
    }

    currentItems = await removeServerCartVariant(token, item.serverItemId);
  }

  return currentItems;
}

export async function mergeGuestCartIntoServer(token: string, items: CartItem[]) {
  const { quantities, skippedItems } = getMergeableGuestQuantities(items);
  const serverCart = await fetchCart(token);
  const serverItemsByVariant = new Map(
    serverCart.items.map((item) => [item.variant.id, item])
  );

  for (const [variantId, guestQuantity] of quantities) {
    const serverItem = serverItemsByVariant.get(variantId);

    if (!serverItem) {
      await addCartItem(token, variantId, guestQuantity);
      continue;
    }

    await updateCartItemQuantity(
      token,
      serverItem.id,
      serverItem.quantity + guestQuantity
    );
  }

  return {
    items: await fetchServerCartItems(token),
    skippedItems
  };
}
