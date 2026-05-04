"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  ApiError,
  createAddress,
  deleteAddress,
  fetchAddresses,
  fetchFavorites,
  fetchMe,
  fetchOrders,
  getOrderStatusLabel,
  getOrderStatusNote,
  getOrderStatusTone,
  logoutUser,
  removeFavorite,
  updateAddress,
  updateMe,
  type Address,
  type AddressInput,
  type FavoriteProductEntry,
  type Order,
  type UserProfile
} from "../../lib/api";
import { useFavoritesStore } from "../../stores/favorites-store";
import { useUserStore } from "../../stores/user-store";

type ProfileFormState = {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
};

type AddressFormState = AddressInput;

const emptyAddressForm: AddressFormState = {
  label: "Дом",
  recipient_name: "",
  phone: "",
  country: "RU",
  city: "",
  postal_code: "",
  line1: "",
  line2: "",
  is_default: false
};

const currencyFormatter = new Intl.NumberFormat("ru-RU", {
  currency: "RUB",
  style: "currency"
});

function getErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Не удалось выполнить запрос.";
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "long",
    year: "numeric"
  }).format(new Date(value));
}

function initials(profile: UserProfile | null) {
  if (!profile) {
    return "AA";
  }

  const source = `${profile.first_name ?? ""} ${profile.last_name ?? ""}`.trim();
  if (source) {
    return source
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() ?? "")
      .join("");
  }

  return profile.username.slice(0, 2).toUpperCase();
}

function AddressCard({
  address,
  onEdit,
  onDelete,
  onSetDefault
}: {
  address: Address;
  onEdit: (address: Address) => void;
  onDelete: (address: Address) => void;
  onSetDefault: (address: Address) => void;
}) {
  return (
    <article className="border border-white/10 bg-white/[0.04] p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-black text-white">{address.label}</h3>
            {address.is_default ? (
              <span className="border border-neon-teal/40 bg-neon-teal/10 px-2 py-1 text-[11px] font-black uppercase text-neon-teal">
                Основной
              </span>
            ) : null}
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            {address.recipient_name}
            <br />
            {address.line1}
            {address.line2 ? `, ${address.line2}` : ""}
            <br />
            {address.city}, {address.postal_code}
          </p>
        </div>

        <div className="text-right text-xs uppercase text-slate-500">
          Обновлён
          <br />
          {formatDate(address.updated_at)}
        </div>
      </div>

      <div className="mt-5 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => onEdit(address)}
          className="h-10 border border-white/15 bg-white/5 px-4 text-sm font-semibold text-white transition hover:border-neon-crimson/60 hover:bg-white/10"
        >
          Редактировать
        </button>
        {!address.is_default ? (
          <button
            type="button"
            onClick={() => onSetDefault(address)}
            className="h-10 border border-neon-teal/30 bg-neon-teal/10 px-4 text-sm font-semibold text-ice transition hover:bg-neon-teal/20"
          >
            Сделать основным
          </button>
        ) : null}
        <button
          type="button"
          onClick={() => onDelete(address)}
          className="h-10 border border-red-400/30 bg-red-500/10 px-4 text-sm font-semibold text-red-100 transition hover:bg-red-500/20"
        >
          Удалить
        </button>
      </div>
    </article>
  );
}

