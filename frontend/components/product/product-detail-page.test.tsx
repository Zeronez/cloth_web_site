import type { ReactNode } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { ApiError, fetchFavorites, fetchProduct } from "../../lib/api";
import { useUserStore } from "../../stores/user-store";
import { ProductDetailPage } from "./product-detail-page";

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
  fetchFavorites: jest.fn(),
  fetchProduct: jest.fn()
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

describe("ProductDetailPage", () => {
  beforeEach(() => {
    jest.resetAllMocks();
    useUserStore.setState({
      accessToken: null,
      refreshToken: null,
      profile: null
    });
    jest.mocked(fetchFavorites).mockResolvedValue([]);
  });

  it("shows an unavailable state for archived or missing products instead of demo fallback", async () => {
    jest
      .mocked(fetchProduct)
      .mockRejectedValue(new ApiError("Not found", 404, {}));

    renderWithQueryClient(<ProductDetailPage slug="archived-drop-jacket" />);

    expect(await screen.findByText(/товар недоступен/i)).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /добавить выбранный размер/i })
    ).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /назад в каталог/i })).toHaveAttribute(
      "href",
      "/catalog"
    );
  });

  it("shows an API error state instead of demo product content", async () => {
    jest.mocked(fetchProduct).mockRejectedValue(new Error("backend offline"));

    renderWithQueryClient(<ProductDetailPage slug="neon-ronin-shell" />);

    expect(
      await screen.findByText(/карточка товара временно недоступна/i)
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /добавить выбранный размер/i })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: /neon ronin shell/i })
    ).not.toBeInTheDocument();
  });

  it("renders a clickable product media gallery from API images", async () => {
    jest.mocked(fetchProduct).mockResolvedValue({
      id: 1,
      name: "Neon Ronin Shell",
      slug: "neon-ronin-shell",
      category: { id: 10, name: "Куртки", slug: "jackets" },
      franchise: { id: 11, name: "Akira", slug: "akira" },
      base_price: "12990.00",
      is_featured: true,
      description: "Techwear shell for neon nights.",
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
        },
        {
          id: 102,
          url: "https://cdn.example.com/products/ronin-closeup.jpg",
          alt_text: "Neon Ronin close-up",
          is_main: false
        }
      ],
      total_stock: 6,
      variants: [
        {
          id: 201,
          sku: "RONIN-M",
          size: "M",
          color: "Black",
          stock_quantity: 6,
          price_delta: "0.00",
          price: "12990.00",
          is_active: true
        }
      ]
    } as any);

    renderWithQueryClient(<ProductDetailPage slug="neon-ronin-shell" />);

    expect((await screen.findAllByAltText("Neon Ronin front")).length).toBeGreaterThan(0);

    const backThumb = screen.getByRole("button", {
      name: /показать медиа 2/i
    });
    fireEvent.click(backThumb);

    expect(backThumb).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Neon Ronin back")).toBeInTheDocument();
  });

  it("renders fit recommendation and capsule outfit for authenticated users", async () => {
    useUserStore.setState({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile: null
    });
    jest.mocked(fetchProduct).mockResolvedValue({
      id: 1,
      name: "Neon Ronin Shell",
      slug: "neon-ronin-shell",
      category: { id: 10, name: "Куртки", slug: "jackets" },
      franchise: { id: 11, name: "Akira", slug: "akira" },
      base_price: "12990.00",
      is_featured: true,
      description: "Techwear shell for neon nights.",
      main_image: null,
      images: [],
      total_stock: 6,
      fit_recommendation: {
        recommended_size: "L",
        confidence: "high",
        profile_ready: true,
        missing_profile_fields: [],
        summary: "Рекомендуем размер L.",
        explanation: "Размер подобран по меркам и предпочтению более свободной посадки.",
        reasons: [],
        warnings: ["closest_available_size_selected"],
        outfit: {
          total_price: "24880.00",
          items: [
            {
              id: 7,
              name: "Tokyo Team Tee",
              slug: "tokyo-team-tee",
              category: "Футболки",
              franchise: "Akira",
              base_price: "5890.00",
              main_image_url: null,
              reason: "Поддерживает силуэт и цветовую температуру образа."
            }
          ]
        }
      },
      variants: [
        {
          id: 201,
          sku: "RONIN-L",
          size: "L",
          color: "Black",
          stock_quantity: 4,
          price_delta: "0.00",
          price: "12990.00",
          is_active: true
        }
      ]
    } as any);

    renderWithQueryClient(<ProductDetailPage slug="neon-ronin-shell" />);

    expect(await screen.findByText("Рекомендуем размер L")).toBeInTheDocument();
    expect(screen.getByText("Капсульный образ")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Tokyo Team Tee/i })).toHaveAttribute(
      "href",
      "/products/tokyo-team-tee"
    );
    expect(screen.getByRole("button", { name: /размер l, в наличии/i })).toHaveAttribute(
      "aria-pressed",
      "true"
    );
  });

  it("falls back to anonymous product fetch after auth expiry", async () => {
    useUserStore.setState({
      accessToken: "expired-token",
      refreshToken: "refresh-token",
      profile: null
    });
    const fallbackProduct = {
      id: 3,
      name: "Fallback Product",
      slug: "fallback-product",
      category: { id: 12, name: "Худи", slug: "hoodies" },
      franchise: null,
      base_price: "9990.00",
      is_featured: false,
      description: "Recovered anonymously.",
      main_image: null,
      images: [],
      total_stock: 2,
      variants: [
        {
          id: 301,
          sku: "FALLBACK-M",
          size: "M",
          color: "Black",
          stock_quantity: 2,
          price_delta: "0.00",
          price: "9990.00",
          is_active: true
        }
      ]
    } as any;
    jest
      .mocked(fetchProduct)
      .mockRejectedValueOnce(new ApiError("Unauthorized", 401, {}))
      .mockResolvedValue(fallbackProduct);

    renderWithQueryClient(<ProductDetailPage slug="fallback-product" />);

    expect(await screen.findByRole("heading", { name: /fallback product/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(fetchProduct).toHaveBeenCalledWith("fallback-product", "expired-token");
      expect(fetchProduct).toHaveBeenCalledWith("fallback-product");
    });
  });

  it("shows sold-out sizes in the selector and disables purchase for them", async () => {
    jest.mocked(fetchProduct).mockResolvedValue({
      id: 2,
      name: "Eva Utility Hoodie",
      slug: "eva-utility-hoodie",
      category: { id: 12, name: "Худи", slug: "hoodies" },
      franchise: { id: 13, name: "Evangelion", slug: "evangelion" },
      base_price: "9990.00",
      is_featured: false,
      description: "Utility hoodie with limited stock.",
      main_image: null,
      images: [],
      total_stock: 2,
      variants: [
        {
          id: 301,
          sku: "EVA-HOODIE-M",
          size: "M",
          color: "Black",
          stock_quantity: 2,
          price_delta: "0.00",
          price: "9990.00",
          is_active: true
        },
        {
          id: 302,
          sku: "EVA-HOODIE-L",
          size: "L",
          color: "Black",
          stock_quantity: 0,
          price_delta: "0.00",
          price: "9990.00",
          is_active: true
        }
      ]
    } as any);

    renderWithQueryClient(<ProductDetailPage slug="eva-utility-hoodie" />);

    const mediumSize = await screen.findByRole("button", {
      name: /размер m, заканчивается/i
    });
    const soldOutSize = screen.getByRole("button", {
      name: /размер l, нет в наличии/i
    });

    expect(mediumSize).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText(/заканчивается: 2 шт\., цвет: black/i)).toBeInTheDocument();

    fireEvent.click(soldOutSize);

    expect(soldOutSize).toHaveAttribute("aria-pressed", "true");
    expect(screen.getAllByText(/нет в наличии/i).length).toBeGreaterThan(0);
    expect(
      screen.getByRole("button", { name: /выбранный размер недоступен/i })
    ).toBeDisabled();
  });
});
