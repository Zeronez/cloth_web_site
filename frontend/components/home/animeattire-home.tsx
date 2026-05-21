"use client";

import { motion } from "framer-motion";
import Image from "next/image";

import { useCartSync } from "../../lib/use-cart-sync";
import { ProductImagePlaceholder } from "../product-image-placeholder";

const featureDrops = [
  {
    code: "01",
    name: "Куртка Neon Ronin",
    detail:
      "Водоотталкивающий нейлон, светоотражающая тесьма, свободный крой.",
    price: "14 800 ₽"
  },
  {
    code: "02",
    name: "Худи Arcade Alley",
    detail: "Плотный футер, подкладка с манга-панелями, объёмный капюшон.",
    price: "9 600 ₽"
  },
  {
    code: "03",
    name: "Карго Signal",
    detail:
      "Технологичный твил, магнитные клапаны, аккуратные строчки и карманы.",
    price: "11 800 ₽"
  }
];

const motionUp = {
  hidden: { opacity: 0, y: 28 },
  visible: { opacity: 1, y: 0 }
};

const support = {
  telegram: "https://t.me/animeattire",
  vk: "https://vk.com/animeattre",
  phoneDisplay: "+7 982 402-26-46",
  phoneHref: "tel:+79824022646",
  address: "Лиговский проспект, 76, Санкт-Петербург, 191040"
};

export function AnimeAttireHome() {
  const { addItem } = useCartSync();

  return (
    <main className="bg-ink-950 text-white">
      <section className="relative isolate min-h-[92vh] overflow-hidden border-b border-white/10 px-4 pb-16 pt-28 sm:px-6 lg:px-8">
        <div className="absolute inset-0 -z-20 bg-[linear-gradient(115deg,#002A32_0%,#00333D_60%,#002A32_100%)]" />
        <div className="absolute inset-0 -z-10 opacity-[0.25] [background-image:radial-gradient(circle_at_top,rgba(255,255,255,0.08),transparent_55%)]" />

        <div className="mx-auto grid max-w-7xl items-center gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(390px,0.82fr)]">
          <motion.div
            initial="hidden"
            animate="visible"
            transition={{ staggerChildren: 0.08 }}
            className="max-w-3xl"
          >
            <motion.div variants={motionUp} className="mb-6 w-full max-w-xl">
              <Image
                src="/brand/animeattire-logo.v2.png"
                alt="AnimeAttire"
                width={2172}
                height={724}
                priority
                className="h-auto w-full opacity-95"
              />
            </motion.div>

            <motion.p
              variants={motionUp}
              className="max-w-2xl text-lg leading-8 text-slate-200 sm:text-xl"
            >
              Лимитированный аниме-стритвир: аккуратные силуэты, плотные ткани и
              минималистичный вайб.
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
                className="h-12 rounded-full bg-white px-6 text-sm font-black uppercase text-ink-950 transition hover:bg-white/90 focus:outline-none focus:ring-2 focus:ring-white/30"
              >
                Добавить дроп
              </button>
              <a
                href="#drops"
                className="grid h-12 place-items-center rounded-full border border-white/15 bg-white/5 px-6 text-sm font-black uppercase text-white transition hover:border-white/30 hover:bg-white/10"
              >
                Смотреть дропы
              </a>
            </motion.div>

            <motion.dl
              variants={motionUp}
              className="mt-12 grid max-w-2xl grid-cols-3 gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04]"
            >
              {[
                ["48ч", "Новые дропы"],
                ["0₽", "Доставка от"],
                ["14", "Дней на возврат"]
              ].map(([value, label]) => (
                <div key={label} className="bg-ink-950/60 p-4">
                  <dt className="text-2xl font-black text-white">{value}</dt>
                  <dd className="mt-1 text-xs font-bold uppercase tracking-[0.18em] text-slate-400">
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
            <div className="absolute right-10 top-10 rounded-full border border-white/10 bg-ink-950/80 px-3 py-2 text-xs font-black uppercase tracking-[0.18em] text-white">
              Дроп 07
            </div>
          </motion.div>
        </div>
      </section>

      <section id="drops" className="px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-400">
                Капсула в продаже
              </p>
              <h2 className="mt-3 text-3xl font-black sm:text-4xl">
                Ключевые позиции недели
              </h2>
            </div>
            <p className="max-w-md text-sm leading-6 text-slate-400">
              Минимум шума — максимум формы. Собрали три позиции, которые проще
              всего стилизовать под город.
            </p>
          </div>

          <div className="mt-10 grid gap-4 md:grid-cols-3">
            {featureDrops.map((drop) => (
              <article
                key={drop.code}
                className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 transition hover:border-white/20 hover:bg-white/[0.06]"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-black uppercase tracking-[0.22em] text-slate-400">
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

      <section className="border-t border-white/10 bg-white/[0.03] px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-8 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.24em] text-neon-teal">
              Соцсети и поддержка
            </p>
            <h2 className="mt-4 text-3xl font-black leading-tight sm:text-4xl">
              Мы на связи — напишите в Telegram или VK.
            </h2>
            <p className="mt-4 max-w-xl text-sm leading-6 text-slate-300">
              По вопросам заказа, доставки и возврата.
            </p>
          </div>

          <div className="grid gap-3 rounded-2xl border border-white/10 bg-ink-900/40 p-6 text-sm text-slate-200">
            <a
              className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 transition hover:border-white/20 hover:bg-white/[0.06]"
              href={support.telegram}
              rel="noreferrer"
              target="_blank"
            >
              <span className="font-bold">Telegram</span>
              <span className="text-slate-300">t.me/animeattire</span>
            </a>
            <a
              className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 transition hover:border-white/20 hover:bg-white/[0.06]"
              href={support.vk}
              rel="noreferrer"
              target="_blank"
            >
              <span className="font-bold">VK</span>
              <span className="text-slate-300">vk.com/animeattre</span>
            </a>
            <a
              className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 transition hover:border-white/20 hover:bg-white/[0.06]"
              href={support.phoneHref}
            >
              <span className="font-bold">Телефон</span>
              <span className="text-slate-300">{support.phoneDisplay}</span>
            </a>
            <div className="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3">
              <div className="font-bold">Адрес</div>
              <div className="mt-1 text-slate-300">{support.address}</div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
