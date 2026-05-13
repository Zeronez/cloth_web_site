import type { ReactNode } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";

import {
  fetchCategories,
  fetchFavorites,
  fetchFranchises,
  fetchProducts
} from "../../lib/api";
import { useUserStore } from "../../stores/user-store";
import { CatalogPage } from "./catalog-page";

jest.mock("next/link", () => {
  const React = require("react");

  return React.forwardRef(function LinkMock(
    { href, children, ...props }: any,
    ref: any
  ) {
    return React.createElement("a", { ref, href, ...props }, children);
  });
});

jest.mock("../../lib/api", () => ({
  ...jest.requireActual("../../lib/api"),
  fetchCategories: jest.fn(),
  fetchFavorites: jest.fn(),
  fetchFranchises: jest.fn(),
  fetchProducts: jest.fn()
}));

function renderWithQueryClient(children: ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false
      }
    }
  });

  return render(
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe("CatalogPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useUserStore.setState({
      accessToken: null,
      refreshToken: null,
      profile: null
    });
    jest.mocked(fetchCategories).mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: []
    });
    jest.mocked(fetchFranchises).mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: []
    });
    jest.mocked(fetchFavorites).mockResolvedValue([]);
  });

  it("shows an API error state instead of demo products when catalog loading fails", async () => {
    jest.mocked(fetchProducts).mockRejectedValue(new Error("catalog offline"));

    renderWithQueryClient(<CatalogPage />);

    expect(
      await screen.findByText(/каталог временно недоступен/i)
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: /neon ronin/i })
    ).not.toBeInTheDocument();
  });
});
