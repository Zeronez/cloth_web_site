import type { ReactNode } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";

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
    jest.clearAllMocks();
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
});
