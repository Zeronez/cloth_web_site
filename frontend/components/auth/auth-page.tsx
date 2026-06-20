"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, KeyboardEvent, useMemo, useState } from "react";

import { ApiError, fetchMe, loginUser, registerUser } from "../../lib/api";
import { mergeGuestCartIntoServer } from "../../lib/cart-sync";
import { useCartStore } from "../../stores/cart-store";
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
  privacy_policy_accepted: boolean;
  offer_agreement_accepted: boolean;
  marketing_opt_in: boolean;
};

type ConsentFieldName =
  | "privacy_policy_accepted"
  | "offer_agreement_accepted"
  | "marketing_opt_in";

type TextFieldName = Exclude<keyof FormState, ConsentFieldName>;

const initialFormState: FormState = {
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
  first_name: "",
  last_name: "",
  phone: "",
  privacy_policy_accepted: false,
  offer_agreement_accepted: false,
  marketing_opt_in: false
};

type FieldConfig = {
  name: TextFieldName;
  label: string;
  type: string;
  autoComplete: string;
};

type FieldErrorState = Partial<Record<TextFieldName | ConsentFieldName, string>>;

const fieldLabels: Record<TextFieldName | ConsentFieldName, string> = {
  username: "Логин",
  email: "Email",
  password: "Пароль",
  confirmPassword: "Повторите пароль",
  first_name: "Имя",
  last_name: "Фамилия",
  phone: "Телефон",
  privacy_policy_accepted: "Политика конфиденциальности",
  offer_agreement_accepted: "Оферта",
  marketing_opt_in: "Подписка на новости"
};

function formatRussianPhoneInput(value: string) {
  const digits = value.replace(/\D/g, "");

  if (!digits) {
    return "";
  }

  const normalizedDigits = (() => {
    if (digits.startsWith("8")) {
      return `7${digits.slice(1)}`;
    }

    if (digits.startsWith("7")) {
      return digits;
    }

    return `7${digits}`;
  })().slice(0, 11);

  const countryCode = normalizedDigits[0];
  const areaCode = normalizedDigits.slice(1, 4);
  const prefix = normalizedDigits.slice(4, 7);
  const linePartOne = normalizedDigits.slice(7, 9);
  const linePartTwo = normalizedDigits.slice(9, 11);

  let formatted = `+${countryCode}`;

  if (areaCode) {
    formatted += ` (${areaCode}`;
  }

  if (areaCode.length === 3) {
    formatted += ")";
  }

  if (prefix) {
    formatted += ` ${prefix}`;
  }

  if (linePartOne) {
    formatted += `-${linePartOne}`;
  }

  if (linePartTwo) {
    formatted += `-${linePartTwo}`;
  }

  return formatted;
}

function normalizeRussianPhoneForSubmit(value: string) {
  const digits = value.replace(/\D/g, "");

  if (!digits) {
    return "";
  }

  if (digits.startsWith("8")) {
    return `+7${digits.slice(1, 11)}`;
  }

  if (digits.startsWith("7")) {
    return `+${digits.slice(0, 11)}`;
  }

  return `+7${digits.slice(0, 10)}`;
}

function removePhoneDigitAt(value: string, digitIndex: number) {
  const digits = value.replace(/\D/g, "");

  if (!digits || digitIndex < 0 || digitIndex >= digits.length) {
    return value;
  }

  if (digits.length === 1) {
    return "";
  }

  const nextDigits = `${digits.slice(0, digitIndex)}${digits.slice(digitIndex + 1)}`;
  return formatRussianPhoneInput(nextDigits);
}

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
    eyebrow: "",
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
    if (error.status >= 500) {
      return "Сервис временно недоступен. Попробуйте позже.";
    }
    if (error.status === 429) {
      return "Слишком много попыток. Подождите немного и попробуйте снова.";
    }
    if (error.status === 401) {
      return "Неверный логин или пароль.";
    }
    return error.message || "Не удалось выполнить запрос. Попробуйте ещё раз.";
  }

  if (error instanceof TypeError) {
    return "Не удалось связаться с сервером. Проверьте интернет и попробуйте позже.";
  }

  return "Произошла ошибка. Попробуйте позже.";
}

function extractMessageFromDetail(detail: unknown) {
  if (typeof detail === "string") {
    return detail;
  }

  if (
    detail &&
    typeof detail === "object" &&
    "message" in detail &&
    typeof (detail as { message?: unknown }).message === "string"
  ) {
    return (detail as { message: string }).message;
  }

  return null;
}