function OrderCard({ order }: { order: Order }) {
  const statusLabel = order.status_label ?? getOrderStatusLabel(order.status);
  const statusNote = getOrderStatusNote(order.status);
  const deliveryNote =
    order.delivery?.tracking_status_label && order.delivery?.current_location
      ? `${order.delivery.tracking_status_label}: ${order.delivery.current_location}`
      : order.delivery?.tracking_status_label ?? "";

  return (
    <article className="border border-white/10 bg-white/[0.04] p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase text-slate-500">
            Заказ #{order.id}
          </p>
          <h3 className="mt-2 text-xl font-black">
            {currencyFormatter.format(Number(order.total_amount))}
          </h3>
          <p className="mt-2 text-sm text-slate-400">
            {formatDate(order.created_at)} · {order.items_count} поз.
          </p>
        </div>
        <div className="text-right">
          <span
            className={`inline-flex border px-3 py-1 text-xs font-black uppercase ${getOrderStatusTone(
              order.status
            )}`}
          >
            {statusLabel}
          </span>
          {order.track_number ? (
            <p className="mt-2 text-xs uppercase text-slate-500">
              Трек {order.track_number}
            </p>
          ) : null}
          {deliveryNote ? (
            <p className="mt-2 text-xs uppercase text-slate-500">{deliveryNote}</p>
          ) : null}
        </div>
      </div>

      <p className="mt-4 text-sm leading-6 text-slate-300">{statusNote}</p>

      <div className="mt-4 flex flex-wrap gap-3">
        <Link
          href={`/account/orders/${order.id}`}
          className="inline-flex h-10 items-center border border-white/15 bg-white/5 px-4 text-sm font-semibold text-white transition hover:border-neon-teal/60 hover:bg-white/10"
        >
          Отследить заказ
        </Link>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <div className="border border-white/10 bg-ink-900/60 p-4">
          <p className="text-xs uppercase text-slate-500">Доставка</p>
          <p className="mt-2 text-sm leading-6 text-slate-200">
            {order.shipping_address.name}
            <br />
            {order.shipping_address.city}, {order.shipping_address.line1}
            {order.shipping_address.line2 ? `, ${order.shipping_address.line2}` : ""}
          </p>
        </div>
        <div className="border border-white/10 bg-ink-900/60 p-4">
          <p className="text-xs uppercase text-slate-500">Состав</p>
          <div className="mt-2 space-y-2">
            {order.items.slice(0, 3).map((item) => (
              <div key={item.id} className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-white">{item.product_name}</p>
                  <p className="text-xs uppercase text-slate-500">
                    Размер {item.size} · {item.quantity} шт.
                  </p>
                </div>
                <p className="text-sm font-semibold text-slate-200">
                  {currencyFormatter.format(Number(item.line_total))}
                </p>
              </div>
            ))}
            {order.items.length > 3 ? (
              <p className="text-xs uppercase text-slate-500">
                И ещё {order.items.length - 3} поз.
              </p>
            ) : null}
          </div>
        </div>
      </div>
    </article>
  );
}

function FavoriteCard({
  favorite,
  onRemove
}: {
  favorite: FavoriteProductEntry;
  onRemove: (favorite: FavoriteProductEntry) => void;
}) {
  return (
    <article className="border border-white/10 bg-white/[0.04] p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-black uppercase text-neon-crimson">
            {favorite.product.category.name}
          </p>
          <Link
            href={`/products/${favorite.product.slug}`}
            className="mt-2 block text-xl font-black transition hover:text-neon-teal"
          >
            {favorite.product.name}
          </Link>
          <p className="mt-2 text-sm text-slate-400">
            {currencyFormatter.format(Number(favorite.product.base_price))} ·{" "}
            {favorite.product.franchise?.name ?? "AnimeAttire"}
          </p>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs uppercase text-slate-500">
          Добавлено {formatDate(favorite.created_at)}
        </p>
        <button
          type="button"
          onClick={() => onRemove(favorite)}
          className="h-10 border border-white/15 bg-white/5 px-4 text-sm font-semibold text-white transition hover:border-neon-crimson/70 hover:bg-neon-crimson/10"
        >
          Убрать
        </button>
      </div>
    </article>
  );
}

