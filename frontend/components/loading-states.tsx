export function CatalogGridSkeleton() {
  return (
    <div className="grid auto-rows-[minmax(320px,_auto)] gap-4 md:grid-cols-2 xl:grid-cols-3">
      {[0, 1, 2, 3, 4, 5].map((item) => (
        <div
          key={item}
          className="animate-pulse border border-white/10 bg-white/[0.04] p-5"
        >
          <div className="h-full w-full bg-[linear-gradient(135deg,rgba(255,255,255,0.08),rgba(255,255,255,0.02))]" />
        </div>
      ))}
    </div>
  );
}

export function ProductDetailSkeleton() {
  return (
    <main className="min-h-screen bg-ink-950 px-4 pb-20 pt-28 text-white sm:px-6 lg:px-8">
      <section className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[1fr_0.82fr]">
        <div className="min-h-[620px] animate-pulse border border-white/10 bg-white/[0.04]" />
        <div className="space-y-6">
          <div className="h-4 w-36 animate-pulse bg-white/10" />
          <div className="h-12 w-4/5 animate-pulse bg-white/10" />
          <div className="h-28 w-full animate-pulse bg-white/10" />
          <div className="h-20 w-full animate-pulse bg-white/10" />
          <div className="grid grid-cols-4 gap-2">
            {[0, 1, 2, 3].map((item) => (
              <div key={item} className="h-12 animate-pulse bg-white/10" />
            ))}
          </div>
          <div className="h-14 w-full animate-pulse bg-white/10" />
        </div>
      </section>
    </main>
  );
}

export function CheckoutMethodListSkeleton() {
  return (
    <div
      className="mt-4 grid gap-3 sm:grid-cols-2"
      aria-label="Загрузка способов"
    >
      {Array.from({ length: 4 }).map((_, index) => (
        <div
          key={index}
          className="animate-pulse border border-white/10 bg-ink-900/60 p-4"
        >
          <div className="h-5 w-32 bg-white/10" />
          <div className="mt-3 h-4 w-full bg-white/10" />
          <div className="mt-2 h-4 w-24 bg-white/10" />
        </div>
      ))}
    </div>
  );
}

export function CheckoutPageSkeleton() {
  return (
    <main
      className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8"
      aria-label="Загрузка оформления заказа"
    >
      <section className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[1fr_420px]">
        <div className="border border-white/10 bg-white/[0.04] p-5 sm:p-6">
          <div className="animate-pulse space-y-6">
            <div className="h-3 w-36 bg-white/10" />
            <div className="h-10 w-64 bg-white/10" />
            <div className="grid gap-4 sm:grid-cols-2">
              {Array.from({ length: 6 }).map((_, index) => (
                <div key={index} className="h-12 bg-white/10" />
              ))}
            </div>
            <CheckoutMethodListSkeleton />
            <CheckoutMethodListSkeleton />
            <div className="h-12 w-full bg-white/10" />
          </div>
        </div>
        <div className="border border-white/10 bg-white/[0.04] p-5">
          <div className="animate-pulse space-y-4">
            <div className="h-3 w-20 bg-white/10" />
            <div className="h-8 w-40 bg-white/10" />
            {Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className="h-24 bg-white/10" />
            ))}
            <div className="h-12 bg-white/10" />
          </div>
        </div>
      </section>
    </main>
  );
}

export function OrderTrackingSkeleton() {
  return (
    <main
      className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8"
      aria-label="Загрузка отслеживания заказа"
    >
      <section className="mx-auto max-w-5xl space-y-6">
        <div className="border border-white/10 bg-white/[0.04] p-6 sm:p-8">
          <div className="animate-pulse space-y-4">
            <div className="h-3 w-40 bg-white/10" />
            <div className="h-10 w-72 bg-white/10" />
            <div className="h-5 max-w-2xl bg-white/10" />
            <div className="h-5 max-w-xl bg-white/10" />
          </div>
        </div>

        <div className="grid gap-3 border border-white/10 bg-white/[0.04] p-4 sm:grid-cols-2">
          {Array.from({ length: 6 }).map((_, index) => (
            <div
              key={index}
              className="animate-pulse border border-white/10 bg-ink-900/60 p-4"
            >
              <div className="h-3 w-28 bg-white/10" />
              <div className="mt-3 h-5 w-40 bg-white/10" />
            </div>
          ))}
        </div>

        <section className="border border-white/10 bg-white/[0.04] p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-3 w-24 bg-white/10" />
            <div className="h-8 w-56 bg-white/10" />
          </div>
          <div className="mt-6 space-y-4">
            {Array.from({ length: 3 }).map((_, index) => (
              <div
                key={index}
                className="animate-pulse border border-white/10 bg-ink-900/60 p-4"
              >
                <div className="h-4 w-36 bg-white/10" />
                <div className="mt-3 h-4 w-full max-w-2xl bg-white/10" />
                <div className="mt-2 h-4 w-48 bg-white/10" />
              </div>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}

export function PaymentReturnSkeleton() {
  return (
    <main
      className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8"
      aria-label="Загрузка статуса оплаты"
    >
      <section className="mx-auto max-w-4xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-3 w-40 bg-white/10" />
          <div className="h-10 w-72 bg-white/10" />
          <div className="h-5 max-w-2xl bg-white/10" />
          <div className="h-5 max-w-xl bg-white/10" />
        </div>

        <div className="mt-6 grid gap-3 border border-white/10 bg-ink-950/50 p-4 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="animate-pulse space-y-3">
              <div className="h-3 w-24 bg-white/10" />
              <div className="h-5 w-40 bg-white/10" />
            </div>
          ))}
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          <div className="h-12 w-52 animate-pulse bg-white/10" />
          <div className="h-12 w-44 animate-pulse bg-white/10" />
        </div>
      </section>
    </main>
  );
}

export function InlineNotice({
  title,
  text,
  tone = "info"
}: {
  title: string;
  text: string;
  tone?: "info" | "warning";
}) {
  const toneClass =
    tone === "warning"
      ? "border-neon-amber/40 bg-neon-amber/10 text-neon-amber"
      : "border-neon-teal/40 bg-neon-teal/10 text-neon-teal";

  return (
    <div className={`border px-4 py-3 ${toneClass}`}>
      <p className="text-sm font-black uppercase">{title}</p>
      <p className="mt-1 text-sm leading-6 text-slate-200">{text}</p>
    </div>
  );
}
