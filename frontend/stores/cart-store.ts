import { create } from "zustand";
import { persist } from "zustand/middleware";

export type CartItem = {
  id: string;
  name: string;
  price: number;
  size: string;
  image?: string;
  quantity: number;
};

type AddCartItemInput = Omit<CartItem, "quantity"> & {
  quantity?: number;
};

export type CartState = {
  items: CartItem[];
  isOpen: boolean;
  addItem: (item: AddCartItemInput) => void;
  removeItem: (id: string, size: string) => void;
  setItemQuantity: (id: string, size: string, quantity: number) => void;
  clearCart: () => void;
  openCart: () => void;
  closeCart: () => void;
  toggleCart: () => void;
};

const itemKey = (id: string, size: string) => `${id}:${size}`;

export const useCartStore = create<CartState>()(
  persist(
    (set) => ({
      items: [],
      isOpen: false,
      addItem: (item) =>
        set((state) => {
          const quantity = item.quantity ?? 1;
          const nextKey = itemKey(item.id, item.size);
          const existing = state.items.find(
            (cartItem) => itemKey(cartItem.id, cartItem.size) === nextKey
          );

          if (existing) {
            return {
              isOpen: true,
              items: state.items.map((cartItem) =>
                itemKey(cartItem.id, cartItem.size) === nextKey
                  ? { ...cartItem, quantity: cartItem.quantity + quantity }
                  : cartItem
              )
            };
          }

          return {
            isOpen: true,
            items: [...state.items, { ...item, quantity }]
          };
        }),
      removeItem: (id, size) =>
        set((state) => ({
          items: state.items.filter(
            (item) => itemKey(item.id, item.size) !== itemKey(id, size)
          )
        })),
      setItemQuantity: (id, size, quantity) =>
        set((state) => ({
          items:
            quantity <= 0
              ? state.items.filter(
                  (item) => itemKey(item.id, item.size) !== itemKey(id, size)
                )
              : state.items.map((item) =>
                  itemKey(item.id, item.size) === itemKey(id, size)
                    ? { ...item, quantity }
                    : item
                )
        })),
      clearCart: () => set({ items: [] }),
      openCart: () => set({ isOpen: true }),
      closeCart: () => set({ isOpen: false }),
      toggleCart: () => set((state) => ({ isOpen: !state.isOpen }))
    }),
    {
      name: "animeattire-cart"
    }
  )
);

export const selectCartCount = (state: CartState) =>
  state.items.reduce((total, item) => total + item.quantity, 0);

export const selectCartSubtotal = (state: CartState) =>
  state.items.reduce((total, item) => total + item.price * item.quantity, 0);
