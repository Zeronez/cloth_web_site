"use client";

import { FormEvent, useMemo, useState } from "react";

import {
  ApiError,
  createContactRequest,
  type ContactRequestInput,
  type ContactRequestTopic
} from "../../lib/api";

type ContactFormState = ContactRequestInput;

const initialFormState: ContactFormState = {
  name: "",
  email: "",
  phone: "",
  topic: "other",
  order_number: "",
  message: ""
};

type TopicOption = {
  value: ContactRequestTopic;
  label: string;
  description: string;
};

function getErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Не удалось отправить обращение. Попробуйте ещё раз.";
}

export function ContactPage() {
  const [form, setForm] = useState<ContactFormState>(initialFormState);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const supportEmail = process.env.NEXT_PUBLIC_SUPPORT_EMAIL ?? "";
  const supportPhone = process.env.NEXT_PUBLIC_SUPPORT_PHONE ?? "";
  const supportTelegram = process.env.NEXT_PUBLIC_SUPPORT_TELEGRAM ?? "";

  const topicOptions = useMemo<TopicOption[]>(
    () => [
      {
        value: "order",
        label: "Вопрос по заказу",
        description: "Статус заказа, оплата, изменение данных или уточнения."
      },
      {
        value: "delivery",
        label: "Доставка",
        description: "Сроки, адрес, курьер и изменения по доставке."
      },
      {
        value: "return",
        label: "Возврат или обмен",
        description: "Возврат, обмен размера или проверка брака."
      },
      {
        value: "product",
        label: "Товар или размер",
        description: "Вопросы по посадке, материалам, наличию и подбору размера."
      },
      {
        value: "partnership",
        label: "Партнёрство",
        description: "Коммерческие предложения, коллаборации и опт."
      },
      {
        value: "other",
        label: "Другое",
        description: "Если вопрос не подходит под другие темы."
      }
    ],
    []
  );

  function updateField<K extends keyof ContactFormState>(
    name: K,
    value: ContactFormState[K]
  ) {
    setForm((current) => ({
      ...current,
      [name]: value
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    setIsSubmitting(true);

    try {
      await createContactRequest({
        name: form.name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim(),
        topic: form.topic,
        order_number: form.order_number.trim(),
        message: form.message.trim()
      });

      setSuccess(
        "Спасибо. Сообщение отправлено, мы ответим по указанным контактам."
      );
      setForm(initialFormState);
    } catch (submittedError) {
      setError(getErrorMessage(submittedError));
    } finally {
      setIsSubmitting(false);
    }
  }

  const statusId = "contact-form-status";

  return (
    <main className="bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
      <section className="mx-auto max-w-7xl">
        <div className="max-w-3xl">
          <p className="text-xs font-black uppercase tracking-[0.24em] text-neon-teal">
            Контакты AnimeAttire
          </p>
          <h1 className="mt-4 text-4xl font-black leading-tight sm:text-5xl">
            Напишите нам по заказу, доставке или возврату.
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-8 text-slate-300 sm:text-lg">
            Заполните форму — обращение попадёт в поддержку. Обычно отвечаем в
            течение дня.
          </p>
        </div>

        <div className="mt-10 grid gap-10 lg:grid-cols-[minmax(0,1fr)_18rem]">
          <form className="space-y-6" onSubmit={(event) => void handleSubmit(event)}>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-slate-200">
                  Имя
                </span>
                <input
                  required
                  name="name"
                  type="text"
                  autoComplete="name"
                  value={form.name}
                  onChange={(event) => updateField("name", event.target.value)}
                  className="h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition placeholder:text-slate-500 focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30"
                />
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-slate-200">
                  Email
                </span>
                <input
                  required
                  name="email"
                  type="email"
                  autoComplete="email"
                  value={form.email}
                  onChange={(event) => updateField("email", event.target.value)}
                  className="h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition placeholder:text-slate-500 focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30"
                />
              </label>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-slate-200">
                  Телефон
                </span>
                <input
                  name="phone"
                  type="tel"
                  autoComplete="tel"
                  value={form.phone}
                  onChange={(event) => updateField("phone", event.target.value)}
                  className="h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition placeholder:text-slate-500 focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30"
                />
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-slate-200">
                  Тема
                </span>
                <select
                  name="topic"
                  value={form.topic}
                  onChange={(event) =>
                    updateField("topic", event.target.value as ContactRequestTopic)
                  }
                  className="h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30"
                >
                  {topicOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-slate-200">
                Номер заказа (если есть)
              </span>
              <input
                name="order_number"
                type="text"
                autoComplete="off"
                value={form.order_number}
                onChange={(event) =>
                  updateField("order_number", event.target.value)
                }
                className="h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition placeholder:text-slate-500 focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-slate-200">
                Сообщение
              </span>
              <textarea
                required
                name="message"
                rows={7}
                minLength={20}
                value={form.message}
                onChange={(event) => updateField("message", event.target.value)}
                className="w-full border border-white/10 bg-ink-900/80 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30"
              />
            </label>

            <div className="space-y-3" id={statusId} aria-live="polite">
              {error ? (
                <div
                  role="alert"
                  className="border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100"
                >
                  {error}
                </div>
              ) : null}

              {success ? (
                <div
                  role="status"
                  className="border border-neon-teal/30 bg-neon-teal/10 px-4 py-3 text-sm leading-6 text-ice"
                >
                  {success}
                </div>
              ) : null}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="flex h-12 w-full items-center justify-center bg-neon-crimson px-6 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? "Отправляем..." : "Отправить сообщение"}
            </button>
          </form>

          <aside className="space-y-6 border-t border-white/10 pt-6 lg:border-l lg:border-t-0 lg:pl-8 lg:pt-0">
            <div>
              <h2 className="text-2xl font-black text-white">Контакты</h2>
              {supportEmail || supportPhone || supportTelegram ? (
                <ul className="mt-3 space-y-2 text-sm leading-7 text-slate-300">
                  {supportEmail ? <li>Email: {supportEmail}</li> : null}
                  {supportPhone ? <li>Телефон: {supportPhone}</li> : null}
                  {supportTelegram ? <li>Telegram: {supportTelegram}</li> : null}
                </ul>
              ) : (
                <p className="mt-3 text-sm leading-7 text-slate-300">
                  Контакты поддержки пока не настроены. Используйте форму выше —
                  она работает всегда.
                </p>
              )}
            </div>

            <div>
              <h2 className="text-2xl font-black text-white">Что можно написать</h2>
              <p className="mt-3 text-sm leading-7 text-slate-300">
                Поддержка принимает обращения по заказам, доставке, возвратам,
                подбору размера и партнёрским предложениям.
              </p>
            </div>

            <dl className="space-y-4">
              {topicOptions.map((option) => (
                <div
                  key={option.value}
                  className="border border-white/10 bg-white/[0.04] p-4"
                >
                  <dt className="text-sm font-black text-white">{option.label}</dt>
                  <dd className="mt-2 text-sm leading-6 text-slate-400">
                    {option.description}
                  </dd>
                </div>
              ))}
            </dl>
          </aside>
        </div>
      </section>
    </main>
  );
}

