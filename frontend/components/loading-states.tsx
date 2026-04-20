export function CatalogGridSkeleton() {
  return (
    <div className="grid auto-rows-[260px] gap-4 md:grid-cols-2 xl:grid-cols-3">
      {[0, 1, 2, 3, 4, 5].map((item) => (
        <div
          key={item}
          className={`animate-pulse border border-white/10 bg-white/[0.04] p-5 ${
            item === 0 ? "md:col-span-2 md:row-span-2" : ""
          }`}
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
