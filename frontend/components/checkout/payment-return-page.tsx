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

  return "Не удалось проверить статус оплаты. Попробуйте еще раз.";
}

function retryButtonLabel(result: PaymentReturnStatus) {
  if (result.return_state === "awaiting_webhook") {
    return "Вернуться к оплате";
  }

  return "Подготовить новую оплату";
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
            Возврат из оплаты
          </p>
          <h1 className="mt-3 text-3xl font-black sm:text-4xl">
            Не удалось определить платеж.
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">
            Откройте кабинет заказов: там всегда доступен актуальный статус оплаты и
            самого заказа.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/account"
              className="inline-flex h-12 items-center bg-neon-crimson px-5 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950"
            >
              Открыть кабинет
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

  if (!accessToken) {
    return (
      <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
        <section className="mx-auto max-w-4xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
          <p className="text-xs font-black uppercase text-neon-amber">
            Возврат из оплаты
          </p>
          <h1 className="mt-3 text-3xl font-black sm:text-4xl">
            Войдите, чтобы проверить статус оплаты.
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">
            Мы не показываем детали заказа без авторизации. После входа можно открыть
            кабинет и продолжить оплату, если это потребуется.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/login"
              className="inline-flex h-12 items-center bg-neon-crimson px-5 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950"
            >
              Войти
            </Link>
            <Link
              href="/account"
              className="inline-flex h-12 items-center border border-white/15 bg-white/5 px-5 text-sm font-semibold text-white transition hover:border-neon-teal/60 hover:bg-white/10"
            >
              Открыть кабинет
            </Link>
          </div>
        </section>
      </main>
    );
  }

  if (returnStatusQuery.isLoading) {
    return (
      <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
        <section className="mx-auto max-w-4xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
          <p className="text-xs font-black uppercase text-neon-teal">
            Возврат из оплаты
          </p>
          <h1 className="mt-3 text-3xl font-black sm:text-4xl">
            Проверяем статус оплаты.
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">
            Это может занять несколько секунд, пока мы сверяем состояние платежа и
            заказа.
          </p>
        </section>
      </main>
    );
  }

  if (returnStatusQuery.isError || !result) {
    return (
      <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
        <section className="mx-auto max-w-4xl border border-red-400/30 bg-red-500/10 p-6 sm:p-8">
          <p className="text-xs font-black uppercase text-red-100">
            Возврат из оплаты
          </p>
          <h1 className="mt-3 text-3xl font-black sm:text-4xl">
            Не удалось проверить статус.
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-red-50">
            {getErrorMessage(returnStatusQuery.error)}
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/account"
              className="inline-flex h-12 items-center bg-neon-crimson px-5 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950"
            >
              Открыть кабинет
            </Link>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
      <section className="mx-auto max-w-4xl border border-neon-teal/30 bg-neon-teal/10 p-6 sm:p-8">
        <p className="text-xs font-black uppercase text-neon-teal">Возврат из оплаты</p>
        <h1 className="mt-3 text-3xl font-black sm:text-4xl">
          Заказ #{result.order.id}: {getPaymentStatusLabel(result.payment.status)}
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-7 text-slate-200">
          {result.message}
        </p>

        <dl className="mt-6 grid gap-3 border border-white/10 bg-ink-950/50 p-4 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-slate-400">Сумма заказа</dt>
            <dd className="mt-1 font-bold text-white">
              {currencyFormatter.format(toAmount(result.order.total_amount))}
            </dd>
          </div>
          <div>
            <dt className="text-slate-400">Провайдер</dt>
            <dd className="mt-1 font-bold uppercase text-white">{result.provider}</dd>
          </div>
          <div>
            <dt className="text-slate-400">Статус платежа</dt>
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
            <dt className="text-slate-400">Что дальше</dt>
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
              {isRetrying ? "Готовим оплату..." : retryButtonLabel(result)}
            </button>
          ) : null}
          <Link
            href="/account"
            className="inline-flex h-12 items-center border border-white/15 bg-white/5 px-5 text-sm font-semibold text-white transition hover:border-neon-teal/60 hover:bg-white/10"
          >
            Открыть кабинет
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
