import type { Metadata } from "next";

import { OrderTrackingPage } from "../../../../components/account/order-tracking-page";

export const metadata: Metadata = {
  title: "Отслеживание заказа"
};

function toNumber(value?: string | string[]) {
  const raw = Array.isArray(value) ? value[0] : value;
  const parsed = Number(raw);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

export default function OrderTrackingRoute({
  params
}: {
  params?: { id?: string };
}) {
  return <OrderTrackingPage orderId={toNumber(params?.id)} />;
}
