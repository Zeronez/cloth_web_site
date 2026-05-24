"use client";

import { useEffect } from "react";

import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";

import { useCartSync } from "../lib/use-cart-sync";
import { selectCartSubtotal, useCartStore } from "../stores/cart-store";
import { ProductImagePlaceholder } from "./product-image-placeholder";

const currencyFormatter = new Intl.NumberFormat("ru-RU", {
  currency: "RUB",
  style: "currency"
});

function CartItemMedia({
  image,
  imageAlt,
  name
}: {
  image?: string;
  imageAlt?: string;
  name: string;
}) {
  if (image) {
    return <img src={image} alt={imageAlt ?? name} className="h-[88px] w-full object-cover" />;
  }

  return <ProductImagePlaceholder label="AA" variant="cart" className="h-[88px]" />;
}

export function CartDrawer() {
  const items = useCartStore((state) => state.items);
  const isOpen = useCartStore((state) => state.isOpen);
  const closeCart = useCartStore((state) => state.closeCart);
  const subtotal = useCartStore(selectCartSubtotal);
  const {
    accessToken,
    clearCart,
    isSyncing,
    refreshCart,
    removeItem,
    setItemQuantity,
    syncError
  } = useCartSync();

  useEffect(() => {
    if (!isOpen || !accessToken || items.length > 0) {
      return;
    }

    void refreshCart();
  }, [accessToken, isOpen, items.length, refreshCart]);

  const handleDecreaseQuantity = async (
    item: (typeof items)[number]
  ) => {
    await setItemQuantity(item, item.quantity - 1);
  };

  const handleIncreaseQuantity = async (
    item: (typeof items)[number]
  ) => {
    await setItemQuantity(item, item.quantity + 1);
  };

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
              {syncError ? (
                <div className="mb-4 border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
                  <p className="font-semibold">Не удалось обновить корзину.</p>
                  <p className="mt-1 text-red-100/90">{syncError}</p>
                  {accessToken ? (
                    <button
                      type="button"
                      onClick={() => void refreshCart()}
                      className="mt-3 text-sm font-semibold text-white transition hover:text-neon-teal"
                    >
                      Повторить
                    </button>
                  ) : null}
                </div>
              ) : null}

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
                      {item.productSlug ? (
                        <Link
                          href={`/products/${item.productSlug}`}
                          onClick={closeCart}
                          className="overflow-hidden border border-white/10 bg-black/20 transition hover:border-white/25"
                        >
                          <CartItemMedia image={item.image} imageAlt={item.imageAlt} name={item.name} />
                        </Link>
                      ) : (
                        <div className="overflow-hidden border border-white/10 bg-black/20">
                          <CartItemMedia image={item.image} imageAlt={item.imageAlt} name={item.name} />
                        </div>
                      )}
                      <div>
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            {item.productSlug ? (
                              <Link
                                href={`/products/${item.productSlug}`}
                                onClick={closeCart}
                                className="font-bold leading-tight transition hover:text-neon-teal"
                              >
                                {item.name}
                              </Link>
                            ) : (
                              <h3 className="font-bold leading-tight">{item.name}</h3>
                            )}
                            <p className="mt-1 text-xs uppercase text-slate-400">
                              Размер {item.size}
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={() => void removeItem(item)}
                            disabled={isSyncing}
                            className="text-sm text-slate-400 transition hover:text-neon-crimson disabled:cursor-not-allowed disabled:opacity-60"
                          >
                            Удалить
                          </button>
                        </div>
                        <div className="mt-4 flex items-center justify-between gap-3">
                          <div
                            className="flex items-center border border-white/10"
                            role="group"
                            aria-label={`Количество товара ${item.name}, размер ${item.size}`}
                          >
                            <button
                              type="button"
                              className="grid h-8 w-8 place-items-center transition hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-neon-teal disabled:cursor-not-allowed disabled:opacity-60"
                              onClick={() => void handleDecreaseQuantity(item)}
                              disabled={isSyncing}
                              aria-label={
                                item.quantity === 1
                                  ? `Удалить ${item.name} из корзины`
                                  : `Уменьшить количество ${item.name}`
                              }
                            >
                              -
                            </button>
                            <span
                              className="grid h-8 min-w-10 place-items-center px-2 text-sm font-bold tabular-nums"
                              aria-live="polite"
                              aria-atomic="true"
                            >
                              {item.quantity}
                            </span>
                            <button
                              type="button"
                              className="grid h-8 w-8 place-items-center transition hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-neon-teal disabled:cursor-not-allowed disabled:opacity-60"
                              onClick={() => void handleIncreaseQuantity(item)}
                              disabled={isSyncing}
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
                  onClick={() => void clearCart()}
                  disabled={isSyncing}
                  className="mt-3 h-10 w-full text-sm font-semibold text-slate-400 transition hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
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
