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
