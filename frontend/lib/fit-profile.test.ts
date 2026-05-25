import { emptyFitProfileForm, validateFitProfileForm } from "./fit-profile";

describe("validateFitProfileForm", () => {
  it("returns Russian validation errors for incomplete first step", () => {
    const errors = validateFitProfileForm(emptyFitProfileForm, "measurements");

    expect(errors[0]).toBe("Укажите рост.");
    expect(errors).toContain("Укажите вес.");
  });

  it("validates budget range and numeric bounds", () => {
    const errors = validateFitProfileForm(
      {
        ...emptyFitProfileForm,
        height_cm: "250",
        weight_kg: "70",
        chest_cm: "100",
        waist_cm: "80",
        hips_cm: "95",
        preferred_fit: "regular",
        preferred_style: "streetwear",
        preferred_season: "winter",
        tops_usual_size: "M",
        bottoms_usual_size: "L",
        budget_min_rub: "25000",
        budget_max_rub: "15000"
      },
      "all"
    );

    expect(errors).toContain("Рост должен быть в диапазоне 130–230.");
    expect(errors).toContain('Бюджет "от" не может быть больше бюджета "до".');
  });
});
