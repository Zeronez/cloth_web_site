"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  ApiError,
  addCartItem,
  checkoutOrder,
  deleteCartItem,
  fetchAddresses,
  fetchCart,
  updateCartItemQuantity,
  type Address,
  type CheckoutInput,
  type Order
} from "../../lib/api";
import {
  selectCartCount,
  selectCartSubtotal,
  useCartStore,
  type CartItem
} from "../../stores/cart-store";
import { useUserStore } from "../../stores/user-store";
import { ProductImagePlaceholder } from "../product-image-placeholder";

const currencyFormatter = new Intl.NumberFormat("ru-RU", {
  currency: "RUB",
  style: "currency"
});

const emptyCheckoutForm: CheckoutInput = {
  shipping_name: "",
  shipping_phone: "",
  shipping_country: "RU",
  shipping_city: "",
  shipping_postal_code: "",
  shipping_line1: "",
  shipping_line2: ""
};

function getErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Не удалось выполнить запрос. Попробуйте еще раз.";
}

function addressToForm(address: Address): CheckoutInput {
  return {
    shipping_name: address.recipient_name,
    shipping_phone: address.phone,
    shipping_country: address.country,
    shipping_city: address.city,
    shipping_postal_code: address.postal_code,
    shipping_line1: address.line1,
    shipping_line2: address.line2
  };
}

function profileName(profile: ReturnType<typeof useUserStore.getState>["profile"]) {
  if (!profile) {
    return "";
  }

  return `${profile.first_name ?? ""} ${profile.last_name ?? ""}`.trim();
}

function normalizeLocalCart(items: CartItem[]) {
  const desired = new Map<number, number>();

  for (const item of items) {
    const variantId = Number(item.id);

    if (!Number.isInteger(variantId) || variantId < 1) {
      throw new Error(
        `Позиция "${item.name}" не содержит корректный variant_id для backend cart.`
      );
    }

    desired.set(variantId, (desired.get(variantId) ?? 0) + item.quantity);
  }

  return desired;
}

async function syncLocalCartToServer(token: string, items: CartItem[]) {
  const desired = normalizeLocalCart(items);
  const serverCart = await fetchCart(token);
  const serverItemsByVariant = new Map(
    serverCart.items.map((item) => [item.variant.id, item])
  );

  for (const serverItem of serverCart.items) {
    if (!desired.has(serverItem.variant.id)) {
      await deleteCartItem(token, serverItem.id);
    }
  }

  for (const [variantId, quantity] of desired) {
    const serverItem = serverItemsByVariant.get(variantId);

    if (!serverItem) {
      await addCartItem(token, variantId, quantity);
      continue;
    }

    if (serverItem.quantity !== quantity) {
      await updateCartItemQuantity(token, serverItem.id, quantity);
    }
  }
}

function CheckoutField({
  label,
  name,
  value,
  autoComplete,
  required = true,
  type = "text",
  onChange
}: {
  label: string;
  name: keyof CheckoutInput;
  value: string;
  autoComplete: string;
  required?: boolean;
  type?: string;
  onChange: (name: keyof CheckoutInput, value: string) => void;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-semibold text-slate-200">
        {label}
      </span>
      <input
        name={name}
        required={required}
        type={type}
        autoComplete={autoComplete}
        value={value}
        onChange={(event) => onChange(name, event.target.value)}
        className="h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition placeholder:text-slate-500 focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30"
      />
    </label>
  );
}

function OrderSummary({
  items,
  subtotal
}: {
  items: CartItem[];
  subtotal: number;
}) {
  return (
    <section className="border border-white/10 bg-white/[0.04] p-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-black uppercase text-neon-teal">Корзина</p>
          <h2 className="mt-2 text-2xl font-black">Состав заказа</h2>
        </div>
        <Link
          href="/catalog"
          className="text-sm font-semibold text-slate-300 transition hover:text-white"
        >
          В каталог
        </Link>
      </div>

      <div className="mt-6 space-y-4">
        {items.map((item) => (
          <article
            key={`${item.id}-${item.size}`}
            className="grid grid-cols-[72px_1fr] gap-4 border border-white/10 bg-ink-900/60 p-3"
          >
            <ProductImagePlaceholder label="AA" variant="cart" className="h-[88px]" />
            <div className="min-w-0">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-bold leading-tight text-white">{item.name}</h3>
                  <p className="mt-1 text-xs uppercase text-slate-400">
                    Размер {item.size} · {item.quantity} шт.
                  </p>
                </div>
                <p className="shrink-0 font-bold">
                  {currencyFormatter.format(item.price * item.quantity)}
                </p>
              </div>
            </div>
          </article>
        ))}
      </div>

      <dl className="mt-6 space-y-3 border-t border-white/10 pt-5 text-sm">
        <div className="flex items-center justify-between text-slate-300">
          <dt>Товары</dt>
          <dd>{currencyFormatter.format(subtotal)}</dd>
        </div>
        <div className="flex items-center justify-between text-slate-300">
          <dt>Доставка</dt>
          <dd>Рассчитаем после подтверждения</dd>
        </div>
        <div className="flex items-center justify-between text-lg font-black text-white">
          <dt>Итого</dt>
          <dd>{currencyFormatter.format(subtotal)}</dd>
        </div>
      </dl>
    </section>
  );
}

