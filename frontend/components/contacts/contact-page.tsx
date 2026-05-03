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

  return "Не удалось отправить обращение. Попробуйте еще раз.";
}

export function ContactPage() {
  const [form, setForm] = useState<ContactFormState>(initialFormState);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const topicOptions = useMemo<TopicOption[]>(
    () => [
      {
        value: "order",
        label: "Вопрос по заказу",
        description: "Подойдет для статуса заказа, оплаты и общих уточнений."
      },
      {
        value: "delivery",
        label: "Доставка",
        description: "Для сроков, адреса, курьера и пункта выдачи."
      },
      {
        value: "return",
        label: "Возврат или обмен",
        description: "Если нужен возврат, обмен размера или проверка брака."
      },
      {
        value: "product",
        label: "Товар или размер",
        description: "Для консультации по модели, посадке и наличию."
      },
      {
        value: "partnership",
        label: "Партнерство",
        description: "Для коммерческих предложений и коллабораций."
      },
      {
        value: "other",
        label: "Другое",
        description: "Если вопрос не подходит под другие категории."
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

      setSuccess("Спасибо. Сообщение отправлено, мы ответим по указанным контактам.");
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
            Заполните форму ниже, и обращение уйдет в систему поддержки. Если вопрос
            связан с заказом, номер поможет нам ответить быстрее.
          </p>
        </div>

        <div className="mt-12 grid gap-10 lg:grid-cols-[minmax(0,1fr)_360px]">
          <form
            className="space-y-6 border border-white/10 bg-white/[0.04] p-6 shadow-[0_28px_80px_rgba(0,0,0,0.28)] sm:p-8"
            onSubmit={handleSubmit}
            aria-describedby={statusId}
            aria-busy={isSubmitting}
          >
            <div className="grid gap-5 sm:grid-cols-2">
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
                  inputMode="email"
                  value={form.email}
                  onChange={(event) => updateField("email", event.target.value)}
                  className="h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition placeholder:text-slate-500 focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30"
                />
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-slate-200">
                  Телефон <span className="text-slate-500">(необязательно)</span>
                </span>
                <input
                  name="phone"
                  type="tel"
                  autoComplete="tel"
                  inputMode="tel"
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
                  required
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
                Номер заказа <span className="text-slate-500">(необязательно)</span>
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

            <p className="text-sm leading-6 text-slate-400">
              Выберите тему, которая ближе всего к вашему вопросу. Это помогает
              быстрее передать обращение в нужный поток.
            </p>

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
              <h2 className="text-2xl font-black text-white">Что можно написать</h2>
              <p className="mt-3 text-sm leading-7 text-slate-300">
                Поддержка принимает обращения по заказам, доставке, возвратам,
                подбору размера и партнерским предложениям.
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

            <div className="border border-white/10 bg-white/[0.04] p-4">
              <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">
                Совет
              </p>
              <p className="mt-2 text-sm leading-7 text-slate-300">
                Если обращение связано с заказом, укажите номер в теме или в самом
                сообщении. Так мы быстрее найдем нужную карточку.
              </p>
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}
