"use client";

import { motion } from "framer-motion";
import Image from "next/image";

import { useCartSync } from "../../lib/use-cart-sync";
import { ProductImagePlaceholder } from "../product-image-placeholder";

const featureDrops = [
  {
    code: "01",
    id: "beige-cargo-pants",
    name: "Штаны карго | BEIGE",
    detail:
      "Оверсайз силуэт из варёного хлопка, карманы и регулировка по низу штанин.",
    price: "9 400 ₽",
    priceValue: 9400,
    variant: "pants" as const,
    defaultSize: "L",
    imageSrc: "/products/beige-cargo-pants-1.webp",
    imageAlt: "Штаны карго BEIGE"
  },
  {
    code: "02",
    id: "flash-of-the-leaf-tee",
    name: "ФУТБОЛКА | FLASH OF THE LEAF",
    detail: "Лёгкая унисекс футболка с лайкрой для идеальной посадки и активности.",
    price: "4 790 ₽",
    priceValue: 4790,
    variant: "jacket" as const,
    defaultSize: "M",
    imageSrc: "/products/flash-of-the-leaf-tee-1.webp",
    imageAlt: "Футболка FLASH OF THE LEAF"
  },
  {
    code: "03",
    id: "fate-zip-hoodie",
    name: "Худи на молнии | FATE",
    detail:
      "Интерсофт средней плотности, карман-кенгуру и удобная посадка под прохладную погоду.",
    price: "14 190 ₽",
    priceValue: 14190,
    variant: "hoodie" as const,
    defaultSize: "M",
    imageSrc: "/products/fate-zip-hoodie-1.webp",
    imageAlt: "Худи на молнии FATE"
  }
];

const motionUp = {
  hidden: { opacity: 0, y: 28 },
  visible: { opacity: 1, y: 0 }
};

const motionFade = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 }
};

const motionScale = {
  hidden: { opacity: 0, y: 22, scale: 0.96 },
  visible: { opacity: 1, y: 0, scale: 1 }
};

const staggerGroup = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.12
    }
  }
};

const sectionViewport = {
  once: true,
  amount: 0.2
} as const;

const support = {
  telegram: "https://t.me/animeattire",
  vk: "https://vk.com/animeattre",
  phoneDisplay: "+7 982 402-26-46",
  phoneHref: "tel:+79824022646",
  address: "Лиговский проспект, 76, Санкт-Петербург, 191040"
};

const testimonials = [
  {
    name: "Екатерина",
    city: "Санкт‑Петербург",
    photoSrc: "/testimonials/otzyv-1.jpg",
    photoAlt: "Фото полученного товара",
    text: "Упаковка аккуратная, принт чёткий, ткань плотная. После стирки форма не поплыла — очень довольна."
  },
  {
    name: "Илья",
    city: "Москва",
    photoSrc: "/testimonials/otzyv-2.jpg",
    photoAlt: "Фото полученного товара",
    text: "Забрал на следующий день, всё по размеру. Вживую выглядит ещё круче: детали и принт прям топ."
  },
  {
    name: "Марина",
    city: "Екатеринбург",
    photoSrc: "/testimonials/otzyv-3.jpg",
    photoAlt: "Фото полученного товара",
    text: "Сервис в чате помог подобрать размер, отправили быстро. Качество швов отличное, носить приятно."
  }
];

