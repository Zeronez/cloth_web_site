import type { Metadata } from "next";

import { ContactPage } from "../../components/contacts/contact-page";

export const metadata: Metadata = {
  title: "Контакты | AnimeAttire",
  description:
    "Напишите в поддержку AnimeAttire по заказу, доставке, возврату, подбору размера или партнерству."
};

export default function ContactsPage() {
  return <ContactPage />;
}
