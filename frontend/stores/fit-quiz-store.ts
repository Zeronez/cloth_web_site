import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { FitProfileFormState } from "../lib/fit-profile";

export type FitQuizExtras = {
  color_vibe: string;
};

type FitQuizState = {
  completedProfile: FitProfileFormState | null;
  extras: FitQuizExtras;
  completedAt: string | null;
  setCompletedProfile: (profile: FitProfileFormState, extras?: Partial<FitQuizExtras>) => void;
  clearCompletedProfile: () => void;
  setExtras: (extras: Partial<FitQuizExtras>) => void;
};

const defaultExtras: FitQuizExtras = {
  color_vibe: ""
};

export const useFitQuizStore = create<FitQuizState>()(
  persist(
    (set) => ({
      completedProfile: null,
      extras: defaultExtras,
      completedAt: null,
      setCompletedProfile: (profile, extras) =>
        set(() => ({
          completedProfile: profile,
          extras: { ...defaultExtras, ...(extras ?? {}) },
          completedAt: new Date().toISOString()
        })),
      clearCompletedProfile: () =>
        set(() => ({
          completedProfile: null,
          completedAt: null
        })),
      setExtras: (extras) =>
        set((state) => ({
          extras: { ...state.extras, ...extras }
        }))
    }),
    { name: "animeattire-fit-quiz" }
  )
);

