import { getRecommendationScopeKey, useRecommendationHistoryStore } from "./recommendation-history-store";

describe("useRecommendationHistoryStore", () => {
  beforeEach(() => {
    localStorage.clear();
    useRecommendationHistoryStore.setState({
      entries: [],
      wizardDrafts: {}
    });
  });

  it("records recommendation views and persists saved state", () => {
    const scopeKey = getRecommendationScopeKey(7);

    useRecommendationHistoryStore.getState().recordView({
      scopeKey,
      productId: 42,
      productSlug: "blazonry-body-white",
      productName: "BLAZONRY WHT",
      categoryName: "Боди",
      recommendation: {
        recommended_size: "M",
        confidence: "high",
        profile_ready: true,
        missing_profile_fields: [],
        summary: "Рекомендуем размер M.",
        explanation: "Размер подобран по fit-profile.",
        reasons: ["Размер подобран по fit-profile."],
        warnings: [],
        outfit: {
          items: [],
          total_price: "8900.00"
        }
      }
    });

    const [entry] = useRecommendationHistoryStore.getState().entries;
    expect(entry).toMatchObject({
      scopeKey,
      productId: 42,
      recommendedSize: "M",
      confidence: "high"
    });

    useRecommendationHistoryStore.getState().toggleSaved(entry.id);
    expect(useRecommendationHistoryStore.getState().entries[0].savedAt).not.toBeNull();

    const persisted = JSON.parse(
      localStorage.getItem("animeattire-recommendation-history") ?? "{}"
    );
    expect(persisted.state.entries[0]).toMatchObject({
      productSlug: "blazonry-body-white",
      recommendedSize: "M"
    });
  });

  it("stores and clears wizard drafts per user scope", () => {
    const scopeKey = getRecommendationScopeKey(5);

    useRecommendationHistoryStore.getState().setWizardDraft(scopeKey, {
      height_cm: "178",
      preferred_fit: "regular"
    });

    expect(useRecommendationHistoryStore.getState().wizardDrafts[scopeKey]).toEqual(
      expect.objectContaining({
        height_cm: "178",
        preferred_fit: "regular"
      })
    );

    useRecommendationHistoryStore.getState().clearWizardDraft(scopeKey);
    expect(useRecommendationHistoryStore.getState().wizardDrafts[scopeKey]).toBeUndefined();
  });
});
