"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  ApiError,
  createPaymentSession,
  fetchPaymentReturnStatus,
  getPaymentStatusActionLabel,
  getPaymentStatusFollowUp,
  getPaymentStatusLabel,
  getPaymentStatusTone,
  type PaymentReturnStatus
} from "../../lib/api";
import { useUserStore } from "../../stores/user-store";
import { PaymentReturnSkeleton } from "../loading-states";

const currencyFormatter = new Intl.NumberFormat("ru-RU", {
  currency: "RUB",
  style: "currency"
});

function toAmount(value: string | number | null | undefined) {
  const amount = Number(value ?? 0);
  return Number.isFinite(amount) ? amount : 0;
}

function getErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "РќРµ СѓРґР°Р»РѕСЃСЊ РїСЂРѕРІРµСЂРёС‚СЊ СЃС‚Р°С‚СѓСЃ РѕРїР»Р°С‚С‹. РџРѕРїСЂРѕР±СѓР№С‚Рµ РµС‰Рµ СЂР°Р·.";
}

function retryButtonLabel(result: PaymentReturnStatus) {
  if (result.return_state === "awaiting_webhook") {
    return "Р’РµСЂРЅСѓС‚СЊСЃСЏ Рє РѕРїР»Р°С‚Рµ";
  }

  return "РџРѕРґРіРѕС‚РѕРІРёС‚СЊ РЅРѕРІСѓСЋ РѕРїР»Р°С‚Сѓ";
}

