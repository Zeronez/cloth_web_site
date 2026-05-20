import type { Metadata } from "next";

import { SearchPage } from "../../components/search/search-page";

export const metadata: Metadata = {
  title: "Поиск | AnimeAttire",
  description: "Поиск товаров AnimeAttire по названию и описанию."
};

export default function Page() {
  return <SearchPage />;
}

