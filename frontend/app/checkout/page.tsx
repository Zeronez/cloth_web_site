import type { Metadata } from "next";

import { CheckoutPage } from "../../components/checkout/checkout-page";

export const metadata: Metadata = {
  title: "Оформление заказа | AnimeAttire",
  description:
    "Оформление заказа: контакты, адрес, доставка и оплата. AnimeAttire."
};

export default function Page() {
  return <CheckoutPage />;
}

