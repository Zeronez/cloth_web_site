"use client";

import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";

import { selectCartSubtotal, useCartStore } from "../stores/cart-store";
import { ProductImagePlaceholder } from "./product-image-placeholder";

const currencyFormatter = new Intl.NumberFormat("ru-RU", {
  currency: "RUB",
  style: "currency"
});

export function CartDrawer() {
  const items = useCartStore((state) => state.items);
  const isOpen = useCartStore((state) => state.isOpen);
  const closeCart = useCartStore((state) => state.closeCart);
  const clearCart = useCartStore((state) => state.clearCart);
  const removeItem = useCartStore((state) => state.removeItem);
  const setItemQuantity = useCartStore((state) => state.setItemQuantity);
  const subtotal = useCartStore(selectCartSubtotal);

  return (
    <AnimatePresence>
      {isOpen ? (
        <>
          <motion.button
            type="button"
            aria-label="Закрыть корзину"
            className="fixed inset-0 z-50 cursor-default bg-black/60 backdrop-blur-sm"
            onClick={closeCart}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />
          <motion.aside
            className="fixed right-0 top-0 z-50 flex h-dvh w-full max-w-md flex-col border-l border-white/10 bg-ink-950 text-white shadow-[0_0_80px_rgba(0,0,0,0.52)]"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 260 }}
            aria-label="Корзина"
          >
            <div className="flex items-center justify-between border-b border-white/10 px-5 py-5">
              <div>
                <p className="text-xs font-semibold uppercase text-neon-teal">
                  Корзина
                </p>
                <h2 className="mt-1 text-2xl font-black">Текущий набор</h2>
              </div>
              <button
                type="button"
                onClick={closeCart}
                className="grid h-10 w-10 place-items-center border border-white/15 bg-white/10 text-xl leading-none transition hover:border-neon-crimson hover:text-neon-crimson focus:outline-none focus:ring-2 focus:ring-neon-teal"
                aria-label="Закрыть корзину"
              >
                x
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-6">
              {items.length === 0 ? (
                <div className="grid h-full place-items-center text-center">
                  <div>
                    <div className="mx-auto mb-6 h-28 w-28 border border-dashed border-white/20 bg-white/5" />
                    <h3 className="text-xl font-bold">Корзина пока пуста</h3>
                    <p className="mt-2 text-sm leading-6 text-slate-400">
                      Добавьте вещь из дропа, чтобы собрать заказ.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {items.map((item) => (
                    <article
                      key={`${item.id}-${item.size}`}
                      className="grid grid-cols-[72px_1fr] gap-4 border border-white/10 bg-white/[0.04] p-3"
                    >
                      <ProductImagePlaceholder
                        label="AA"
                        variant="cart"
                        className="h-[88px]"
                      />
                      <div>
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <h3 className="font-bold leading-tight">{item.name}</h3>
                            <p className="mt-1 text-xs uppercase text-slate-400">
                              Размер {item.size}
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={() => removeItem(item.id, item.size)}
                            className="text-sm text-slate-400 transition hover:text-neon-crimson"
                          >
                            Удалить
                          </button>
                        </div>
                        <div className="mt-4 flex items-center justify-between">
                          <div className="flex items-center border border-white/10">
                            <button
                              type="button"
                              className="grid h-8 w-8 place-items-center hover:bg-white/10"
                              onClick={() =>
                                setItemQuantity(
                                  item.id,
                                  item.size,
                                  item.quantity - 1
                                )
                              }
                              aria-label={`Уменьшить количество ${item.name}`}
                            >
                              -
                            </button>
                            <span className="grid h-8 w-9 place-items-center text-sm font-bold">
                              {item.quantity}
                            </span>
                            <button
                              type="button"
                              className="grid h-8 w-8 place-items-center hover:bg-white/10"
                              onClick={() =>
                                setItemQuantity(
                                  item.id,
                                  item.size,
                                  item.quantity + 1
                                )
                              }
                              aria-label={`Увеличить количество ${item.name}`}
                            >
                              +
                            </button>
                          </div>
                          <p className="font-bold">
                            {currencyFormatter.format(item.price * item.quantity)}
                          </p>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </div>

            <div className="border-t border-white/10 p-5">
              <div className="flex items-center justify-between text-sm text-slate-300">
                <span>Итого</span>
                <strong className="text-xl text-white">
                  {currencyFormatter.format(subtotal)}
                </strong>
              </div>
              {items.length > 0 ? (
                <Link
                  href="/checkout"
                  role="button"
                  onClick={closeCart}
                  className="mt-5 flex h-12 w-full items-center justify-center bg-neon-crimson px-5 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950"
                >
                  Оформить заказ
                </Link>
              ) : (
                <button
                  type="button"
                  className="mt-5 h-12 w-full cursor-not-allowed bg-white/10 px-5 text-sm font-black uppercase text-slate-500 shadow-none"
                  disabled
                >
                  Оформить заказ
                </button>
              )}
              {items.length > 0 ? (
                <button
                  type="button"
                  onClick={clearCart}
                  className="mt-3 h-10 w-full text-sm font-semibold text-slate-400 transition hover:text-white"
                >
                  Очистить корзину
                </button>
              ) : null}
            </div>
          </motion.aside>
        </>
      ) : null}
    </AnimatePresence>
  );
}