export function AccountPage() {
  const router = useRouter();
  const accessToken = useUserStore((state) => state.accessToken);
  const refreshToken = useUserStore((state) => state.refreshToken);
  const profile = useUserStore((state) => state.profile);
  const setSession = useUserStore((state) => state.setSession);
  const clearSession = useUserStore((state) => state.clearSession);
  const setFavorites = useFavoritesStore((state) => state.setFavorites);
  const [isMounted, setIsMounted] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [addressError, setAddressError] = useState<string | null>(null);
  const [favoritesError, setFavoritesError] = useState<string | null>(null);
  const [profileForm, setProfileForm] = useState<ProfileFormState>({
    first_name: "",
    last_name: "",
    email: "",
    phone: ""
  });
  const [addressForm, setAddressForm] =
    useState<AddressFormState>(emptyAddressForm);
  const [editingAddressId, setEditingAddressId] = useState<number | null>(null);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isSavingAddress, setIsSavingAddress] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const profileQuery = useQuery({
    queryKey: ["me", accessToken],
    enabled: isMounted && Boolean(accessToken),
    queryFn: () => fetchMe(accessToken ?? ""),
    retry: false
  });

  const addressesQuery = useQuery({
    queryKey: ["addresses", accessToken],
    enabled: isMounted && Boolean(accessToken),
    queryFn: () => fetchAddresses(accessToken ?? ""),
    retry: false
  });

  const ordersQuery = useQuery({
    queryKey: ["orders", accessToken],
    enabled: isMounted && Boolean(accessToken),
    queryFn: () => fetchOrders(accessToken ?? ""),
    retry: false
  });

  const favoritesQuery = useQuery({
    queryKey: ["favorites", accessToken],
    enabled: isMounted && Boolean(accessToken),
    queryFn: () => fetchFavorites(accessToken ?? ""),
    retry: false
  });

  const currentProfile = profileQuery.data ?? profile;

  useEffect(() => {
    if (profileQuery.data) {
      setProfileForm({
        first_name: profileQuery.data.first_name ?? "",
        last_name: profileQuery.data.last_name ?? "",
        email: profileQuery.data.email ?? "",
        phone: profileQuery.data.phone ?? ""
      });
    }
  }, [profileQuery.data]);

  useEffect(() => {
    if (favoritesQuery.data) {
      setFavorites(favoritesQuery.data);
    }
  }, [favoritesQuery.data, setFavorites]);

  useEffect(() => {
    if (profileQuery.error instanceof ApiError && profileQuery.error.status === 401) {
      clearSession();
    }
  }, [clearSession, profileQuery.error]);

  useEffect(() => {
    if (
      addressesQuery.error instanceof ApiError &&
      addressesQuery.error.status === 401
    ) {
      clearSession();
    }
  }, [addressesQuery.error, clearSession]);

  useEffect(() => {
    if (ordersQuery.error instanceof ApiError && ordersQuery.error.status === 401) {
      clearSession();
    }
  }, [clearSession, ordersQuery.error]);

  useEffect(() => {
    if (
      favoritesQuery.error instanceof ApiError &&
      favoritesQuery.error.status === 401
    ) {
      clearSession();
    }
  }, [clearSession, favoritesQuery.error]);

  const metrics = useMemo(
    () => [
      { label: "Имя пользователя", value: currentProfile?.username ?? "—" },
      { label: "Телефон", value: currentProfile?.phone ?? "Не указан" },
      { label: "Адресов", value: String(addressesQuery.data?.length ?? 0) },
      { label: "Заказов", value: String(ordersQuery.data?.results.length ?? 0) },
      { label: "В избранном", value: String(favoritesQuery.data?.length ?? 0) }
    ],
    [
      addressesQuery.data?.length,
      currentProfile,
      favoritesQuery.data?.length,
      ordersQuery.data?.results.length
    ]
  );

  async function handleProfileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken || !refreshToken) {
      return;
    }

    setProfileError(null);
    setIsSavingProfile(true);

    try {
      const updated = await updateMe(accessToken, {
        first_name: profileForm.first_name,
        last_name: profileForm.last_name,
        email: profileForm.email,
        phone: profileForm.phone
      });

      setSession({
        accessToken,
        refreshToken,
        profile: updated
      });
      profileQuery.refetch();
    } catch (error) {
      setProfileError(getErrorMessage(error));
    } finally {
      setIsSavingProfile(false);
    }
  }

  async function handleAddressSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) {
      return;
    }

    setAddressError(null);
    setIsSavingAddress(true);

    try {
      if (editingAddressId) {
        await updateAddress(accessToken, editingAddressId, addressForm);
      } else {
        await createAddress(accessToken, addressForm);
      }

      await addressesQuery.refetch();
      setAddressForm(emptyAddressForm);
      setEditingAddressId(null);
    } catch (error) {
      setAddressError(getErrorMessage(error));
    } finally {
      setIsSavingAddress(false);
    }
  }

  function handleEditAddress(address: Address) {
    setEditingAddressId(address.id);
    setAddressForm({
      label: address.label,
      recipient_name: address.recipient_name,
      phone: address.phone,
      country: address.country,
      city: address.city,
      postal_code: address.postal_code,
      line1: address.line1,
      line2: address.line2,
      is_default: address.is_default
    });
  }

  function handleResetAddressForm() {
    setEditingAddressId(null);
    setAddressForm(emptyAddressForm);
  }

  async function handleDeleteAddress(address: Address) {
    if (!accessToken) {
      return;
    }

    if (!window.confirm(`Удалить адрес "${address.label}"?`)) {
      return;
    }

    setAddressError(null);

    try {
      await deleteAddress(accessToken, address.id);
      await addressesQuery.refetch();
    } catch (error) {
      setAddressError(getErrorMessage(error));
    }
  }

  async function handleSetDefault(address: Address) {
    if (!accessToken) {
      return;
    }

    setAddressError(null);

    try {
      await updateAddress(accessToken, address.id, {
        is_default: true
      });
      await addressesQuery.refetch();
    } catch (error) {
      setAddressError(getErrorMessage(error));
    }
  }

  async function handleRemoveFavorite(favorite: FavoriteProductEntry) {
    if (!accessToken) {
      return;
    }

    try {
      setFavoritesError(null);
      await removeFavorite(accessToken, favorite.product_id);
      const updatedFavorites = await fetchFavorites(accessToken);
      setFavorites(updatedFavorites);
      await favoritesQuery.refetch();
    } catch (error) {
      setFavoritesError(getErrorMessage(error));
    }
  }

  async function handleLogout() {
    if (!accessToken || !refreshToken) {
      clearSession();
      router.push("/login");
      return;
    }

    setIsLoggingOut(true);

    try {
      await logoutUser(accessToken, refreshToken);
    } catch {
      // Локальную сессию всё равно можно очистить.
    } finally {
      clearSession();
      router.push("/login");
      router.refresh();
      setIsLoggingOut(false);
    }
  }

  if (!isMounted) {
    return (
      <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
        <section className="mx-auto space-y-6">
          <div className="h-10 w-64 animate-pulse bg-white/10" />
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="h-[380px] animate-pulse border border-white/10 bg-white/[0.04]" />
            <div className="h-[380px] animate-pulse border border-white/10 bg-white/[0.04]" />
          </div>
          <div className="grid gap-6 xl:grid-cols-2">
            <div className="h-[320px] animate-pulse border border-white/10 bg-white/[0.04]" />
            <div className="h-[320px] animate-pulse border border-white/10 bg-white/[0.04]" />
          </div>
        </section>
      </main>
    );
  }

  if (!accessToken) {
    return (
      <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
        <section className="mx-auto grid max-w-4xl gap-6 border border-white/10 bg-white/[0.04] p-6 sm:p-8">
          <p className="text-xs font-black uppercase text-neon-teal">Личный кабинет</p>
          <h1 className="text-3xl font-black sm:text-4xl">
            Войдите, чтобы открыть профиль, адреса, заказы и избранное.
          </h1>
          <p className="max-w-2xl text-base leading-7 text-slate-300">
            В кабинете сохраняются данные профиля, адреса доставки, история заказов и
            подборка любимых вещей.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/login"
              className="inline-flex h-11 items-center border border-white/15 bg-white/5 px-5 text-sm font-semibold text-white transition hover:border-neon-crimson/60 hover:bg-white/10"
            >
              Войти
            </Link>
            <Link
              href="/register"
              className="inline-flex h-11 items-center border border-neon-teal/30 bg-neon-teal/10 px-5 text-sm font-semibold text-ice transition hover:bg-neon-teal/20"
            >
              Зарегистрироваться
            </Link>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
      <section className="mx-auto max-w-7xl space-y-8">
        <div className="flex flex-col justify-between gap-4 border border-white/10 bg-white/[0.04] p-6 md:flex-row md:items-center">
          <div className="flex items-center gap-4">
            <div className="grid h-14 w-14 place-items-center border border-white/10 bg-ink-900 text-lg font-black text-white">
              {initials(currentProfile)}
            </div>
            <div>
              <p className="text-xs font-black uppercase text-neon-crimson">
                Личный кабинет
              </p>
              <h1 className="mt-2 text-2xl font-black sm:text-3xl">
                {currentProfile?.first_name || currentProfile?.last_name
                  ? `${currentProfile?.first_name ?? ""} ${currentProfile?.last_name ?? ""}`.trim()
                  : currentProfile?.username}
              </h1>
              <p className="mt-1 text-sm text-slate-400">
                {currentProfile?.email ?? "Аккаунт готов к управлению"}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="h-11 border border-white/15 bg-white/5 px-5 text-sm font-semibold text-white transition hover:border-neon-crimson/60 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isLoggingOut ? "Выход..." : "Выйти"}
          </button>
        </div>

        <div className="grid gap-6 lg:grid-cols-[0.92fr_1.08fr]">
          <section className="border border-white/10 bg-white/[0.04] p-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-black uppercase text-neon-teal">Профиль</p>
                <h2 className="mt-3 text-2xl font-black">Контактные данные</h2>
              </div>
            </div>

            {profileQuery.error ? (
              <div className="mt-4 border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
                {getErrorMessage(profileQuery.error)}
              </div>
            ) : null}

            <dl className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {metrics.map((metric) => (
                <div key={metric.label} className="border border-white/10 bg-ink-900/60 p-4">
                  <dt className="text-xs uppercase text-slate-500">{metric.label}</dt>
                  <dd className="mt-2 text-sm font-semibold text-white">{metric.value}</dd>
                </div>
              ))}
            </dl>

            <form className="mt-6 space-y-4" onSubmit={handleProfileSubmit}>
              {[
                ["first_name", "Имя"],
                ["last_name", "Фамилия"],
                ["email", "Почта"],
                ["phone", "Телефон"]
              ].map(([name, label]) => (
                <label key={name} className="block">
                  <span className="mb-2 block text-sm font-semibold text-slate-200">
                    {label}
                  </span>
                  <input
                    required={name === "email"}
                    value={profileForm[name as keyof ProfileFormState]}
                    onChange={(event) =>
                      setProfileForm((current) => ({
                        ...current,
                        [name]: event.target.value
                      }))
                    }
                    type={name === "email" ? "email" : "text"}
                    className="h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30"
                  />
                </label>
              ))}

              {profileError ? (
                <div className="border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
                  {profileError}
                </div>
              ) : null}

              <button
                type="submit"
                disabled={isSavingProfile}
                className="flex h-12 items-center justify-center bg-neon-crimson px-5 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSavingProfile ? "Сохранение..." : "Сохранить профиль"}
              </button>
            </form>
          </section>

          <section className="border border-white/10 bg-white/[0.04] p-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-black uppercase text-neon-amber">Адреса</p>
                <h2 className="mt-3 text-2xl font-black">Доставка и получатели</h2>
              </div>
              <span className="text-sm text-slate-400">
                {addressesQuery.data?.length ?? 0} запис.
              </span>
            </div>

            {addressesQuery.error ? (
              <div className="mt-4 border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
                {getErrorMessage(addressesQuery.error)}
              </div>
            ) : null}

            <form className="mt-6 space-y-4" onSubmit={handleAddressSubmit}>
              <div className="grid gap-4 sm:grid-cols-2">
                {[
                  ["label", "Метка"],
                  ["recipient_name", "Получатель"],
                  ["phone", "Телефон"],
                  ["country", "Страна"],
                  ["city", "Город"],
                  ["postal_code", "Индекс"],
                  ["line1", "Адрес, строка 1"],
                  ["line2", "Адрес, строка 2"]
                ].map(([name, label]) => (
                  <label key={name} className="block sm:col-span-1">
                    <span className="mb-2 block text-sm font-semibold text-slate-200">
                      {label}
                    </span>
                    <input
                      required={name !== "line2"}
                      value={addressForm[name as keyof AddressFormState] as string}
                      onChange={(event) =>
                        setAddressForm((current) => ({
                          ...current,
                          [name]: event.target.value
                        }))
                      }
                      className={`h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30 ${
                        name === "line1" || name === "line2" ? "sm:col-span-2" : ""
                      }`}
                    />
                  </label>
                ))}
              </div>

              <label className="flex items-center gap-3 text-sm text-slate-200">
                <input
                  type="checkbox"
                  checked={addressForm.is_default}
                  onChange={(event) =>
                    setAddressForm((current) => ({
                      ...current,
                      is_default: event.target.checked
                    }))
                  }
                  className="h-4 w-4 border-white/20 bg-ink-900 text-neon-teal focus:ring-neon-teal"
                />
                Сделать этот адрес основным
              </label>

              {addressError ? (
                <div className="border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
                  {addressError}
                </div>
              ) : null}

              <div className="flex flex-wrap gap-3">
                <button
                  type="submit"
                  disabled={isSavingAddress}
                  className="flex h-12 items-center justify-center bg-neon-crimson px-5 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSavingAddress
                    ? editingAddressId
                      ? "Обновление..."
                      : "Добавление..."
                    : editingAddressId
                      ? "Обновить адрес"
                      : "Добавить адрес"}
                </button>
                {editingAddressId ? (
                  <button
                    type="button"
                    onClick={handleResetAddressForm}
                    className="h-12 border border-white/15 bg-white/5 px-5 text-sm font-semibold text-white transition hover:border-neon-teal/60 hover:bg-white/10"
                  >
                    Отменить
                  </button>
                ) : null}
              </div>
            </form>

            <div className="mt-8 space-y-4">
              {addressesQuery.isLoading ? (
                <div className="space-y-4">
                  <div className="h-36 animate-pulse border border-white/10 bg-white/[0.04]" />
                  <div className="h-36 animate-pulse border border-white/10 bg-white/[0.04]" />
                </div>
              ) : addressesQuery.data?.length ? (
                addressesQuery.data.map((address) => (
                  <AddressCard
                    key={address.id}
                    address={address}
                    onEdit={handleEditAddress}
                    onDelete={handleDeleteAddress}
                    onSetDefault={handleSetDefault}
                  />
                ))
              ) : (
                <div className="border border-dashed border-white/15 bg-ink-900/50 px-5 py-10 text-center text-sm leading-6 text-slate-400">
                  Адресов пока нет. Добавьте первый адрес, чтобы ускорить оформление
                  заказа.
                </div>
              )}
            </div>
          </section>
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          <section className="border border-white/10 bg-white/[0.04] p-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-black uppercase text-neon-teal">Заказы</p>
                <h2 className="mt-3 text-2xl font-black">История покупок</h2>
              </div>
              <span className="text-sm text-slate-400">
                {ordersQuery.data?.results.length ?? 0} запис.
              </span>
            </div>

            {ordersQuery.error ? (
              <div className="mt-4 border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
                {getErrorMessage(ordersQuery.error)}
              </div>
            ) : null}

            <div className="mt-6 space-y-4">
              {ordersQuery.isLoading ? (
                <div className="space-y-4">
                  <div className="h-44 animate-pulse border border-white/10 bg-white/[0.04]" />
                  <div className="h-44 animate-pulse border border-white/10 bg-white/[0.04]" />
                </div>
              ) : ordersQuery.data?.results.length ? (
                ordersQuery.data.results.map((order) => (
                  <OrderCard key={order.id} order={order} />
                ))
              ) : (
                <div className="border border-dashed border-white/15 bg-ink-900/50 px-5 py-10 text-center text-sm leading-6 text-slate-400">
                  Пока нет заказов. Первый оформленный дроп появится здесь.
                </div>
              )}
            </div>
          </section>

          <section className="border border-white/10 bg-white/[0.04] p-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-black uppercase text-neon-crimson">Избранное</p>
                <h2 className="mt-3 text-2xl font-black">Любимые вещи</h2>
              </div>
              <span className="text-sm text-slate-400">
                {favoritesQuery.data?.length ?? 0} запис.
              </span>
            </div>

            {favoritesQuery.error ? (
              <div className="mt-4 border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
                {getErrorMessage(favoritesQuery.error)}
              </div>
            ) : null}
            {favoritesError ? (
              <div className="mt-4 border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
                {favoritesError}
              </div>
            ) : null}

            <div className="mt-6 space-y-4">
              {favoritesQuery.isLoading ? (
                <div className="space-y-4">
                  <div className="h-36 animate-pulse border border-white/10 bg-white/[0.04]" />
                  <div className="h-36 animate-pulse border border-white/10 bg-white/[0.04]" />
                </div>
              ) : favoritesQuery.data?.length ? (
                favoritesQuery.data.map((favorite) => (
                  <FavoriteCard
                    key={favorite.id}
                    favorite={favorite}
                    onRemove={handleRemoveFavorite}
                  />
                ))
              ) : (
                <div className="border border-dashed border-white/15 bg-ink-900/50 px-5 py-10 text-center text-sm leading-6 text-slate-400">
                  Здесь будут вещи, которые вы отложили на потом.
                </div>
              )}
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
