import Link from "next/link";
import type { ReactNode } from "react";

export type LegalSection = {
  title: string;
  paragraphs?: string[];
  bullets?: string[];
  note?: string;
};

type LegalPageProps = {
  eyebrow: string;
  title: string;
  intro: string;
  updatedAt: string;
  backHref?: string;
  backLabel?: string;
  sections: LegalSection[];
  sidebarTitle?: string;
  sidebarItems?: Array<{
    label: string;
    value: ReactNode;
  }>;
};

function SectionBody({ section }: { section: LegalSection }) {
  return (
    <div className="mt-4 space-y-4">
      {section.paragraphs?.map((paragraph) => (
        <p key={paragraph} className="text-sm leading-7 text-slate-300">
          {paragraph}
        </p>
      ))}

      {section.bullets?.length ? (
        <ul className="space-y-2 text-sm leading-7 text-slate-300">
          {section.bullets.map((bullet) => (
            <li key={bullet} className="flex gap-3">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 bg-neon-teal" />
              <span>{bullet}</span>
            </li>
          ))}
        </ul>
      ) : null}

      {section.note ? (
        <p className="border-l-2 border-neon-crimson pl-4 text-sm leading-7 text-slate-400">
          {section.note}
        </p>
      ) : null}
    </div>
  );
}

export function LegalPage({
  eyebrow,
  title,
  intro,
  updatedAt,
  backHref = "/catalog",
  backLabel = "Вернуться в каталог",
  sections,
  sidebarTitle,
  sidebarItems
}: LegalPageProps) {
  return (
    <main className="bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
      <section className="mx-auto max-w-7xl">
        <div className="max-w-3xl">
          <p className="text-xs font-black uppercase tracking-[0.24em] text-neon-teal">
            {eyebrow}
          </p>
          <h1 className="mt-4 text-4xl font-black leading-tight sm:text-5xl">
            {title}
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-8 text-slate-300 sm:text-lg">
            {intro}
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-4 text-sm">
            <span className="text-slate-500">{updatedAt}</span>
            <Link
              href={backHref}
              className="font-semibold text-slate-200 transition hover:text-white"
            >
              {backLabel}
            </Link>
          </div>
        </div>

        <div className="mt-12 grid gap-10 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div className="space-y-10">
            {sections.map((section) => (
              <section key={section.title} className="border-t border-white/10 pt-8">
                <h2 className="text-2xl font-black text-white">{section.title}</h2>
                <SectionBody section={section} />
              </section>
            ))}
          </div>

          {sidebarItems?.length ? (
            <aside className="border-t border-white/10 pt-8 lg:pt-0">
              {sidebarTitle ? (
                <h2 className="text-lg font-black text-white">{sidebarTitle}</h2>
              ) : null}
              <dl className="mt-4 space-y-4 text-sm">
                {sidebarItems.map((item) => (
                  <div
                    key={item.label}
                    className="border border-white/10 bg-white/[0.04] p-4"
                  >
                    <dt className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">
                      {item.label}
                    </dt>
                    <dd className="mt-2 leading-6 text-slate-200">{item.value}</dd>
                  </div>
                ))}
              </dl>
            </aside>
          ) : null}
        </div>
      </section>
    </main>
  );
}
