import type { Metadata } from "next";

import { AnimeAttireHome } from "../components/home/animeattire-home";

export const metadata: Metadata = {
  title: "Главная",
  description:
    "AnimeAttire — интернет-магазин аниме-стритвира: лимитированные коллекции, доставка по России и СНГ."
};

export default function HomePage() {
  return <AnimeAttireHome />;
}
