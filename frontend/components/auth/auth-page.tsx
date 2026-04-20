"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";
import {
  ApiError,
  fetchMe,
  loginUser,
  registerUser
} from "../../lib/api";
import { useUserStore } from "../../stores/user-store";

type Mode = "login" | "register";

type FormState = {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  first_name: string;
  last_name: string;
  phone: string;
};

const initialFormState: FormState = {
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
  first_name: "",
  last_name: "",
  phone: ""
};

type FieldConfig = {
  name: keyof FormState;
  label: string;
  type: string;
  autoComplete: string;
};

const authCopy: Record<
  Mode,
  {
    eyebrow: string;
    title: string;
    description: string;
    primaryLabel: string;
    switchLabel: string;
    switchHref: string;
  }
> = {
  login: {
    eyebrow: "Вход в аккаунт",
    title: "Продолжите покупки без лишних шагов.",
    description:
      "Сохраните корзину, проверьте адреса доставки и быстрее возвращайтесь к заказу.",
    primaryLabel: "Войти",
    switchLabel: "Нет аккаунта? Зарегистрироваться",
    switchHref: "/register"
  },
  register: {
    eyebrow: "Создание аккаунта",
    title: "Один профиль для заказов, адресов и истории.",
    description:
      "Зарегистрируйтесь один раз, чтобы в пару кликов оформлять доставку и управлять данными.",
    primaryLabel: "Создать аккаунт",
    switchLabel: "Уже есть аккаунт? Войти",
    switchHref: "/login"
  }
};

function getErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Не удалось выполнить запрос. Попробуйте еще раз.";
}

function AuthSidePanel({ mode }: { mode: Mode }) {
  const copy = authCopy[mode];

  return (
    <div className="space-y-8">
      <div className="max-w-xl">
        <p className="text-xs font-black uppercase text-neon-teal">
          {copy.eyebrow}
        </p>
        <h1 className="mt-4 text-4xl font-black leading-tight sm:text-5xl">
          {copy.title}
        </h1>
        <p className="mt-5 max-w-lg text-base leading-7 text-slate-300 sm:text-lg">
          {copy.description}
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        {[
          ["JWT", "Безопасная сессия"],
          ["Profile", "Профиль и адреса"],
          ["Fast", "Быстрый возврат к заказу"]
        ].map(([value, label]) => (
          <div key={label} className="border border-white/10 bg-white/[0.04] p-4">
            <p className="text-xl font-black text-white">{value}</p>
            <p className="mt-1 text-xs uppercase text-slate-400">
              {label}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AuthPage({ mode }: { mode: Mode }) {
  const router = useRouter();
  const setSession = useUserStore((state) => state.setSession);
  const [form, setForm] = useState<FormState>(initialFormState);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const copy = authCopy[mode];

  const fields = useMemo<FieldConfig[]>(
    () =>
      mode === "login"
        ? [
            { name: "username", label: "Логин", type: "text", autoComplete: "username" },
            {
              name: "password",
              label: "Пароль",
              type: "password",
              autoComplete: "current-password"
            }
          ]
        : [
            { name: "username", label: "Логин", type: "text", autoComplete: "username" },
            { name: "email", label: "Email", type: "email", autoComplete: "email" },
            { name: "first_name", label: "Имя", type: "text", autoComplete: "given-name" },
            { name: "last_name", label: "Фамилия", type: "text", autoComplete: "family-name" },
            { name: "phone", label: "Телефон", type: "tel", autoComplete: "tel" },
            {
              name: "password",
              label: "Пароль",
              type: "password",
              autoComplete: "new-password"
            },
            {
              name: "confirmPassword",
              label: "Повторите пароль",
              type: "password",
              autoComplete: "new-password"
            }
          ],
    [mode]
  );

  function updateField(name: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    if (mode === "register" && form.password !== form.confirmPassword) {
      setError("Пароли не совпадают.");
      return;
    }

    setIsSubmitting(true);

    try {
      if (mode === "login") {
        const tokens = await loginUser({
          username: form.username,
          password: form.password
        });
        const profile = await fetchMe(tokens.access);

        setSession({
          accessToken: tokens.access,
          refreshToken: tokens.refresh,
          profile
        });
        router.replace("/account");
        router.refresh();
        return;
      }

      await registerUser({
        username: form.username,
        email: form.email,
        password: form.password,
        first_name: form.first_name,
        last_name: form.last_name,
        phone: form.phone
      });

      const tokens = await loginUser({
        username: form.username,
        password: form.password
      });
      const profile = await fetchMe(tokens.access);

      setSession({
        accessToken: tokens.access,
        refreshToken: tokens.refresh,
        profile
      });
      setSuccess("Аккаунт создан, вход выполнен автоматически.");
      router.replace("/account");
      router.refresh();
    } catch (submittedError) {
      setError(getErrorMessage(submittedError));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-ink-950 px-4 pb-16 pt-28 text-white sm:px-6 lg:px-8">
      <section className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[1.05fr_0.9fr] lg:items-start">
        <AuthSidePanel mode={mode} />

        <div className="border border-white/10 bg-white/[0.04] p-6 shadow-[0_28px_80px_rgba(0,0,0,0.28)] sm:p-8">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-black uppercase text-neon-crimson">
                {copy.eyebrow}
              </p>
              <h2 className="mt-3 text-2xl font-black sm:text-3xl">
                {copy.primaryLabel}
              </h2>
            </div>
            <Link
              href={copy.switchHref}
              className="text-sm font-semibold text-slate-300 transition hover:text-white"
            >
              {copy.switchLabel}
            </Link>
          </div>

          <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
            <div className="grid gap-4 sm:grid-cols-2">
              {fields.map((field) => (
                <label key={field.name} className="block">
                  <span className="mb-2 block text-sm font-semibold text-slate-200">
                    {field.label}
                  </span>
                  <input
                    required
                    name={field.name}
                    type={field.type}
                    autoComplete={field.autoComplete}
                    value={form[field.name]}
                    onChange={(event) =>
                      updateField(field.name, event.target.value)
                    }
                    className={`h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition placeholder:text-slate-500 focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30 ${
                      field.name === "password" || field.name === "confirmPassword"
                        ? "sm:col-span-2"
                        : ""
                    }`}
                  />
                </label>
              ))}
            </div>

            <div className="space-y-3">
              {error ? (
                <div className="border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
                  {error}
                </div>
              ) : null}
              {success ? (
                <div className="border border-neon-teal/30 bg-neon-teal/10 px-4 py-3 text-sm leading-6 text-ice">
                  {success}
                </div>
              ) : null}
            </div>

            {mode === "register" ? (
              <p className="text-sm leading-6 text-slate-400">
                Пароль должен быть достаточно сложным и не совпадать с предыдущими
                данными из других сервисов.
              </p>
            ) : (
              <p className="text-sm leading-6 text-slate-400">
                После входа сессия сохранится в браузере, чтобы не логиниться на
                каждой странице.
              </p>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="flex h-12 w-full items-center justify-center bg-neon-crimson px-6 text-sm font-black uppercase text-white shadow-neon-crimson transition hover:bg-white hover:text-ink-950 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting
                ? mode === "login"
                  ? "Вход..."
                  : "Создание..."
                : copy.primaryLabel}
            </button>
          </form>
        </div>
      </section>
    </main>
  );
}
