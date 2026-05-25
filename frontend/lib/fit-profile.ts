import type {
  FitProfile,
  FitProfilePreferredFit,
  FitProfilePreferredSeason,
  FitProfilePreferredStyle,
  FitProfileSize
} from "./api";

export type FitProfileFormState = {
  height_cm: string;
  weight_kg: string;
  chest_cm: string;
  waist_cm: string;
  hips_cm: string;
  inseam_cm: string;
  preferred_fit: "" | FitProfilePreferredFit;
  preferred_style: "" | FitProfilePreferredStyle;
  preferred_season: "" | FitProfilePreferredSeason;
  tops_usual_size: "" | FitProfileSize;
  bottoms_usual_size: "" | FitProfileSize;
  budget_min_rub: string;
  budget_max_rub: string;
  notes: string;
};

export const emptyFitProfileForm: FitProfileFormState = {
  height_cm: "",
  weight_kg: "",
  chest_cm: "",
  waist_cm: "",
  hips_cm: "",
  inseam_cm: "",
  preferred_fit: "",
  preferred_style: "",
  preferred_season: "",
  tops_usual_size: "",
  bottoms_usual_size: "",
  budget_min_rub: "",
  budget_max_rub: "",
  notes: ""
};

export const fitSizeOptions: FitProfileSize[] = [
  "XS",
  "S",
  "M",
  "L",
  "XL",
  "XXL",
  "ONE_SIZE"
];

export const fitProfileFieldLabels: Record<string, string> = {
  height_cm: "рост",
  weight_kg: "вес",
  chest_cm: "обхват груди",
  waist_cm: "обхват талии",
  hips_cm: "обхват бёдер",
  inseam_cm: "длина по внутреннему шву",
  preferred_fit: "предпочтительная посадка",
  preferred_style: "любимый стиль",
  preferred_season: "предпочтительный сезон",
  tops_usual_size: "обычный размер верха",
  bottoms_usual_size: "обычный размер низа",
  budget_min_rub: "минимальный бюджет",
  budget_max_rub: "максимальный бюджет"
};

export const fitProfileWizardSteps = [
  {
    id: "measurements",
    title: "Мерки",
    description: "Базовые параметры для точной посадки."
  },
  {
    id: "preferences",
    title: "Предпочтения",
    description: "Любимая посадка, стиль и привычные размеры."
  },
  {
    id: "review",
    title: "Финал",
    description: "Бюджет, заметки и сохранение профиля."
  }
] as const;

function toFormValue(value: string | number | null | undefined) {
  return value === null || value === undefined ? "" : String(value);
}

function normalizeOptionalNumber(value: string) {
  if (!value.trim()) {
    return null;
  }

  return Number(value);
}

export function fitProfileToForm(profile?: Partial<FitProfile> | null): FitProfileFormState {
  return {
    height_cm: toFormValue(profile?.height_cm),
    weight_kg: toFormValue(profile?.weight_kg),
    chest_cm: toFormValue(profile?.chest_cm),
    waist_cm: toFormValue(profile?.waist_cm),
    hips_cm: toFormValue(profile?.hips_cm),
    inseam_cm: toFormValue(profile?.inseam_cm),
    preferred_fit: (profile?.preferred_fit ?? "") as FitProfileFormState["preferred_fit"],
    preferred_style: (profile?.preferred_style ?? "") as FitProfileFormState["preferred_style"],
    preferred_season: (profile?.preferred_season ?? "") as FitProfileFormState["preferred_season"],
    tops_usual_size: (profile?.tops_usual_size ?? "") as FitProfileFormState["tops_usual_size"],
    bottoms_usual_size: (profile?.bottoms_usual_size ??
      "") as FitProfileFormState["bottoms_usual_size"],
    budget_min_rub: toFormValue(profile?.budget_min_rub),
    budget_max_rub: toFormValue(profile?.budget_max_rub),
    notes: profile?.notes ?? ""
  };
}

