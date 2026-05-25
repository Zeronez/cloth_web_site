"use client";

import Link from "next/link";

import { useRecommendationHistoryStore } from "../../stores/recommendation-history-store";

const dateFormatter = new Intl.DateTimeFormat("ru-RU", {
  day: "2-digit",
  month: "short",
  hour: "2-digit",
  minute: "2-digit"
});

const money = new Intl.NumberFormat("ru-RU", {
  style: "currency",
  currency: "RUB"
});

const confidenceLabel: Record<string, string> = {
  none: "Нужны данные",
  low: "Предварительно",
  medium: "Хорошее совпадение",
  high: "Высокая точность"
};

export function RecommendationHistoryPanel({
  scopeKey,
  title = "История рекомендаций",
  description = "Сохранённые и просмотренные рекомендации можно быстро сравнить позже.",
  emptyTitle = "История пока пустая",
  emptyText = "Откройте товар с smart fitting или сохраните образ, чтобы он появился здесь.",
  maxItems = 6
}: {
  scopeKey: string;
  title?: string;
  description?: string;
  emptyTitle?: string;
  emptyText?: string;
  maxItems?: number;
}) {
  const entries = useRecommendationHistoryStore((state) =>
    state.entries
      .filter((entry) => entry.scopeKey === scopeKey)
      .sort((left, right) => {
        if (left.savedAt && !right.savedAt) {
          return -1;
        }

        if (!left.savedAt && right.savedAt) {
          return 1;
        }

        return right.viewedAt.localeCompare(left.viewedAt);
      })
      .slice(0, maxItems)
  );
  const toggleSaved = useRecommendationHistoryStore((state) => state.toggleSaved);
  const removeEntry = useRecommendationHistoryStore((state) => state.removeEntry);

  return (
    <section className="border border-white/10 bg-white/[0.04] p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-black uppercase text-neon-amber">Smart fitting</p>
          <h2 className="mt-3 text-2xl font-black text-white">{title}</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">{description}</p>
        </div>
        <Link
          href="/fitting"
          className="inline-flex h-11 items-center border border-neon-teal/30 bg-neon-teal/10 px-5 text-sm font-semibold text-ice transition hover:bg-neon-teal/20"
        >
          Открыть wizard
        </Link>
      </div>

      {entries.length === 0 ? (
        <div className="mt-6 border border-dashed border-white/10 bg-black/10 p-5">
          <h3 className="text-lg font-black text-white">{emptyTitle}</h3>
          <p className="mt-2 text-sm leading-6 text-slate-400">{emptyText}</p>
        </div>
      ) : (
        <div className="mt-6 space-y-4">
          {entries.map((entry) => (
            <article
              key={entry.id}
              className="border border-white/10 bg-black/10 p-4"
              data-testid="recommendation-history-entry"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="border border-white/10 bg-white/5 px-2 py-1 text-[11px] font-black uppercase text-slate-300">
                      {entry.categoryName}
                    </span>
                    <span className="border border-white/10 bg-black/20 px-2 py-1 text-[11px] font-semibold uppercase text-slate-400">
                      {confidenceLabel[entry.confidence] ?? entry.confidence}
                    </span>
                    {entry.savedAt ? (
                      <span className="border border-neon-crimson/40 bg-neon-crimson/10 px-2 py-1 text-[11px] font-black uppercase text-white">
                        Сохранено
                      </span>
                    ) : null}
                  </div>
                  <Link
                    href={`/products/${entry.productSlug}`}
                    className="mt-3 block text-lg font-black text-white transition hover:text-neon-teal"
                  >
                    {entry.productName}
                  </Link>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{entry.summary}</p>
                </div>
                <div className="text-right text-xs uppercase text-slate-500">
                  Просмотрено
                  <br />
                  {dateFormatter.format(new Date(entry.viewedAt))}
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-4 text-sm text-slate-300">
                <span>
                  Размер: <strong className="text-white">{entry.recommendedSize ?? "—"}</strong>
                </span>
                <span>Образов: {entry.outfit.items.length}</span>
                {entry.outfit.totalPrice ? (
                  <span>Итого: {money.format(Number(entry.outfit.totalPrice))}</span>
                ) : null}
              </div>

              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => toggleSaved(entry.id)}
                  className="h-10 border border-white/15 bg-white/5 px-4 text-sm font-semibold text-white transition hover:border-neon-crimson/60 hover:bg-white/10"
                >
                  {entry.savedAt ? "Убрать из сохранённого" : "Сохранить для сравнения"}
                </button>
                <button
                  type="button"
                  onClick={() => removeEntry(entry.id)}
                  className="h-10 border border-white/10 bg-black/20 px-4 text-sm font-semibold text-slate-300 transition hover:border-white/30 hover:text-white"
                >
                  Удалить
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
