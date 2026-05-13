"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  ApiError,
  fetchOrder,
  refreshOrderTracking,
  type Order
} from "../../lib/api";
import { useUserStore } from "../../stores/user-store";
import { OrderTrackingSkeleton } from "../loading-states";

function getErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "РќРµ СѓРґР°Р»РѕСЃСЊ РѕС‚РєСЂС‹С‚СЊ РѕС‚СЃР»РµР¶РёРІР°РЅРёРµ Р·Р°РєР°Р·Р°. РџРѕРїСЂРѕР±СѓР№С‚Рµ РµС‰С‘ СЂР°Р·.";
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return "РћР¶РёРґР°РµРј РѕР±РЅРѕРІР»РµРЅРёРµ";
  }

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "long",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function getTrackingTone(order: Order) {
  const trackingStatus = order.delivery?.tracking_status ?? "";

  if (["delivered"].includes(trackingStatus)) {
    return "border-emerald-400/40 bg-emerald-500/10 text-emerald-100";
  }
  if (["failed", "returned"].includes(trackingStatus)) {
    return "border-red-400/30 bg-red-500/10 text-red-100";
  }
  if (["out_for_delivery"].includes(trackingStatus)) {
    return "border-neon-amber/40 bg-neon-amber/10 text-neon-amber";
  }
  return "border-neon-teal/40 bg-neon-teal/10 text-neon-teal";
}

function TrackingSummary({ order }: { order: Order }) {
  if (!order.delivery) {
    return (
      <div className="border border-dashed border-white/15 bg-ink-900/50 px-5 py-8 text-sm leading-6 text-slate-400">
        Р”Р»СЏ СЌС‚РѕРіРѕ Р·Р°РєР°Р·Р° РµС‰С‘ РЅРµ СЃРѕР·РґР°РЅ delivery snapshot. РљР°Рє С‚РѕР»СЊРєРѕ Р·Р°РєР°Р· РїРµСЂРµРґР°РґСѓС‚ РІ
        РґРѕСЃС‚Р°РІРєСѓ, Р·РґРµСЃСЊ РїРѕСЏРІСЏС‚СЃСЏ С‚СЂРµРє Рё РёСЃС‚РѕСЂРёСЏ РґРІРёР¶РµРЅРёСЏ.
      </div>
    );
  }

  return (
    <div className="grid gap-3 border border-white/10 bg-ink-950/50 p-4 text-sm sm:grid-cols-2">
      <div>
        <p className="text-slate-400">РўСЂРµРє-РЅРѕРјРµСЂ</p>
        <p className="mt-1 font-bold text-white">
          {order.track_number || "РќР°Р·РЅР°С‡Р°РµС‚СЃСЏ РїРµСЂРµРІРѕР·С‡РёРєРѕРј"}
        </p>
      </div>
      <div>
        <p className="text-slate-400">РџРµСЂРµРІРѕР·С‡РёРє</p>
        <p className="mt-1 font-bold uppercase text-white">
          {order.delivery.provider_code || "manual"}
        </p>
      </div>
      <div>
        <p className="text-slate-400">РўРµРєСѓС‰РёР№ СЃС‚Р°С‚СѓСЃ</p>
        <p className="mt-1">
          <span
            className={`inline-flex border px-3 py-1 text-xs font-black uppercase ${getTrackingTone(
              order
            )}`}
          >
            {order.delivery.tracking_status_label}
          </span>
        </p>
      </div>
      <div>
        <p className="text-slate-400">РџРѕСЃР»РµРґРЅСЏСЏ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ</p>
        <p className="mt-1 font-bold text-white">
          {formatDateTime(order.delivery.last_tracking_sync_at)}
        </p>
      </div>
      <div>
        <p className="text-slate-400">РўРµРєСѓС‰РµРµ РјРµСЃС‚РѕРїРѕР»РѕР¶РµРЅРёРµ</p>
        <p className="mt-1 font-bold text-white">
          {order.delivery.current_location || "Р–РґС‘Рј РѕР±РЅРѕРІР»РµРЅРёРµ РѕС‚ СЃР»СѓР¶Р±С‹ РґРѕСЃС‚Р°РІРєРё"}
        </p>
      </div>
      <div>
        <p className="text-slate-400">РђРґСЂРµСЃ РґРѕСЃС‚Р°РІРєРё</p>
        <p className="mt-1 font-bold text-white">
          {order.shipping_city}, {order.shipping_line1}
        </p>
      </div>
    </div>
  );
}

