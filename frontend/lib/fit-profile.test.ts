import { emptyFitProfileForm, validateFitProfileForm } from "./fit-profile";

describe("validateFitProfileForm", () => {
  it("returns Russian validation errors for incomplete first step", () => {
    const errors = validateFitProfileForm(emptyFitProfileForm, "measurements");

    expect(errors[0]).toBe("Укажите рост.");
    expect(errors).toContain("Укажите вес.");
  });

  it("validates numeric bounds", () => {
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
        bottoms_usual_size: "L"
      },
      "all"
    );

    expect(errors).toContain("Рост должен быть в диапазоне 130–230.");
  });
});