export function PaymentReturnPage({
  paymentId,
  provider,
  externalPaymentId
}: {
  paymentId: number | null;
  provider: string;
  externalPaymentId?: string;
}) {
  const accessToken = useUserStore((state) => state.accessToken);
  const [retrySessionUrl, setRetrySessionUrl] = useState<string | null>(null);
  const [retryMessage, setRetryMessage] = useState<string | null>(null);
  const [retryError, setRetryError] = useState<string | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);

  const returnStatusQuery = useQuery({
    queryKey: [
      "payment-return-status",
      accessToken,
      paymentId,
      provider,
      externalPaymentId
    ],
    enabled: Boolean(accessToken && paymentId),
    retry: false,
    queryFn: () =>
      fetchPaymentReturnStatus(accessToken ?? "", paymentId ?? 0, {
        provider,
        external_payment_id: externalPaymentId
      })
  });

  const result = returnStatusQuery.data ?? null;
  const activeConfirmationUrl = retrySessionUrl ?? result?.confirmation_url ?? null;
  const followUp = useMemo(() => {
    if (!result) {
      return "";
    }

    return getPaymentStatusFollowUp(result.payment.status);
  }, [result]);

  async function handleRetryPayment() {
    if (!accessToken || !result) {
      return;
    }

    setIsRetrying(true);
    setRetryError(null);

    try {
      const session = await createPaymentSession(accessToken, {
        order_id: result.order.id,
        payment_method_code: result.payment.method_code,
        idempotency_key: `return-${result.order.id}-${result.payment.method_code}-${Date.now()}`
      });
      setRetrySessionUrl(session.confirmation_url);
      setRetryMessage(session.message);
    } catch (error) {
      setRetryError(getErrorMessage(error));
    } finally {
      setIsRetrying(false);
    }
  }

  if (!paymentId) {
    return (
      <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
        <section className="mx-auto max-w-4xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
          <p className="text-xs font-black uppercase text-neon-amber">
            Р’РѕР·РІСЂР°С‚ РёР· РѕРїР»Р°С‚С‹
          </p>
          <h1 className="mt-3 text-3xl font-black sm:text-4xl">
            РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ РїР»Р°С‚РµР¶.
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">
            РћС‚РєСЂРѕР№С‚Рµ РєР°Р±РёРЅРµС‚ Р·Р°РєР°Р·РѕРІ: С‚Р°Рј РІСЃРµРіРґР° РґРѕСЃС‚СѓРїРµРЅ Р°РєС‚СѓР°Р»СЊРЅС‹Р№ СЃС‚Р°С‚СѓСЃ РѕРїР»Р°С‚С‹ Рё
            СЃР°РјРѕРіРѕ Р·Р°РєР°Р·Р°.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/account"
              className="inline-flex h-12 items-center bg-neon-crimson px-5 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950"
            >
              РћС‚РєСЂС‹С‚СЊ РєР°Р±РёРЅРµС‚
            </Link>
            <Link
              href="/catalog"
              className="inline-flex h-12 items-center border border-white/15 bg-white/5 px-5 text-sm font-semibold text-white transition hover:border-neon-teal/60 hover:bg-white/10"
            >
              Р’РµСЂРЅСѓС‚СЊСЃСЏ РІ РєР°С‚Р°Р»РѕРі
            </Link>
          </div>
        </section>
      </main>
    );
  }

  if (!accessToken) {
    return (
      <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
        <section className="mx-auto max-w-4xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
          <p className="text-xs font-black uppercase text-neon-amber">
            Р’РѕР·РІСЂР°С‚ РёР· РѕРїР»Р°С‚С‹
          </p>
          <h1 className="mt-3 text-3xl font-black sm:text-4xl">
            Р’РѕР№РґРёС‚Рµ, С‡С‚РѕР±С‹ РїСЂРѕРІРµСЂРёС‚СЊ СЃС‚Р°С‚СѓСЃ РѕРїР»Р°С‚С‹.
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">
            РњС‹ РЅРµ РїРѕРєР°Р·С‹РІР°РµРј РґРµС‚Р°Р»Рё Р·Р°РєР°Р·Р° Р±РµР· Р°РІС‚РѕСЂРёР·Р°С†РёРё. РџРѕСЃР»Рµ РІС…РѕРґР° РјРѕР¶РЅРѕ РѕС‚РєСЂС‹С‚СЊ
            РєР°Р±РёРЅРµС‚ Рё РїСЂРѕРґРѕР»Р¶РёС‚СЊ РѕРїР»Р°С‚Сѓ, РµСЃР»Рё СЌС‚Рѕ РїРѕС‚СЂРµР±СѓРµС‚СЃСЏ.
          </p>
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

  if (returnStatusQuery.isLoading) {
    return <PaymentReturnSkeleton />;
  }

  if (returnStatusQuery.isError || !result) {
    return (
      <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
        <section className="mx-auto max-w-4xl border border-red-400/30 bg-red-500/10 p-6 sm:p-8">
          <p className="text-xs font-black uppercase text-red-100">
            Р’РѕР·РІСЂР°С‚ РёР· РѕРїР»Р°С‚С‹
          </p>
          <h1 className="mt-3 text-3xl font-black sm:text-4xl">
            РќРµ СѓРґР°Р»РѕСЃСЊ РїСЂРѕРІРµСЂРёС‚СЊ СЃС‚Р°С‚СѓСЃ.
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-red-50">
            {getErrorMessage(returnStatusQuery.error)}
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

  return (
    <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
      <section className="mx-auto max-w-4xl border border-neon-teal/30 bg-neon-teal/10 p-6 sm:p-8">
        <p className="text-xs font-black uppercase text-neon-teal">Р’РѕР·РІСЂР°С‚ РёР· РѕРїР»Р°С‚С‹</p>
        <h1 className="mt-3 text-3xl font-black sm:text-4xl">
          Р—Р°РєР°Р· #{result.order.id}: {getPaymentStatusLabel(result.payment.status)}
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-7 text-slate-200">
          {result.message}
        </p>

        <dl className="mt-6 grid gap-3 border border-white/10 bg-ink-950/50 p-4 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-slate-400">РЎСѓРјРјР° Р·Р°РєР°Р·Р°</dt>
            <dd className="mt-1 font-bold text-white">
              {currencyFormatter.format(toAmount(result.order.total_amount))}
            </dd>
          </div>
          <div>
            <dt className="text-slate-400">РџСЂРѕРІР°Р№РґРµСЂ</dt>
            <dd className="mt-1 font-bold uppercase text-white">{result.provider}</dd>
          </div>
          <div>
            <dt className="text-slate-400">РЎС‚Р°С‚СѓСЃ РїР»Р°С‚РµР¶Р°</dt>
            <dd className="mt-1 inline-flex">
              <span
                className={`border px-3 py-1 text-xs font-black uppercase ${getPaymentStatusTone(
                  result.payment.status
                )}`}
              >
                {getPaymentStatusLabel(result.payment.status)}
              </span>
            </dd>
          </div>
          <div>
            <dt className="text-slate-400">Р§С‚Рѕ РґР°Р»СЊС€Рµ</dt>
            <dd className="mt-1 font-bold text-white">{followUp}</dd>
          </div>
        </dl>

        {retryMessage ? (
          <div className="mt-4 border border-white/10 bg-ink-950/50 px-4 py-3 text-sm leading-6 text-slate-200">
            {retryMessage}
          </div>
        ) : null}

        {retryError ? (
          <div className="mt-4 border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
            {retryError}
          </div>
        ) : null}

        <div className="mt-6 flex flex-wrap gap-3">
          {activeConfirmationUrl ? (
            <Link
              href={activeConfirmationUrl}
              className="inline-flex h-12 items-center bg-neon-crimson px-5 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950"
            >
              {getPaymentStatusActionLabel(result.payment.status)}
            </Link>
          ) : null}
          {result.can_retry && !activeConfirmationUrl ? (
            <button
              type="button"
              onClick={handleRetryPayment}
              disabled={isRetrying}
              className="inline-flex h-12 items-center bg-neon-crimson px-5 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-slate-500 disabled:shadow-none"
            >
              {isRetrying ? "Р“РѕС‚РѕРІРёРј РѕРїР»Р°С‚Сѓ..." : retryButtonLabel(result)}
            </button>
          ) : null}
          <Link
            href="/account"
            className="inline-flex h-12 items-center border border-white/15 bg-white/5 px-5 text-sm font-semibold text-white transition hover:border-neon-teal/60 hover:bg-white/10"
          >
            РћС‚РєСЂС‹С‚СЊ РєР°Р±РёРЅРµС‚
          </Link>
          <Link
            href="/catalog"
            className="inline-flex h-12 items-center border border-white/15 bg-white/5 px-5 text-sm font-semibold text-white transition hover:border-neon-teal/60 hover:bg-white/10"
          >
            Р’РµСЂРЅСѓС‚СЊСЃСЏ РІ РєР°С‚Р°Р»РѕРі
          </Link>
        </div>
      </section>
    </main>
  );
}