function SuccessState({ order }: { order: Order }) {
  return (
    <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
      <section className="mx-auto max-w-4xl border border-neon-teal/30 bg-neon-teal/10 p-6 sm:p-8">
        <p className="text-xs font-black uppercase text-neon-teal">Заказ создан</p>
        <h1 className="mt-3 text-3xl font-black sm:text-4xl">
          Заказ #{order.id} принят в обработку.
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-7 text-slate-200">
          Мы сохранили адрес доставки и состав заказа. Статус и детали доступны в
          личном кабинете.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/account"
            className="inline-flex h-12 items-center bg-neon-crimson px-5 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950"
          >
            Открыть заказы
          </Link>
          <Link
            href="/catalog"
            className="inline-flex h-12 items-center border border-white/15 bg-white/5 px-5 text-sm font-semibold text-white transition hover:border-neon-teal/60 hover:bg-white/10"
          >
            Вернуться в каталог
          </Link>
        </div>
      </section>
    </main>
  );
}

export function CheckoutPage() {
  const accessToken = useUserStore((state) => state.accessToken);
  const profile = useUserStore((state) => state.profile);
  const clearSession = useUserStore((state) => state.clearSession);
  const items = useCartStore((state) => state.items);
  const clearCart = useCartStore((state) => state.clearCart);
  const subtotal = useCartStore(selectCartSubtotal);
  const cartCount = useCartStore(selectCartCount);
  const [isMounted, setIsMounted] = useState(false);
  const [form, setForm] = useState<CheckoutInput>(emptyCheckoutForm);
  const [selectedAddressId, setSelectedAddressId] = useState("manual");
  const [error, setError] = useState<string | null>(null);
  const [successOrder, setSuccessOrder] = useState<Order | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const addressesQuery = useQuery({
    queryKey: ["addresses", accessToken, "checkout"],
    enabled: isMounted && Boolean(accessToken),
    queryFn: () => fetchAddresses(accessToken ?? ""),
    retry: false
  });

  const addresses = useMemo(
    () => addressesQuery.data ?? [],
    [addressesQuery.data]
  );

  useEffect(() => {
    if (addressesQuery.error instanceof ApiError && addressesQuery.error.status === 401) {
      clearSession();
    }
  }, [addressesQuery.error, clearSession]);

  useEffect(() => {
    if (!profile) {
      return;
    }

    setForm((current) => ({
      ...current,
      shipping_name: current.shipping_name || profileName(profile),
      shipping_phone: current.shipping_phone || profile.phone || ""
    }));
  }, [profile]);

  useEffect(() => {
    if (selectedAddressId !== "manual" || addresses.length === 0) {
      return;
    }

    const defaultAddress = addresses.find((address) => address.is_default);

    if (defaultAddress) {
      setSelectedAddressId(String(defaultAddress.id));
      setForm(addressToForm(defaultAddress));
    }
  }, [addresses, selectedAddressId]);

  function updateField(name: keyof CheckoutInput, value: string) {
    setForm((current) => ({ ...current, [name]: value }));
    setSelectedAddressId("manual");
  }

  function handleAddressSelect(value: string) {
    setSelectedAddressId(value);

    if (value === "manual") {
      return;
    }

    const address = addresses.find((item) => String(item.id) === value);

    if (address) {
      setForm(addressToForm(address));
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!accessToken) {
      setError("Для оформления заказа нужно войти в аккаунт.");
      return;
    }

    if (items.length === 0) {
      setError("Корзина пуста. Добавьте товары перед оформлением заказа.");
      return;
    }

    setIsSubmitting(true);

    try {
      await syncLocalCartToServer(accessToken, items);
      const order = await checkoutOrder(accessToken, form);
      clearCart();
      setSuccessOrder(order);
    } catch (submittedError) {
      setError(getErrorMessage(submittedError));
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!isMounted) {
    return (
      <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
        <section className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[1fr_420px]">
          <div className="h-[580px] animate-pulse border border-white/10 bg-white/[0.04]" />
          <div className="h-[420px] animate-pulse border border-white/10 bg-white/[0.04]" />
        </section>
      </main>
    );
  }

  if (successOrder) {
    return <SuccessState order={successOrder} />;
  }

  if (items.length === 0) {
    return (
      <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
        <section className="mx-auto max-w-4xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
          <p className="text-xs font-black uppercase text-neon-teal">
            Оформление заказа
          </p>
          <h1 className="mt-3 text-3xl font-black sm:text-4xl">
            Корзина пока пуста.
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">
            Добавьте размер из дропа, и мы соберем заказ на этой странице.
          </p>
          <Link
            href="/catalog"
            className="mt-6 inline-flex h-12 items-center bg-neon-crimson px-5 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950"
          >
            Перейти в каталог
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
      <section className="mx-auto max-w-7xl">
        <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <p className="text-xs font-black uppercase text-neon-crimson">
              Оформление заказа
            </p>
            <h1 className="mt-3 text-4xl font-black sm:text-5xl">
              Доставка и контакты
            </h1>
          </div>
          <p className="text-sm text-slate-400">
            {cartCount} поз. · {currencyFormatter.format(subtotal)}
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_420px] lg:items-start">
          <section className="border border-white/10 bg-white/[0.04] p-5 sm:p-6">
            {!accessToken ? (
              <div className="mb-6 border border-neon-amber/30 bg-neon-amber/10 px-4 py-3 text-sm leading-6 text-orange-100">
                Войдите или зарегистрируйтесь, чтобы подтвердить заказ. Корзина
                останется на месте.
                <div className="mt-3 flex flex-wrap gap-3">
                  <Link
                    href="/login"
                    className="inline-flex h-10 items-center border border-white/15 bg-white/5 px-4 text-sm font-semibold text-white transition hover:bg-white/10"
                  >
                    Войти
                  </Link>
                  <Link
                    href="/register"
                    className="inline-flex h-10 items-center border border-neon-teal/30 bg-neon-teal/10 px-4 text-sm font-semibold text-ice transition hover:bg-neon-teal/20"
                  >
                    Зарегистрироваться
                  </Link>
                </div>
              </div>
            ) : null}

            <form className="space-y-6" onSubmit={handleSubmit}>
              {accessToken ? (
                <div>
                  <label className="block">
                    <span className="mb-2 block text-sm font-semibold text-slate-200">
                      Сохраненный адрес
                    </span>
                    <select
                      value={selectedAddressId}
                      onChange={(event) => handleAddressSelect(event.target.value)}
                      disabled={addressesQuery.isLoading}
                      className="h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <option value="manual">
                        {addressesQuery.isLoading
                          ? "Загружаем адреса..."
                          : "Новый адрес"}
                      </option>
                      {addresses.map((address) => (
                        <option key={address.id} value={address.id}>
                          {address.label} · {address.city}, {address.line1}
                        </option>
                      ))}
                    </select>
                  </label>
                  {addressesQuery.error ? (
                    <div className="mt-3 border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
                      {getErrorMessage(addressesQuery.error)}
                    </div>
                  ) : null}
                </div>
              ) : null}

              <div>
                <p className="text-xs font-black uppercase text-neon-teal">
                  Получатель
                </p>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <CheckoutField
                    label="Имя и фамилия"
                    name="shipping_name"
                    value={form.shipping_name}
                    autoComplete="name"
                    onChange={updateField}
                  />
                  <CheckoutField
                    label="Телефон"
                    name="shipping_phone"
                    value={form.shipping_phone}
                    autoComplete="tel"
                    type="tel"
                    onChange={updateField}
                  />
                </div>
              </div>

              <div>
                <p className="text-xs font-black uppercase text-neon-teal">
                  Адрес доставки
                </p>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <CheckoutField
                    label="Страна"
                    name="shipping_country"
                    value={form.shipping_country}
                    autoComplete="country"
                    onChange={updateField}
                  />
                  <CheckoutField
                    label="Город"
                    name="shipping_city"
                    value={form.shipping_city}
                    autoComplete="address-level2"
                    onChange={updateField}
                  />
                  <CheckoutField
                    label="Индекс"
                    name="shipping_postal_code"
                    value={form.shipping_postal_code}
                    autoComplete="postal-code"
                    onChange={updateField}
                  />
                  <CheckoutField
                    label="Улица, дом, квартира"
                    name="shipping_line1"
                    value={form.shipping_line1}
                    autoComplete="address-line1"
                    onChange={updateField}
                  />
                  <div className="sm:col-span-2">
                    <CheckoutField
                      label="Комментарий к адресу"
                      name="shipping_line2"
                      value={form.shipping_line2}
                      autoComplete="address-line2"
                      required={false}
                      onChange={updateField}
                    />
                  </div>
                </div>
              </div>

              {error ? (
                <div className="border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
                  {error}
                </div>
              ) : null}

              <button
                type="submit"
                disabled={isSubmitting || !accessToken}
                className="flex h-12 w-full items-center justify-center bg-neon-crimson px-6 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-slate-500 disabled:shadow-none"
              >
                {isSubmitting ? "Создаем заказ..." : "Подтвердить заказ"}
              </button>
            </form>
          </section>

          <OrderSummary items={items} subtotal={subtotal} />
        </div>
      </section>
    </main>
  );
}
