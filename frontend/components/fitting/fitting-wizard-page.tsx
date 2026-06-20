"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  ApiError,
  fetchFitProfile,
  updateFitProfile
} from "../../lib/api";
import {
  emptyFitProfileForm,
  fitProfileFormToPayload,
  fitProfileToForm,
  fitProfileWizardSteps,
  fitSizeOptions,
  getFitProfileCompletion,
  validateFitProfileForm,
  type FitProfileFormState
} from "../../lib/fit-profile";
import {
  getRecommendationScopeKey,
  useRecommendationHistoryStore
} from "../../stores/recommendation-history-store";
import { useFitQuizStore } from "../../stores/fit-quiz-store";
import { useUserStore } from "../../stores/user-store";

const emptyWizardDraft: Partial<FitProfileFormState> = {};

function getErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Не удалось выполнить запрос.";
}

function WizardStepBadge({
  title,
  description,
  index,
  isActive,
  isComplete,
  onClick
}: {
  title: string;
  description: string;
  index: number;
  isActive: boolean;
  isComplete: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`border p-4 text-left transition ${
        isActive
          ? "border-neon-teal bg-neon-teal/10"
          : "border-white/10 bg-white/[0.03] hover:border-white/20"
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-black uppercase text-slate-400">Шаг {index + 1}</span>
        {isComplete ? (
          <span className="text-xs font-black uppercase text-neon-teal">Готово</span>
        ) : null}
      </div>
      <h2 className="mt-3 text-lg font-black text-white">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-400">{description}</p>
    </button>
  );
}

export function FittingWizardPage() {
  const accessToken = useUserStore((state) => state.accessToken);
  const profile = useUserStore((state) => state.profile);
  const clearSession = useUserStore((state) => state.clearSession);
  const completedProfile = useFitQuizStore((state) => state.completedProfile);
  const completedAt = useFitQuizStore((state) => state.completedAt);
  const quizExtras = useFitQuizStore((state) => state.extras);
  const setCompletedProfile = useFitQuizStore((state) => state.setCompletedProfile);
  const setQuizExtras = useFitQuizStore((state) => state.setExtras);
  const scopeKey = useMemo(
    () => getRecommendationScopeKey(profile?.id),
    [profile?.id]
  );
  const wizardDraft = useRecommendationHistoryStore(
    (state) => state.wizardDrafts[scopeKey]
  );
  const currentWizardDraft = wizardDraft ?? emptyWizardDraft;
  const setWizardDraft = useRecommendationHistoryStore((state) => state.setWizardDraft);
  const clearWizardDraft = useRecommendationHistoryStore((state) => state.clearWizardDraft);
  const [stepIndex, setStepIndex] = useState(0);
  const [form, setForm] = useState<FitProfileFormState>(emptyFitProfileForm);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [didHydrateDraft, setDidHydrateDraft] = useState(false);
  const fitProfileQuery = useQuery({
    queryKey: ["fit-profile", "wizard", accessToken],
    enabled: Boolean(accessToken),
    queryFn: () => fetchFitProfile(accessToken ?? ""),
    retry: false
  });

  useEffect(() => {
    if (fitProfileQuery.error instanceof ApiError && fitProfileQuery.error.status === 401) {
      clearSession();
    }
  }, [clearSession, fitProfileQuery.error]);

  useEffect(() => {
    if (didHydrateDraft) {
      return;
    }

    if (fitProfileQuery.data) {
      setForm({
        ...fitProfileToForm(fitProfileQuery.data),
        ...currentWizardDraft
      });
      setDidHydrateDraft(true);
      return;
    }

    if (!accessToken && !didHydrateDraft && completedProfile) {
      setForm((current) => ({
        ...current,
        ...completedProfile,
        ...currentWizardDraft
      }));
      setDidHydrateDraft(true);
      return;
    }

    if (Object.keys(currentWizardDraft).length > 0) {
      setForm((current) => ({
        ...current,
        ...currentWizardDraft
      }));
      setDidHydrateDraft(true);
    }
  }, [accessToken, completedProfile, currentWizardDraft, didHydrateDraft, fitProfileQuery.data]);

  useEffect(() => {
    if (!didHydrateDraft) {
      return;
    }

    setWizardDraft(scopeKey, form);
  }, [didHydrateDraft, form, scopeKey, setWizardDraft]);

  const completion = getFitProfileCompletion(form);
  const currentStep = fitProfileWizardSteps[stepIndex];
  const stepCompletion = [
    Boolean(
      form.height_cm &&
        form.weight_kg &&
        form.chest_cm &&
        form.waist_cm &&
        form.hips_cm
    ),
    Boolean(
      form.preferred_fit &&
        form.preferred_style &&
        form.preferred_season &&
        form.tops_usual_size &&
        form.bottoms_usual_size
    ),
    true
  ];

  function updateField<Key extends keyof FitProfileFormState>(
    field: Key,
    value: FitProfileFormState[Key]
  ) {
    setSaveError(null);
    setSaveMessage(null);
    setForm((current) => ({
      ...current,
      [field]: value
    }));
  }

  async function handleSave() {
    const validationErrors = validateFitProfileForm(form, "all");
    if (validationErrors.length > 0) {
      setSaveError(validationErrors[0]);
      setSaveMessage(null);
      return;
    }

    setSaveError(null);
    setSaveMessage(null);
    clearWizardDraft(scopeKey);

    setCompletedProfile(form, quizExtras);

    if (!accessToken) {
      const top = form.tops_usual_size ? (form.tops_usual_size === "ONE_SIZE" ? "One size" : form.tops_usual_size) : "—";
      const bottom = form.bottoms_usual_size
        ? form.bottoms_usual_size === "ONE_SIZE"
          ? "One size"
          : form.bottoms_usual_size
        : "—";
      setSaveMessage(
        `Готово! По ответам чаще всего подойдут размеры: верх — ${top}, низ — ${bottom}. В каталоге включите «Подходящие товары именно вам».`
      );
      return;
    }

    setIsSaving(true);

    try {
      const updatedProfile = await updateFitProfile(
        accessToken,
        fitProfileFormToPayload(form)
      );
      setForm(fitProfileToForm(updatedProfile));
      setSaveMessage(
        "Профиль сохранён. Рекомендации по размеру и капсулы теперь считаются по обновлённым данным."
      );
      await fitProfileQuery.refetch();
    } catch (error) {
      setSaveError(getErrorMessage(error));
    } finally {
      setIsSaving(false);
    }
  }

  function handleNextStep() {
    const currentStepId = fitProfileWizardSteps[stepIndex]?.id;
    if (!currentStepId) {
      return;
    }
    const validationErrors = validateFitProfileForm(form, currentStepId);
    if (validationErrors.length > 0) {
      setSaveError(validationErrors[0]);
      setSaveMessage(null);
      return;
    }
    setStepIndex((current) => Math.min(current + 1, fitProfileWizardSteps.length - 1));
  }

  if (!accessToken) {
    return (
      <main className="min-h-screen bg-ink-950 px-4 pb-20 pt-28 text-white sm:px-6 lg:px-8">
        <section className="mx-auto grid max-w-4xl gap-6 border border-white/10 bg-white/[0.04] p-8">
          <p className="text-xs font-black uppercase text-neon-teal">Рекомендации</p>
          <h1 className="text-3xl font-black sm:text-5xl">
            Войдите, чтобы пройти тест и получать персональные рекомендации.
          </h1>
          <p className="max-w-2xl text-base leading-7 text-slate-300">
            Тест сохраняется в профиле и используется в каталоге для фильтра «Подходящие товары именно вам».
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/login"
              className="inline-flex h-11 items-center border border-white/15 bg-white/5 px-5 text-sm font-semibold text-white transition hover:border-neon-crimson/60 hover:bg-white/10"
            >
              Войти
            </Link>
            <Link
              href="/register"
              className="inline-flex h-11 items-center border border-neon-teal/30 bg-neon-teal/10 px-5 text-sm font-semibold text-ice transition hover:bg-neon-teal/20"
            >
              Создать аккаунт
            </Link>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-ink-950 px-4 pb-20 pt-28 text-white sm:px-6 lg:px-8">
      <section className="mx-auto max-w-7xl space-y-8">
        <div className="grid gap-6 border border-white/10 bg-white/[0.04] p-6 lg:grid-cols-[1.2fr_0.8fr] lg:p-8">
          <div>
            <p className="text-xs font-black uppercase text-neon-teal">Smart fitting wizard</p>
            <h1 className="mt-3 text-3xl font-black sm:text-5xl">
              Заполните fit-profile по шагам и возвращайтесь к рекомендациям позже.
            </h1>
            <p className="mt-4 max-w-3xl text-base leading-7 text-slate-300">
              Wizard работает поверх текущего fit-profile API: черновик сохраняется локально,
              а финальная версия отправляется в аккаунт одним действием.
            </p>
            {!accessToken ? (
              <div className="mt-6 border border-neon-amber/25 bg-neon-amber/10 p-4 text-sm leading-6 text-orange-100">
                <p className="font-semibold">
                  Можно пройти тест без аккаунта — результат сохранится в браузере.
                </p>
                <p className="mt-1 text-orange-100/90">
                  Войдите, если хотите сохранять результат в профиль и получать персональные рекомендации на
                  разных устройствах.
                </p>
                <div className="mt-3 flex flex-wrap gap-3">
                  <Link
                    href="/login"
                    className="inline-flex h-10 items-center border border-white/15 bg-white/5 px-4 text-xs font-semibold uppercase tracking-[0.18em] text-white transition hover:border-white/30 hover:bg-white/10"
                  >
                    Войти
                  </Link>
                </div>
              </div>
            ) : null}
            <div className="mt-6 flex flex-wrap gap-3 text-sm text-slate-300">
              <span>Готовность профиля: {completion.percent}%</span>
              <span>
                Заполнено {completion.completedCount} из {completion.totalCount} ключевых полей
              </span>
              {completedAt ? (
                <span>Последний результат: {new Date(completedAt).toLocaleString("ru-RU")}</span>
              ) : null}
            </div>
          </div>

          <div className="border border-white/10 bg-black/10 p-5">
            <p className="text-xs font-black uppercase text-neon-amber">Текущее состояние</p>
            <p className="mt-3 text-2xl font-black text-white">
              {accessToken
                ? fitProfileQuery.data?.is_complete
                  ? "Профиль готов"
                  : "Нужно уточнить посадку"
                : completedProfile
                  ? "Тест пройден"
                  : "Нужно ответить на вопросы"}
            </p>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              Черновик сохраняется автоматически в браузере. После финального сохранения
              он очищается, а история рекомендаций остаётся доступной для сравнения.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link
                href="/catalog"
                className="inline-flex h-10 items-center border border-white/15 bg-white/5 px-4 text-sm font-semibold text-white transition hover:border-white/30 hover:bg-white/10"
              >
                Перейти в каталог
              </Link>
              <Link
                href={accessToken ? "/account" : "/login"}
                className="inline-flex h-10 items-center border border-neon-teal/30 bg-neon-teal/10 px-4 text-sm font-semibold text-ice transition hover:bg-neon-teal/20"
              >
                {accessToken ? "Открыть аккаунт" : "Войти"}
              </Link>
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="space-y-4">
            {fitProfileWizardSteps.map((step, index) => (
              <WizardStepBadge
                key={step.id}
                index={index}
                title={step.title}
                description={step.description}
                isActive={stepIndex === index}
                isComplete={stepCompletion[index]}
                onClick={() => setStepIndex(index)}
              />
            ))}
          </div>

          <section className="border border-white/10 bg-white/[0.04] p-6 lg:p-8">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-xs font-black uppercase text-neon-amber">
                  {currentStep.title}
                </p>
                <h2 className="mt-3 text-2xl font-black text-white">{currentStep.description}</h2>
              </div>
              <span className="text-sm text-slate-400">
                Шаг {stepIndex + 1} из {fitProfileWizardSteps.length}
              </span>
            </div>

            {fitProfileQuery.error ? (
              <div className="mt-5 border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
                {getErrorMessage(fitProfileQuery.error)}
              </div>
            ) : null}

            {stepIndex === 0 ? (
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                {[
                  ["height_cm", "Рост, см"],
                  ["weight_kg", "Вес, кг"],
                  ["chest_cm", "Грудь, см"],
                  ["waist_cm", "Талия, см"],
                  ["hips_cm", "Бёдра, см"],
                  ["inseam_cm", "Внутренний шов, см"]
                ].map(([name, label]) => (
                  <label key={name} className="block">
                    <span className="mb-2 block text-sm font-semibold text-slate-200">
                      {label}
                    </span>
                    <input
                      inputMode="decimal"
                      value={form[name as keyof FitProfileFormState] as string}
                      onChange={(event) =>
                        updateField(
                          name as keyof FitProfileFormState,
                          event.target.value as never
                        )
                      }
                      className="h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30"
                    />
                  </label>
                ))}
              </div>
            ) : null}

            {stepIndex === 1 ? (
              <div className="mt-6 space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="block">
                    <span className="mb-2 block text-sm font-semibold text-slate-200">
                      Предпочтительная посадка
                    </span>
                    <select
                      value={form.preferred_fit}
                      onChange={(event) => updateField("preferred_fit", event.target.value as never)}
                      className="h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30"
                    >
                      <option value="">Не выбрано</option>
                      <option value="slim">Slim</option>
                      <option value="regular">Regular</option>
                      <option value="relaxed">Relaxed</option>
                      <option value="oversized">Oversized</option>
                    </select>
                  </label>

                  <label className="block">
                    <span className="mb-2 block text-sm font-semibold text-slate-200">
                      Любимый стиль
                    </span>
                    <select
                      value={form.preferred_style}
                      onChange={(event) =>
                        updateField("preferred_style", event.target.value as never)
                      }
                      className="h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30"
                    >
                      <option value="">Не выбрано</option>
                      <option value="minimal">Минимализм</option>
                      <option value="streetwear">Streetwear</option>
                      <option value="dark_fantasy">Dark fantasy</option>
                      <option value="sport">Sport</option>
                      <option value="casual">Casual</option>
                    </select>
                  </label>

                  <label className="block sm:col-span-2">
                    <span className="mb-2 block text-sm font-semibold text-slate-200">
                      По цветам/вайбу ты скорее…
                    </span>
                    <select
                      value={quizExtras.color_vibe}
                      onChange={(event) => {
                        setSaveError(null);
                        setSaveMessage(null);
                        setQuizExtras({ color_vibe: event.target.value });
                      }}
                      className="h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30"
                    >
                      <option value="">Выбери вайб</option>
                      <option value="total black / тёмная база">total black / тёмная база</option>
                      <option value="пастель и нежняк">пастель и нежняк</option>
                      <option value="ярко, но со вкусом">ярко, но со вкусом</option>
                      <option value="нейтралка (серый/беж/база)">нейтралка (серый/беж/база)</option>
                      <option value="контрасты и принты">контрасты и принты</option>
                    </select>
                  </label>

                  <label className="block">
                    <span className="mb-2 block text-sm font-semibold text-slate-200">
                      Предпочтительный сезон
                    </span>
                    <select
                      value={form.preferred_season}
                      onChange={(event) =>
                        updateField("preferred_season", event.target.value as never)
                      }
                      className="h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30"
                    >
                      <option value="">Не выбрано</option>
                      <option value="spring">Весна</option>
                      <option value="summer">Лето</option>
                      <option value="autumn">Осень</option>
                      <option value="winter">Зима</option>
                      <option value="all_season">Круглый год</option>
                    </select>
                  </label>

                  <label className="block">
                    <span className="mb-2 block text-sm font-semibold text-slate-200">
                      Обычный размер верха
                    </span>
                    <select
                      value={form.tops_usual_size}
                      onChange={(event) =>
                        updateField("tops_usual_size", event.target.value as never)
                      }
                      className="h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30"
                    >
                      <option value="">Не выбрано</option>
                      {fitSizeOptions.map((size) => (
                        <option key={`wizard-top-${size}`} value={size}>
                          {size === "ONE_SIZE" ? "One size" : size}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="block">
                    <span className="mb-2 block text-sm font-semibold text-slate-200">
                      Обычный размер низа
                    </span>
                    <select
                      value={form.bottoms_usual_size}
                      onChange={(event) =>
                        updateField("bottoms_usual_size", event.target.value as never)
                      }
                      className="h-12 w-full border border-white/10 bg-ink-900/80 px-4 text-white outline-none transition focus:border-neon-teal focus:ring-2 focus:ring-neon-teal/30"
                    >
                      <option value="">Не выбрано</option>
                      {fitSizeOptions.map((size) => (
                        <option key={`wizard-bottom-${size}`} value={size}>
                          {size === "ONE_SIZE" ? "One size" : size}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              </div>
            ) : null}

            {stepIndex === 2 ? (
              <div className="mt-6 space-y-4">
                <div className="border border-white/10 bg-black/10 p-4">
                  <p className="text-sm font-black uppercase text-neon-teal">Перед сохранением</p>
                  <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-300">
                    <li>Рост: {form.height_cm || "—"} см</li>
                    <li>Вес: {form.weight_kg || "—"} кг</li>
                    <li>Посадка: {form.preferred_fit || "—"}</li>
                    <li>Стиль: {form.preferred_style || "—"}</li>
                    <li>Размер верха / низа: {form.tops_usual_size || "—"} / {form.bottoms_usual_size || "—"}</li>
                  </ul>
                </div>
              </div>
            ) : null}

            {saveError ? (
              <div className="mt-5 border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
                {saveError}
              </div>
            ) : null}

            {saveMessage ? (
              <div className="mt-5 border border-neon-teal/30 bg-neon-teal/10 px-4 py-3 text-sm leading-6 text-ice">
                {saveMessage}
              </div>
            ) : null}

            <div className="mt-6 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => setStepIndex((current) => Math.max(0, current - 1))}
                disabled={stepIndex === 0}
                className="h-11 border border-white/15 bg-white/5 px-5 text-sm font-semibold text-white transition hover:border-white/30 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Назад
              </button>
              {stepIndex < fitProfileWizardSteps.length - 1 ? (
                <button
                  type="button"
                  onClick={handleNextStep}
                  className="h-11 bg-neon-crimson px-5 text-sm font-black uppercase text-white transition hover:bg-white hover:text-ink-950"
                >
                  Дальше
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => void handleSave()}
                  disabled={isSaving}
                  className="h-11 bg-neon-teal px-5 text-sm font-black uppercase text-ink-950 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSaving
                    ? "Сохраняем..."
                    : accessToken
                      ? "Сохранить в профиль"
                      : "Завершить тест"}
                </button>
              )}
            </div>
          </section>
        </div>

      </section>
    </main>
  );
}
