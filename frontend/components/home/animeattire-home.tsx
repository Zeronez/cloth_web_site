"use client";

import { motion } from "framer-motion";
import Image from "next/image";
import { ProductImagePlaceholder } from "../product-image-placeholder";
import { useCartStore } from "../../stores/cart-store";

const featureDrops = [
  {
    code: "01",
    name: "Куртка Neon Ronin",
    detail: "Водоотталкивающий нейлон, светоотражающая тесьма, свободный крой.",
    price: "14 800 ₽"
  },
  {
    code: "02",
    name: "Худи Arcade Alley",
    detail: "Плотный футер, подкладка с манга-панелями, объемный капюшон.",
    price: "9 600 ₽"
  },
  {
    code: "03",
    name: "Карго Signal",
    detail: "Технологичный твил, магнитные клапаны, бирюзовая карта строчек.",
    price: "11 800 ₽"
  }
];

const motionUp = {
  hidden: { opacity: 0, y: 28 },
  visible: { opacity: 1, y: 0 }
};

export function AnimeAttireHome() {
  const addItem = useCartStore((state) => state.addItem);

  return (
    <main className="bg-ink-950 text-white">
      <section className="relative isolate min-h-[92vh] overflow-hidden border-b border-white/10 px-4 pb-16 pt-28 sm:px-6 lg:px-8">
        <div className="absolute inset-0 -z-20 bg-[linear-gradient(115deg,#070910_0%,#111827_48%,#0b1020_100%)]" />
        <div className="absolute inset-0 -z-10 opacity-[0.45] [background-image:linear-gradient(rgba(255,255,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.08)_1px,transparent_1px)] [background-size:48px_48px]" />
        <div className="absolute inset-x-0 bottom-0 -z-10 h-2/5 bg-[linear-gradient(180deg,transparent,rgba(20,184,166,0.12)_44%,rgba(255,56,92,0.14))]" />

        <div className="mx-auto grid max-w-7xl items-center gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(390px,0.82fr)]">
          <motion.div
            initial="hidden"
            animate="visible"
            transition={{ staggerChildren: 0.08 }}
            className="max-w-3xl"
          >
            <motion.div variants={motionUp} className="mb-6 w-full max-w-xl">
              <Image
                src="/brand/animeattire-logo.svg"
                alt="AnimeAttire"
                width={960}
                height={240}
                priority
                className="h-auto w-full"
              />
            </motion.div>

            <motion.p
              variants={motionUp}
              className="max-w-2xl text-lg leading-8 text-slate-200 sm:text-xl"
            >
              Лимитированный аниме-стритвир для ночного города, поздних раменных
              и неонового света после дождя.
            </motion.p>

            <motion.div
              variants={motionUp}
              className="mt-8 flex flex-col gap-3 sm:flex-row"
            >
              <button
                type="button"
                onClick={() =>
                  addItem({
                    id: "neon-ronin-shell",
                    name: "Куртка Neon Ronin",
                    price: 14800,
                    size: "L"
                  })
                }
                className="h-12 bg-neon-crimson px-6 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950 focus:outline-none focus:ring-2 focus:ring-neon-teal"
              >
                Добавить дроп
              </button>
              <a
                href="#drops"
                className="grid h-12 place-items-center border border-white/20 bg-white/10 px-6 text-sm font-black uppercase text-white transition hover:border-neon-teal hover:bg-neon-teal/10"
              >
                Смотреть дропы
              </a>
            </motion.div>

            <motion.dl
              variants={motionUp}
              className="mt-12 grid max-w-2xl grid-cols-3 gap-px border border-white/10 bg-white/10"
            >
              {[
                ["48ч", "окно дропа"],
                ["320gsm", "плотный футер"],
                ["NFC", "метки подлинности"]
              ].map(([value, label]) => (
                <div key={label} className="bg-ink-950/80 p-4">
                  <dt className="text-2xl font-black text-white">{value}</dt>
                  <dd className="mt-1 text-xs uppercase text-slate-400">
                    {label}
                  </dd>
                </div>
              ))}
            </motion.dl>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.94, rotate: 1.5 }}
            animate={{ opacity: 1, scale: 1, rotate: 0 }}
            transition={{ duration: 0.65, ease: "easeOut" }}
            className="relative mx-auto aspect-[4/5] w-full max-w-[520px]"
          >
            <ProductImagePlaceholder
              label="Hero drop"
              variant="jacket"
              className="h-full w-full border border-white/10 shadow-[0_24px_80px_rgba(0,0,0,0.42)]"
            />
            <div className="absolute right-12 top-24 bg-neon-amber px-3 py-2 text-xs font-black uppercase text-ink-950 shadow-[0_0_30px_rgba(249,115,22,0.45)]">
              Дроп 07
            </div>
          </motion.div>
        </div>
      </section>

      <section id="drops" className="px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
            <p className="text-xs font-black uppercase text-neon-teal">
                Капсула в продаже
              </p>
              <h2 className="mt-3 text-3xl font-black sm:text-4xl">
                Стритвир с силуэтом боевой сцены.
              </h2>
            </div>
            <p className="max-w-md text-sm leading-6 text-slate-400">
              Плотные ткани, заряженный цвет, острые силуэты и малые тиражи
              для гардероба ночного рынка.
            </p>
          </div>

          <div className="mt-10 grid gap-4 md:grid-cols-3">
            {featureDrops.map((drop) => (
              <article
                key={drop.code}
                className="border border-white/10 bg-white/[0.04] p-5 transition hover:border-neon-crimson/60 hover:bg-white/[0.07]"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-black uppercase text-neon-crimson">
                    {drop.code}
                  </span>
                  <span className="font-black text-white">{drop.price}</span>
                </div>
                <h3 className="mt-8 text-xl font-black">{drop.name}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-400">
                  {drop.detail}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section
        id="lookbook"
        className="border-y border-white/10 bg-[linear-gradient(90deg,rgba(255,56,92,0.12),rgba(20,184,166,0.1),rgba(249,115,22,0.1))] px-4 py-12 sm:px-6 lg:px-8"
      >
        <div className="mx-auto flex max-w-7xl flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <h2 className="text-2xl font-black sm:text-3xl">
            Следующий дроп откроется, когда город включит неон.
          </h2>
          <a
            href="#craft"
            className="grid h-11 w-full place-items-center border border-white/20 bg-ink-950/75 px-5 text-sm font-black uppercase text-white transition hover:bg-white hover:text-ink-950 sm:w-auto"
          >
            Детали кроя
          </a>
        </div>
      </section>

      <section id="craft" className="px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-8 md:grid-cols-[0.8fr_1fr]">
          <p className="text-xs font-black uppercase text-neon-amber">
            Система материалов
          </p>
          <p className="text-2xl font-bold leading-10 text-slate-100">
            Вещи смешивают плотный хлопок, технологичный нейлон, отражающую
            отделку и геометрию манга-панелей, чтобы образ читался сразу.
          </p>
        </div>
      </section>
    </main>
  );
}