export function AnimeAttireHome() {
  const { addItem } = useCartSync();

  return (
    <main className="bg-ink-950 text-white">
      <section className="relative isolate min-h-[92vh] overflow-hidden border-b border-white/10 px-4 pb-16 pt-28 sm:px-6 lg:px-8">
        <div className="absolute inset-0 -z-20 bg-[linear-gradient(115deg,#002A32_0%,#00333D_60%,#002A32_100%)]" />
        <div className="absolute inset-0 -z-20 opacity-[0.16]">
          <Image
            src="/visual/drop-background.jpg"
            alt=""
            fill
            priority
            sizes="100vw"
            className="object-cover grayscale-[0.35] contrast-125"
          />
        </div>
        <div className="absolute inset-0 -z-10 opacity-[0.25] [background-image:radial-gradient(circle_at_top,rgba(255,255,255,0.08),transparent_55%)]" />
        <div className="pointer-events-none absolute inset-0 -z-10 opacity-[0.55] [background-image:linear-gradient(180deg,rgba(2,6,23,0.18)_0%,rgba(2,6,23,0.62)_55%,rgba(2,6,23,0.92)_100%)]" />

        <div className="mx-auto grid max-w-7xl items-center gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(390px,0.82fr)]">
          <motion.div
            initial="hidden"
            animate="visible"
            transition={{ staggerChildren: 0.08 }}
            className="max-w-3xl"
          >
            <motion.div variants={motionFade} className="mb-6 w-full max-w-xl">
              <Image
                src="/brand/animeattire-logo.png"
                alt="AnimeAttire"
                width={2172}
                height={724}
                priority
                className="h-auto w-full"
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
                onClick={async () => {
                  for (const drop of featureDrops) {
                    await addItem({
                      id: drop.id,
                      name: drop.name,
                      price: drop.priceValue,
                      size: drop.defaultSize
                    });
                  }
                }}
                className="h-12 rounded-full bg-white px-6 text-sm font-black uppercase text-ink-950 transition hover:bg-white/90 focus:outline-none focus:ring-2 focus:ring-white/30"
              >
                Добавить сет
              </button>
              <a
                href="#drops"
                className="grid h-12 place-items-center rounded-full border border-white/15 bg-white/5 px-6 text-sm font-black uppercase text-white transition hover:border-white/30 hover:bg-white/10"
              >
                Смотреть сеты
              </a>
            </motion.div>

            <motion.dl
              variants={staggerGroup}
              className="mt-12 grid max-w-2xl grid-cols-3 gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04]"
            >
              {[
                ["48ч", "Новые дропы"],
                ["0₽", "Доставка от"],
                ["14", "Дней на возврат"]
              ].map(([value, label]) => (
                <motion.div
                  key={label}
                  variants={motionScale}
                  whileHover={{ y: -4, backgroundColor: "rgba(2, 6, 23, 0.72)" }}
                  transition={{ duration: 0.22, ease: "easeOut" }}
                  className="bg-ink-950/60 p-4"
                >
                  <dt className="text-2xl font-black text-white">{value}</dt>
                  <dd className="mt-1 text-xs font-bold uppercase tracking-[0.18em] text-slate-400">
                    {label}
                  </dd>
                </motion.div>
              ))}
            </motion.dl>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.94, rotate: 1.5 }}
            animate={{ opacity: 1, scale: 1, rotate: 0 }}
            transition={{ duration: 0.65, ease: "easeOut" }}
            className="relative mx-auto aspect-[4/5] w-full max-w-[520px]"
          >
            <div className="relative h-full w-full overflow-hidden rounded-3xl border border-white/10 shadow-[0_24px_80px_rgba(0,0,0,0.42)]">
              <Image
                src="/visual/hero-set-week.png"
                alt="Сет недели"
                fill
                priority
                sizes="(min-width: 1024px) 520px, 90vw"
                className="object-cover"
              />
              <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(0,0,0,0.02)_0%,rgba(0,0,0,0.15)_35%,rgba(0,0,0,0.65)_100%)]" />
            </div>
            <div className="absolute right-10 top-10 rounded-full border border-white/10 bg-ink-950/80 px-3 py-2 text-xs font-black uppercase tracking-[0.18em] text-white">
              Сет недели
            </div>
          </motion.div>
        </div>
      </section>

      <motion.section
        id="drops"
        initial="hidden"
        whileInView="visible"
        viewport={sectionViewport}
        variants={staggerGroup}
        className="px-4 py-16 sm:px-6 lg:px-8"
      >
        <div className="relative mx-auto max-w-7xl">
          <motion.div
            variants={motionFade}
            className="pointer-events-none absolute -left-40 top-6 -z-10 hidden w-[320px] opacity-[0.07] xl:block"
          >
            <Image
              src="/visual/guts-berserk-manga.png"
              alt=""
              width={900}
              height={900}
              className="h-auto w-full select-none"
            />
          </motion.div>
          <motion.div
            variants={motionUp}
            className="flex flex-col justify-between gap-4 md:flex-row md:items-end"
          >
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
          </motion.div>

          <motion.div
            variants={staggerGroup}
            className="mt-10 grid gap-4 md:grid-cols-3"
          >
            {featureDrops.map((drop) => (
              <motion.article
                key={drop.code}
                variants={motionScale}
                whileHover={{ y: -8 }}
                transition={{ duration: 0.28, ease: "easeOut" }}
                className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 transition hover:border-white/20 hover:bg-white/[0.06]"
              >
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  transition={{ duration: 0.35, ease: "easeOut" }}
                  className="relative mb-6 aspect-[4/5] overflow-hidden rounded-xl border border-white/10 bg-ink-900/40"
                >
                  {drop.imageSrc ? (
                    <Image
                      src={drop.imageSrc}
                      alt={drop.imageAlt ?? drop.name}
                      fill
                      sizes="(min-width: 768px) 33vw, 100vw"
                      className="object-cover"
                    />
                  ) : (
                    <ProductImagePlaceholder
                      label={drop.name}
                      variant={drop.variant}
                      className="h-full w-full"
                    />
                  )}
                </motion.div>
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
                <button
                  type="button"
                  onClick={() =>
                    addItem({
                      id: drop.id,
                      name: drop.name,
                      price: drop.priceValue,
                      size: drop.defaultSize
                    })
                  }
                  className="mt-6 h-11 w-full rounded-full border border-white/15 bg-white/5 px-6 text-xs font-black uppercase tracking-[0.18em] text-white transition hover:border-white/30 hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-white/30"
                >
                  Добавить в корзину
                </button>
              </motion.article>
            ))}
          </motion.div>
        </div>
      </motion.section>

      <motion.section
        initial="hidden"
        whileInView="visible"
        viewport={sectionViewport}
        variants={staggerGroup}
        className="border-t border-white/10 px-4 py-16 sm:px-6 lg:px-8"
      >
        <div className="mx-auto max-w-7xl">
          <motion.div
            variants={motionUp}
            className="flex flex-col justify-between gap-4 md:flex-row md:items-end"
          >
            <div>
              <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-400">
                Отзывы
              </p>
              <h2 className="mt-3 text-3xl font-black sm:text-4xl">
                Что пишут покупатели
              </h2>
            </div>
            <p className="max-w-md text-sm leading-6 text-slate-400">
              Несколько отзывов о посадке, качестве и доставке.
            </p>
          </motion.div>

          <motion.div
            variants={staggerGroup}
            className="mt-10 grid gap-4 md:grid-cols-3"
          >
            {testimonials.map((item) => (
              <motion.figure
                key={`${item.name}-${item.city}`}
                variants={motionScale}
                whileHover={{ y: -6 }}
                transition={{ duration: 0.26, ease: "easeOut" }}
                className="rounded-2xl border border-white/10 bg-white/[0.04] p-6"
              >
                <motion.div
                  whileHover={{ scale: 1.015 }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                  className="relative mb-5 aspect-[4/3] overflow-hidden rounded-xl border border-white/10 bg-ink-900/40"
                >
                  <Image
                    src={item.photoSrc}
                    alt={item.photoAlt}
                    fill
                    sizes="(min-width: 768px) 33vw, 100vw"
                    className="object-cover"
                  />
                  <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(0,0,0,0.08),rgba(0,0,0,0.46))]" />
                </motion.div>
                <blockquote className="text-sm leading-7 text-slate-200">
                  {item.text}
                </blockquote>
                <figcaption className="mt-5 flex items-center justify-between border-t border-white/10 pt-4">
                  <div className="text-sm font-black text-white">{item.name}</div>
                  <div className="text-xs font-bold uppercase tracking-[0.18em] text-slate-400">
                    {item.city}
                  </div>
                </figcaption>
              </motion.figure>
            ))}
          </motion.div>
        </div>
      </motion.section>

      <motion.section
        initial="hidden"
        whileInView="visible"
        viewport={sectionViewport}
        variants={staggerGroup}
        className="border-t border-white/10 bg-white/[0.03] px-4 py-16 sm:px-6 lg:px-8"
      >
        <div className="mx-auto grid max-w-7xl gap-8 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <motion.div variants={motionUp} className="flex flex-col justify-center">
            <p className="text-xs font-black uppercase tracking-[0.24em] text-neon-teal">
              Соцсети и поддержка
            </p>
            <h2 className="mt-4 text-3xl font-black leading-tight sm:text-4xl">
              Мы на связи — напишите в Telegram или VK.
            </h2>
          </motion.div>

          <motion.div
            variants={motionScale}
            className="relative overflow-hidden rounded-2xl border border-white/10 bg-ink-900/40 p-6 text-sm text-slate-200"
          >
            <div className="pointer-events-none absolute inset-0 z-0 bg-[radial-gradient(circle_at_bottom_right,rgba(2,6,23,0.92),transparent_62%)]" />
            <motion.div
              animate={{ y: [0, -8, 0], rotate: [-6, -4, -6] }}
              transition={{ duration: 6.5, repeat: Infinity, ease: "easeInOut" }}
              className="pointer-events-none absolute -bottom-4 -right-16 z-0 hidden w-[220px] rotate-[-6deg] opacity-[0.28] drop-shadow-[0_40px_70px_rgba(0,0,0,0.55)] md:block"
            >
              <Image
                src="/visual/anime-girl-like.png"
                alt=""
                width={512}
                height={512}
                className="h-auto w-full select-none brightness-75 saturate-50"
              />
            </motion.div>
            <motion.div variants={staggerGroup} className="relative z-10 grid gap-3">
              <motion.a
                variants={motionUp}
                whileHover={{ x: 6 }}
                transition={{ duration: 0.2, ease: "easeOut" }}
                className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 transition hover:border-white/20 hover:bg-white/[0.06]"
                href={support.telegram}
                rel="noreferrer"
                target="_blank"
              >
                <span className="font-bold">Telegram</span>
                <span className="text-slate-300">t.me/animeattire</span>
              </motion.a>
              <motion.a
                variants={motionUp}
                whileHover={{ x: 6 }}
                transition={{ duration: 0.2, ease: "easeOut" }}
                className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 transition hover:border-white/20 hover:bg-white/[0.06]"
                href={support.vk}
                rel="noreferrer"
                target="_blank"
              >
                <span className="font-bold">VK</span>
                <span className="text-slate-300">vk.com/animeattre</span>
              </motion.a>
              <motion.a
                variants={motionUp}
                whileHover={{ x: 6 }}
                transition={{ duration: 0.2, ease: "easeOut" }}
                className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 transition hover:border-white/20 hover:bg-white/[0.06]"
                href={support.phoneHref}
              >
                <span className="font-bold">Телефон</span>
                <span className="text-slate-300">{support.phoneDisplay}</span>
              </motion.a>
              <motion.div
                variants={motionUp}
                className="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3"
              >
                <div className="font-bold">Адрес</div>
                <div className="mt-1 text-slate-300">{support.address}</div>
              </motion.div>
            </motion.div>
          </motion.div>
        </div>
      </motion.section>
    </main>
  );
}
