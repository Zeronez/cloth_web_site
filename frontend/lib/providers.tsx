"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode, useEffect, useRef, useState } from "react";

import { ApiError, fetchMe, refreshTokens } from "./api";
import { useUserStore } from "../stores/user-store";

export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchOnWindowFocus: false,
            retry: 1,
            staleTime: 60_000
          }
        }
      })
  );

  const didBootstrapAuth = useRef(false);

  useEffect(() => {
    if (didBootstrapAuth.current) {
      return;
    }

    didBootstrapAuth.current = true;

    const { accessToken, refreshToken, setSession, clearSession } =
      useUserStore.getState();

    if (accessToken || !refreshToken) {
      return;
    }

    void (async () => {
      try {
        const tokens = await refreshTokens(refreshToken);
        const profile = await fetchMe(tokens.access);
        setSession({
          accessToken: tokens.access,
          refreshToken: tokens.refresh ?? refreshToken,
          profile
        });
      } catch (error) {
        if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
          clearSession();
          return;
        }

        clearSession();
      }
    })();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
