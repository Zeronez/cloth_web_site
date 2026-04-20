import { create } from "zustand";
import { persist } from "zustand/middleware";

export type UserProfile = {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  avatar?: string | null;
};

type UserState = {
  accessToken: string | null;
  refreshToken: string | null;
  profile: UserProfile | null;
  setSession: (session: {
    accessToken: string;
    refreshToken: string;
    profile: UserProfile;
  }) => void;
  clearSession: () => void;
};

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      profile: null,
      setSession: (session) => set(session),
      clearSession: () =>
        set({
          accessToken: null,
          refreshToken: null,
          profile: null
        })
    }),
    {
      name: "animeattire-user"
    }
  )
);