function extractFieldErrors(error: unknown) {
  if (!(error instanceof ApiError) || !error.payload || typeof error.payload !== "object") {
    return { fieldErrors: {} as FieldErrorState, generalError: getErrorMessage(error) };
  }

  const payload = error.payload as Record<string, unknown>;
  const envelope =
    payload.error && typeof payload.error === "object"
      ? (payload.error as Record<string, unknown>)
      : null;
  const details =
    envelope?.details && typeof envelope.details === "object"
      ? (envelope.details as Record<string, unknown>)
      : payload;

  const fieldErrors: FieldErrorState = {};
  let generalError =
    typeof envelope?.message === "string" ? envelope.message : null;

  for (const [key, rawValue] of Object.entries(details)) {
    if (key === "non_field_errors" || key === "detail" || key === "error") {
      const message = Array.isArray(rawValue)
        ? extractMessageFromDetail(rawValue[0])
        : extractMessageFromDetail(rawValue);

      if (message) {
        generalError = message;
      }

      continue;
    }

    const message = Array.isArray(rawValue)
      ? extractMessageFromDetail(rawValue[0])
      : extractMessageFromDetail(rawValue);

    if (message && key in fieldLabels) {
      fieldErrors[key as keyof FieldErrorState] = message;
    }
  }

  return {
    fieldErrors,
    generalError:
      Object.keys(fieldErrors).length > 0 && generalError === "Проверьте введенные данные."
        ? null
        : generalError
  };
}