export function OrderTrackingPage({ orderId }: { orderId: number | null }) {
  const accessToken = useUserStore((state) => state.accessToken);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const orderQuery = useQuery({
    queryKey: ["order-tracking", accessToken, orderId],
    enabled: Boolean(accessToken && orderId),
    retry: false,
    queryFn: () => fetchOrder(accessToken ?? "", orderId ?? 0)
  });

  async function handleRefresh() {
    if (!accessToken || !orderId) {
      return;
    }

    setIsRefreshing(true);
    setRefreshError(null);
    try {
      await refreshOrderTracking(accessToken, orderId);
      await orderQuery.refetch();
    } catch (error) {
      setRefreshError(getErrorMessage(error));
    } finally {
      setIsRefreshing(false);
    }
  }

  if (!orderId) {
    return (
      <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
        <section className="mx-auto max-w-5xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
          <p className="text-xs font-black uppercase text-neon-amber">РћС‚СЃР»РµР¶РёРІР°РЅРёРµ Р·Р°РєР°Р·Р°</p>
          <h1 className="mt-3 text-3xl font-black sm:text-4xl">
            РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ Р·Р°РєР°Р·.
          </h1>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/account"
              className="inline-flex h-12 items-center bg-neon-crimson px-5 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950"
            >
              РћС‚РєСЂС‹С‚СЊ РєР°Р±РёРЅРµС‚
            </Link>
          </div>
        </section>
      </main>
    );
  }

  if (!accessToken) {
    return (
      <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
        <section className="mx-auto max-w-5xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
          <p className="text-xs font-black uppercase text-neon-amber">РћС‚СЃР»РµР¶РёРІР°РЅРёРµ Р·Р°РєР°Р·Р°</p>
          <h1 className="mt-3 text-3xl font-black sm:text-4xl">
            Р’РѕР№РґРёС‚Рµ, С‡С‚РѕР±С‹ РѕС‚РєСЂС‹С‚СЊ РёСЃС‚РѕСЂРёСЋ РґРѕСЃС‚Р°РІРєРё.
          </h1>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/login"
              className="inline-flex h-12 items-center bg-neon-crimson px-5 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950"
            >
              Р’РѕР№С‚Рё
            </Link>
            <Link
              href="/account"
              className="inline-flex h-12 items-center border border-white/15 bg-white/5 px-5 text-sm font-semibold text-white transition hover:border-neon-teal/60 hover:bg-white/10"
            >
              РћС‚РєСЂС‹С‚СЊ РєР°Р±РёРЅРµС‚
            </Link>
          </div>
        </section>
      </main>
    );
  }

  if (orderQuery.isLoading) {
    return <OrderTrackingSkeleton />;
  }

  if (orderQuery.isError || !orderQuery.data) {
    return (
      <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
        <section className="mx-auto max-w-5xl border border-red-400/30 bg-red-500/10 p-6 sm:p-8">
          <p className="text-xs font-black uppercase text-red-100">РћС‚СЃР»РµР¶РёРІР°РЅРёРµ Р·Р°РєР°Р·Р°</p>
          <h1 className="mt-3 text-3xl font-black sm:text-4xl">
            РќРµ СѓРґР°Р»РѕСЃСЊ РѕС‚РєСЂС‹С‚СЊ СЃС‚Р°С‚СѓСЃ РґРѕСЃС‚Р°РІРєРё.
          </h1>
          <p className="mt-4 text-base leading-7 text-red-50">
            {getErrorMessage(orderQuery.error)}
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/account"
              className="inline-flex h-12 items-center bg-neon-crimson px-5 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950"
            >
              РћС‚РєСЂС‹С‚СЊ РєР°Р±РёРЅРµС‚
            </Link>
          </div>
        </section>
      </main>
    );
  }

  const order = orderQuery.data;
  const events = [...(order.delivery?.tracking_events ?? [])].reverse();

  return (
    <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
      <section className="mx-auto max-w-5xl space-y-6">
        <div className="border border-white/10 bg-white/[0.04] p-6 sm:p-8">
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
            <div>
              <p className="text-xs font-black uppercase text-neon-teal">РћС‚СЃР»РµР¶РёРІР°РЅРёРµ Р·Р°РєР°Р·Р°</p>
              <h1 className="mt-3 text-3xl font-black sm:text-4xl">Р—Р°РєР°Р· #{order.id}</h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">
                Р—РґРµСЃСЊ СЃРѕР±СЂР°РЅР° Р°РєС‚СѓР°Р»СЊРЅР°СЏ РёСЃС‚РѕСЂРёСЏ РґРІРёР¶РµРЅРёСЏ Р·Р°РєР°Р·Р°, С‚РµРєСѓС‰РёР№ СЃС‚Р°С‚СѓСЃ РґРѕСЃС‚Р°РІРєРё Рё
                РїРѕСЃР»РµРґРЅРёРµ СЃРѕР±С‹С‚РёСЏ РѕС‚ РїРµСЂРµРІРѕР·С‡РёРєР°.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="inline-flex h-12 items-center bg-neon-crimson px-5 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-slate-500 disabled:shadow-none"
              >
                {isRefreshing ? "РћР±РЅРѕРІР»СЏРµРј..." : "РћР±РЅРѕРІРёС‚СЊ СЃС‚Р°С‚СѓСЃ"}
              </button>
              <Link
                href="/account"
                className="inline-flex h-12 items-center border border-white/15 bg-white/5 px-5 text-sm font-semibold text-white transition hover:border-neon-teal/60 hover:bg-white/10"
              >
                РљР°Р±РёРЅРµС‚
              </Link>
            </div>
          </div>

          {refreshError ? (
            <div className="mt-4 border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
              {refreshError}
            </div>
          ) : null}
        </div>

        <TrackingSummary order={order} />

        <section className="border border-white/10 bg-white/[0.04] p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-black uppercase text-neon-amber">Timeline</p>
              <h2 className="mt-3 text-2xl font-black">РСЃС‚РѕСЂРёСЏ РґРІРёР¶РµРЅРёСЏ</h2>
            </div>
            {order.track_number ? (
              <p className="text-sm font-semibold text-slate-300">РўСЂРµРє {order.track_number}</p>
            ) : null}
          </div>

          <div className="mt-6 space-y-4">
            {events.length ? (
              events.map((event) => (
                <article
                  key={event.id}
                  className="border border-white/10 bg-ink-900/60 p-4"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-black text-white">
                        {event.new_status_label}
                      </p>
                      <p className="mt-1 text-sm leading-6 text-slate-300">
                        {event.message || "РџРµСЂРµРІРѕР·С‡РёРє РѕР±РЅРѕРІРёР» СЃРѕСЃС‚РѕСЏРЅРёРµ РґРѕСЃС‚Р°РІРєРё."}
                      </p>
                      {event.location ? (
                        <p className="mt-2 text-xs uppercase text-slate-500">
                          {event.location}
                        </p>
                      ) : null}
                    </div>
                    <p className="text-xs uppercase text-slate-500">
                      {formatDateTime(event.happened_at || event.created_at)}
                    </p>
                  </div>
                </article>
              ))
            ) : (
              <div className="border border-dashed border-white/15 bg-ink-900/50 px-5 py-10 text-center text-sm leading-6 text-slate-400">
                РЎРѕР±С‹С‚РёР№ РѕС‚ СЃР»СѓР¶Р±С‹ РґРѕСЃС‚Р°РІРєРё РїРѕРєР° РЅРµС‚. РљР°Рє С‚РѕР»СЊРєРѕ РїРµСЂРµРІРѕР·С‡РёРє РІРµСЂРЅС‘С‚ РїРµСЂРІС‹Р№ СЃС‚Р°С‚СѓСЃ,
                РѕРЅ РїРѕСЏРІРёС‚СЃСЏ Р·РґРµСЃСЊ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё.
              </div>
            )}
          </div>
        </section>

        <div className="flex flex-wrap gap-3">
          <Link
            href="/account"
            className="inline-flex h-12 items-center bg-neon-crimson px-5 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950"
          >
            РќР°Р·Р°Рґ РІ РєР°Р±РёРЅРµС‚
          </Link>
          <Link
            href="/catalog"
            className="inline-flex h-12 items-center border border-white/15 bg-white/5 px-5 text-sm font-semibold text-white transition hover:border-neon-teal/60 hover:bg-white/10"
          >
            Р’ РєР°С‚Р°Р»РѕРі
          </Link>
        </div>
      </section>
    </main>
  );
}
