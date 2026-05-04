import type { Metadata } from "next";

import { PaymentReturnPage } from "../../../components/checkout/payment-return-page";

export const metadata: Metadata = {
  title: "Возврат из оплаты"
};

function toNumber(value?: string | string[]) {
  const raw = Array.isArray(value) ? value[0] : value;
  const parsed = Number(raw);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function toStringValue(value?: string | string[]) {
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}

export default function CheckoutReturnRoute({
  searchParams
}: {
  searchParams?: Record<string, string | string[] | undefined>;
}) {
  return (
    <PaymentReturnPage
      paymentId={toNumber(searchParams?.payment_id)}
      provider={toStringValue(searchParams?.provider)}
      externalPaymentId={toStringValue(searchParams?.external_payment_id)}
    />
  );
}