function AuthSidePanel({ mode }: { mode: Mode }) {
  const copy = authCopy[mode];

  return (
    <div className="space-y-8">
      <div className="max-w-xl">
        {copy.eyebrow ? (
          <p className="text-xs font-black uppercase text-neon-teal">
            {copy.eyebrow}
          </p>
        ) : null}
        <h1
          className={`text-4xl font-black leading-tight sm:text-5xl ${
            copy.eyebrow ? "mt-4" : ""
          }`}
        >
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
            <p className="mt-1 text-xs uppercase text-slate-400">{label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AuthPage({ mode }: { mode: Mode }) {
  const router = useRouter();
  const setSession = useUserStore((state) => state.setSession);
  const setCartItems = useCartStore((state) => state.setItems);
  const [form, setForm] = useState<FormState>(initialFormState);
  const [fieldErrors, setFieldErrors] = useState<FieldErrorState>({});
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

  function updateField(name: keyof FormState, value: string | boolean) {
    setFieldErrors((current) => {
      if (!current[name as keyof FieldErrorState]) {
        return current;
      }

      const next = { ...current };
      delete next[name as keyof FieldErrorState];
      return next;
    });

    setForm((current) => {
      if (name === "phone" && typeof value === "string") {
        return {
          ...current,
          phone: formatRussianPhoneInput(value)
        };
      }

      return { ...current, [name]: value };
    });
  }

  function validateForm() {
    const nextFieldErrors: FieldErrorState = {};

    if (!form.username.trim()) {
      nextFieldErrors.username = "Укажите логин.";
    }

    if (mode === "login") {
      if (!form.password) {
        nextFieldErrors.password = "Укажите пароль.";
      }

      return nextFieldErrors;
    }

    if (!form.email.trim()) {
      nextFieldErrors.email = "Укажите email.";
    }

    if (!form.first_name.trim()) {
      nextFieldErrors.first_name = "Укажите имя.";
    }

    if (!form.last_name.trim()) {
      nextFieldErrors.last_name = "Укажите фамилию.";
    }

    if (!form.phone.trim()) {
      nextFieldErrors.phone = "Укажите телефон.";
    } else if (!/^\+7\d{10}$/.test(normalizeRussianPhoneForSubmit(form.phone))) {
      nextFieldErrors.phone = "Введите телефон в формате +7 (999) 123-45-67.";
    }

    if (!form.password) {
      nextFieldErrors.password = "Укажите пароль.";
    } else if (form.password.length < 8) {
      nextFieldErrors.password = "Пароль должен содержать минимум 8 символов.";
    }

    if (!form.confirmPassword) {
      nextFieldErrors.confirmPassword = "Повторите пароль.";
    } else if (form.password !== form.confirmPassword) {
      nextFieldErrors.confirmPassword = "Пароли не совпадают.";
    }

    if (!form.privacy_policy_accepted) {
      nextFieldErrors.privacy_policy_accepted =
        "Нужно принять политику конфиденциальности.";
    }

    if (!form.offer_agreement_accepted) {
      nextFieldErrors.offer_agreement_accepted = "Нужно принять оферту.";
    }

    return nextFieldErrors;
  }

  function handlePhoneKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key !== "Backspace") {
      return;
    }

    const input = event.currentTarget;
    const selectionStart = input.selectionStart ?? 0;
    const selectionEnd = input.selectionEnd ?? 0;

    if (selectionStart !== selectionEnd || selectionStart === 0) {
      return;
    }

    const previousCharacter = input.value[selectionStart - 1];

    if (/\d/.test(previousCharacter)) {
      return;
    }

    const digitsBeforeCaret = input.value
      .slice(0, selectionStart)
      .replace(/\D/g, "").length;

    event.preventDefault();

    if (digitsBeforeCaret <= 1) {
      updateField("phone", "");
      return;
    }

    updateField("phone", removePhoneDigitAt(input.value, digitsBeforeCaret - 1));
  }

  async function syncGuestCartAfterAuth(accessToken: string) {
    const guestItems = useCartStore.getState().items;
    const { items } = await mergeGuestCartIntoServer(accessToken, guestItems);
    setCartItems(items);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    setFieldErrors({});

    const nextFieldErrors = validateForm();

    if (Object.keys(nextFieldErrors).length > 0) {
      setFieldErrors(nextFieldErrors);
      setError("Проверьте заполнение формы.");
      return;
    }

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
        await syncGuestCartAfterAuth(tokens.access);
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
        phone: normalizeRussianPhoneForSubmit(form.phone),
        privacy_policy_accepted: form.privacy_policy_accepted,
        offer_agreement_accepted: form.offer_agreement_accepted,
        marketing_opt_in: form.marketing_opt_in
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
      await syncGuestCartAfterAuth(tokens.access);
      setSuccess("Аккаунт создан, вход выполнен автоматически.");
      router.replace("/account");
      router.refresh();
    } catch (submittedError) {
      const extractedErrors = extractFieldErrors(submittedError);
      setFieldErrors(extractedErrors.fieldErrors);
      setError(extractedErrors.generalError);
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
              <h2 className="text-2xl font-black sm:text-3xl">
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

          <form className="mt-8 space-y-5" onSubmit={handleSubmit} noValidate>
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
                    onChange={(event) => updateField(field.name, event.target.value)}
                    onKeyDown={field.name === "phone" ? handlePhoneKeyDown : undefined}
                    placeholder={field.name === "phone" ? "+7 (___) ___-__-__" : undefined}
                    inputMode={field.name === "phone" ? "tel" : undefined}
                    aria-invalid={Boolean(fieldErrors[field.name])}
                    className={`h-12 w-full border bg-ink-900/80 px-4 text-white outline-none transition placeholder:text-slate-500 focus:ring-2 ${
                      fieldErrors[field.name]
                        ? "border-red-400/80 focus:border-red-400 focus:ring-red-400/20"
                        : "border-white/10 focus:border-neon-teal focus:ring-neon-teal/30"
                    } ${
                      field.name === "password" || field.name === "confirmPassword"
                        ? "sm:col-span-2"
                        : ""
                    }`}
                  />
                  {fieldErrors[field.name] ? (
                    <span className="mt-2 block text-sm text-red-200">
                      {fieldErrors[field.name]}
                    </span>
                  ) : null}
                </label>
              ))}
            </div>

            {mode === "register" ? (
              <div className="space-y-3 border border-white/10 bg-ink-900/50 p-4">
                {[
                  {
                    name: "privacy_policy_accepted" as ConsentFieldName,
                    label:
                      "Принимаю политику конфиденциальности и обработку персональных данных",
                    required: true
                  },
                  {
                    name: "offer_agreement_accepted" as ConsentFieldName,
                    label: "Принимаю оферту и условия продажи",
                    required: true
                  },
                  {
                    name: "marketing_opt_in" as ConsentFieldName,
                    label: "Хочу получать новости о дропах и специальных предложениях",
                    required: false
                  }
                ].map((field) => (
                  <label
                    key={field.name}
                    className="flex items-start gap-3 text-sm leading-6 text-slate-200"
                  >
                    <input
                      type="checkbox"
                      checked={Boolean(form[field.name])}
                      onChange={(event) =>
                        updateField(field.name, event.target.checked)
                      }
                      required={field.required}
                      aria-invalid={Boolean(fieldErrors[field.name])}
                      className="mt-1 h-4 w-4 border-white/20 bg-ink-900 text-neon-teal focus:ring-neon-teal"
                    />
                    <span>{field.label}</span>
                  </label>
                ))}
                {fieldErrors.privacy_policy_accepted || fieldErrors.offer_agreement_accepted ? (
                  <div className="text-sm text-red-200">
                    {fieldErrors.privacy_policy_accepted ?? fieldErrors.offer_agreement_accepted}
                  </div>
                ) : null}
              </div>
            ) : null}

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
                Пароль должен быть достаточно сложным и не совпадать с данными из
                других сервисов.
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