export function fitProfileFormToPayload(form: FitProfileFormState): Partial<FitProfile> {
  return {
    height_cm: normalizeOptionalNumber(form.height_cm),
    weight_kg: form.weight_kg.trim() || null,
    chest_cm: normalizeOptionalNumber(form.chest_cm),
    waist_cm: normalizeOptionalNumber(form.waist_cm),
    hips_cm: normalizeOptionalNumber(form.hips_cm),
    inseam_cm: normalizeOptionalNumber(form.inseam_cm),
    preferred_fit: form.preferred_fit || null,
    preferred_style: form.preferred_style || null,
    preferred_season: form.preferred_season || null,
    tops_usual_size: form.tops_usual_size || null,
    bottoms_usual_size: form.bottoms_usual_size || null,
    budget_min_rub: normalizeOptionalNumber(form.budget_min_rub),
    budget_max_rub: normalizeOptionalNumber(form.budget_max_rub),
    notes: form.notes.trim() || null
  };
}

export function getFitProfileCompletion(form: FitProfileFormState) {
  const trackedFields: Array<keyof FitProfileFormState> = [
    "height_cm",
    "weight_kg",
    "chest_cm",
    "waist_cm",
    "hips_cm",
    "preferred_fit",
    "preferred_style",
    "preferred_season",
    "tops_usual_size",
    "bottoms_usual_size"
  ];

  const completedCount = trackedFields.filter((field) =>
    String(form[field] ?? "").trim()
  ).length;

  return {
    completedCount,
    totalCount: trackedFields.length,
    percent: Math.round((completedCount / trackedFields.length) * 100)
  };
}

export function formatMissingFitFields(fields: string[]) {
  return fields.map((field) => fitProfileFieldLabels[field] ?? field).join(", ");
}

export function validateFitProfileForm(
  form: FitProfileFormState,
  step: (typeof fitProfileWizardSteps)[number]["id"] | "all" = "all"
) {
  const errors: string[] = [];
  const shouldValidate = (target: (typeof fitProfileWizardSteps)[number]["id"]) =>
    step === "all" || step === target;

  const requireValue = (
    field: keyof FitProfileFormState,
    label: string,
    targetStep: (typeof fitProfileWizardSteps)[number]["id"]
  ) => {
    if (shouldValidate(targetStep) && !String(form[field] ?? "").trim()) {
      errors.push(`Укажите ${label}.`);
    }
  };

  requireValue("height_cm", "рост", "measurements");
  requireValue("weight_kg", "вес", "measurements");
  requireValue("chest_cm", "обхват груди", "measurements");
  requireValue("waist_cm", "обхват талии", "measurements");
  requireValue("hips_cm", "обхват бёдер", "measurements");

  requireValue("preferred_fit", "предпочтительную посадку", "preferences");
  requireValue("preferred_style", "любимый стиль", "preferences");
  requireValue("preferred_season", "предпочтительный сезон", "preferences");
  requireValue("tops_usual_size", "обычный размер верха", "preferences");
  requireValue("bottoms_usual_size", "обычный размер низа", "preferences");

  const numericChecks: Array<[keyof FitProfileFormState, string, number, number]> = [
    ["height_cm", "Рост", 130, 230],
    ["weight_kg", "Вес", 30, 250],
    ["chest_cm", "Обхват груди", 60, 170],
    ["waist_cm", "Обхват талии", 45, 160],
    ["hips_cm", "Обхват бёдер", 60, 180],
    ["inseam_cm", "Внутренний шов", 40, 120]
  ];

  numericChecks.forEach(([field, label, min, max]) => {
    const rawValue = String(form[field] ?? "").trim();
    if (!rawValue) {
      return;
    }
    const numericValue = Number(rawValue.replace(",", "."));
    if (Number.isNaN(numericValue) || numericValue < min || numericValue > max) {
      errors.push(`${label} должен быть в диапазоне ${min}–${max}.`);
    }
  });

  const budgetMin = String(form.budget_min_rub ?? "").trim();
  const budgetMax = String(form.budget_max_rub ?? "").trim();
  if (budgetMin && Number(budgetMin) < 0) {
    errors.push("Минимальный бюджет не может быть отрицательным.");
  }
  if (budgetMax && Number(budgetMax) < 0) {
    errors.push("Максимальный бюджет не может быть отрицательным.");
  }
  if (budgetMin && budgetMax && Number(budgetMin) > Number(budgetMax)) {
    errors.push("Бюджет \"от\" не может быть больше бюджета \"до\".");
  }

  return errors;
}
