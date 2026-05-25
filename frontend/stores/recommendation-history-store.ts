import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { FitProfileFormState } from "../lib/fit-profile";
import type {
  FitRecommendation,
  FitRecommendationConfidence,
  FitRecommendationOutfitItem
} from "../lib/api";

type RecommendationHistoryEntry = {
  id: string;
  scopeKey: string;
  productId: number;
  productSlug: string;
  productName: string;
  categoryName: string;
  recommendedSize: string | null;
  confidence: FitRecommendationConfidence;
  summary: string;
  explanation: string;
  warnings: string[];
  viewedAt: string;
  savedAt: string | null;
  outfit: {
    totalPrice: string | null;
    items: FitRecommendationOutfitItem[];
  };
};

type RecommendationEntryInput = {
  scopeKey: string;
  productId: number;
  productSlug: string;
  productName: string;
  categoryName: string;
  recommendation: FitRecommendation;
};

type RecommendationHistoryState = {
  entries: RecommendationHistoryEntry[];
  wizardDrafts: Record<string, Partial<FitProfileFormState>>;
  recordView: (input: RecommendationEntryInput) => void;
  toggleSaved: (entryId: string) => void;
  removeEntry: (entryId: string) => void;
  setWizardDraft: (scopeKey: string, draft: Partial<FitProfileFormState>) => void;
  clearWizardDraft: (scopeKey: string) => void;
};

const MAX_HISTORY_ITEMS = 24;

export function getRecommendationEntryId(scopeKey: string, productId: number) {
  return `${scopeKey}:product:${productId}`;
}

export function getRecommendationScopeKey(userId?: number | null) {
  return userId ? `user:${userId}` : "member";
}

export const useRecommendationHistoryStore = create<RecommendationHistoryState>()(
  persist(
    (set) => ({
      entries: [],
      wizardDrafts: {},
      recordView: (input) =>
        set((state) => {
          const entryId = getRecommendationEntryId(input.scopeKey, input.productId);
          const existingEntry = state.entries.find((entry) => entry.id === entryId);
          const nextEntry: RecommendationHistoryEntry = {
            id: entryId,
            scopeKey: input.scopeKey,
            productId: input.productId,
            productSlug: input.productSlug,
            productName: input.productName,
            categoryName: input.categoryName,
            recommendedSize: input.recommendation.recommended_size,
            confidence: input.recommendation.confidence,
            summary: input.recommendation.summary,
            explanation: input.recommendation.explanation,
            warnings: input.recommendation.warnings.map(String),
            viewedAt: new Date().toISOString(),
            savedAt: existingEntry?.savedAt ?? null,
            outfit: {
              totalPrice: input.recommendation.outfit.total_price,
              items: input.recommendation.outfit.items
            }
          };

          return {
            entries: [
              nextEntry,
              ...state.entries.filter((entry) => entry.id !== entryId)
            ].slice(0, MAX_HISTORY_ITEMS)
          };
        }),
      toggleSaved: (entryId) =>
        set((state) => ({
          entries: state.entries.map((entry) =>
            entry.id === entryId
              ? {
                  ...entry,
                  savedAt: entry.savedAt ? null : new Date().toISOString()
                }
              : entry
          )
        })),
      removeEntry: (entryId) =>
        set((state) => ({
          entries: state.entries.filter((entry) => entry.id !== entryId)
        })),
      setWizardDraft: (scopeKey, draft) =>
        set((state) => ({
          wizardDrafts: {
            ...state.wizardDrafts,
            [scopeKey]: {
              ...(state.wizardDrafts[scopeKey] ?? {}),
              ...draft
            }
          }
        })),
      clearWizardDraft: (scopeKey) =>
        set((state) => {
          const nextDrafts = { ...state.wizardDrafts };
          delete nextDrafts[scopeKey];

          return { wizardDrafts: nextDrafts };
        })
    }),
    {
      name: "animeattire-recommendation-history"
    }
  )
);

export type { RecommendationHistoryEntry };
