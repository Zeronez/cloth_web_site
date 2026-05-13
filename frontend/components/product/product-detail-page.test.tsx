import type { ReactNode } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";

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
});
