import type { ReactNode } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

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
          category: { id: 10, name: "Куртки", slug: "jackets", description: "" },
          franchise: { id: 11, name: "Akira", slug: "akira", description: "" },
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

  it("deduplicates products when the next page repeats an item", async () => {
    jest
      .mocked(fetchProducts)
      .mockResolvedValueOnce({
        count: 3,
        next: "http://api.example.com/products/?page=2",
        previous: null,
        results: [
          {
            id: 1,
            name: "Tokyo Team",
            slug: "tokyo-team-tee",
            category: {
              id: 10,
              name: "Футболки",
              slug: "tshirts",
              description: ""
            },
            franchise: {
              id: 11,
              name: "Магическая битва",
              slug: "jujutsu-kaisen",
              description: ""
            },
            base_price: "5100.00",
            is_featured: false,
            main_image: null,
            total_stock: 8
          },
          {
            id: 2,
            name: "Chainsaw Body",
            slug: "chainsaw-body",
            category: { id: 12, name: "Боди", slug: "bodysuits", description: "" },
            franchise: {
              id: 13,
              name: "Человек-бензопила",
              slug: "chainsaw-man",
              description: ""
            },
            base_price: "5790.00",
            is_featured: false,
            main_image: null,
            total_stock: 6
          }
        ]
      } as any)
      .mockResolvedValueOnce({
        count: 3,
        next: null,
        previous: "http://api.example.com/products?limit=18&offset=0",
        results: [
          {
            id: 2,
            name: "Chainsaw Body",
            slug: "chainsaw-body",
            category: { id: 12, name: "Боди", slug: "bodysuits", description: "" },
            franchise: {
              id: 13,
              name: "Человек-бензопила",
              slug: "chainsaw-man",
              description: ""
            },
            base_price: "5790.00",
            is_featured: false,
            main_image: null,
            total_stock: 6
          },
          {
            id: 3,
            name: "Hyuga Tales Body",
            slug: "hyuga-tales-body",
            category: { id: 12, name: "Боди", slug: "bodysuits", description: "" },
            franchise: {
              id: 14,
              name: "Наруто",
              slug: "naruto",
              description: ""
            },
            base_price: "5290.00",
            is_featured: false,
            main_image: null,
            total_stock: 7
          }
        ]
      } as any);

    renderWithQueryClient(<CatalogPage />);

    expect(await screen.findByRole("link", { name: /tokyo team/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /ещё/i }));

    await waitFor(() => {
      expect(screen.getByRole("link", { name: /hyuga tales body/i })).toBeInTheDocument();
    });

    expect(screen.getAllByRole("link", { name: /chainsaw body/i })).toHaveLength(1);
  });

  it("uses the backend next offset for the next page request", async () => {
    jest
      .mocked(fetchProducts)
      .mockResolvedValueOnce({
        count: 20,
        next: "http://api.example.com/products/?page=3",
        previous: null,
        results: [
          {
            id: 1,
            name: "Tokyo Team",
            slug: "tokyo-team-tee",
            category: {
              id: 10,
              name: "Футболки",
              slug: "tshirts",
              description: ""
            },
            franchise: {
              id: 11,
              name: "Jujutsu Kaisen",
              slug: "jujutsu-kaisen",
              description: ""
            },
            base_price: "5100.00",
            is_featured: false,
            main_image: null,
            total_stock: 8
          }
        ]
      } as any)
      .mockResolvedValueOnce({
        count: 20,
        next: null,
        previous: "http://api.example.com/products?limit=18&offset=0",
        results: [
          {
            id: 2,
            name: "Eva 01 Body",
            slug: "eva01-body",
            category: { id: 12, name: "Боди", slug: "bodysuits", description: "" },
            franchise: {
              id: 13,
              name: "Evangelion",
              slug: "evangelion",
              description: ""
            },
            base_price: "5790.00",
            is_featured: false,
            main_image: null,
            total_stock: 6
          }
        ]
      } as any);

    renderWithQueryClient(<CatalogPage />);

    expect(await screen.findByRole("link", { name: /tokyo team/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /ещё/i }));

    await waitFor(() => {
      expect(screen.getByRole("link", { name: /eva 01 body/i })).toBeInTheDocument();
    });

    expect(jest.mocked(fetchProducts).mock.calls[1][0].get("page")).toBe("3");
  });

  it("renders smart fitting recommendation in catalog for authenticated user", async () => {
    useUserStore.setState({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile: null
    });
    jest.mocked(fetchProducts).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          id: 8,
          name: "Blazonry Body WHT",
          slug: "blazonry-body-white",
          category: { id: 14, name: "Боди", slug: "bodysuits", description: "" },
          franchise: { id: 15, name: "Оригинал", slug: "original", description: "" },
          base_price: "6990.00",
          is_featured: true,
          main_image: null,
          total_stock: 5,
          tags: [],
          fit_recommendation: {
            recommended_size: "M",
            confidence: "high",
            profile_ready: true,
            missing_profile_fields: [],
            summary: "Рекомендуем размер M.",
            explanation: "Размер подобран по сохранённым параметрам пользователя.",
            reasons: [],
            warnings: ["closest_available_size_selected"],
            outfit: {
              items: [
                {
                  id: 100,
                  name: "Tokyo Team Tee",
                  slug: "tokyo-team-tee",
                  category: "Футболки",
                  franchise: "Оригинал",
                  base_price: "5100.00",
                  main_image_url: null,
                  reason: "Поддерживает образ."
                }
              ],
              total_price: "12090.00"
            }
          }
        }
      ]
    } as any);

    renderWithQueryClient(<CatalogPage />);

    expect(await screen.findByText("Умная примерочная")).toBeInTheDocument();
    expect(screen.getByText("Размер M")).toBeInTheDocument();
    expect(screen.getByText(/итого/i)).toBeInTheDocument();
    expect(jest.mocked(fetchProducts).mock.calls[0][1]).toBe("access-token");
  });
});
