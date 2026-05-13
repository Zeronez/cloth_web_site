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

  it("renders product media from API images and keeps hover media in the card", async () => {
    jest.mocked(fetchProducts).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          name: "Neon Ronin Shell",
          slug: "neon-ronin-shell",
          category: { id: 10, name: "Куртки", slug: "jackets" },
          franchise: { id: 11, name: "Akira", slug: "akira" },
          base_price: "12990.00",
          is_featured: true,
          main_image: {
            id: 100,
            url: "https://cdn.example.com/products/ronin-front.jpg",
            alt_text: "Neon Ronin front",
            is_main: true
          },
          images: [
            {
              id: 101,
              url: "https://cdn.example.com/products/ronin-back.jpg",
              alt_text: "Neon Ronin back",
              is_main: false
            }
          ],
          total_stock: 8
        }
      ]
    } as any);

    renderWithQueryClient(<CatalogPage />);

    expect(await screen.findByAltText("Neon Ronin front")).toBeInTheDocument();
    expect(screen.getByAltText("Neon Ronin back")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /neon ronin shell/i })
    ).toHaveAttribute("href", "/products/neon-ronin-shell");
  });
});
