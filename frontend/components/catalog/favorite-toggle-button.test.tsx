import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import {
  addFavorite,
  removeFavorite,
  type FavoriteProductEntry,
  type Product
} from "../../lib/api";
import { useFavoritesStore } from "../../stores/favorites-store";
import { useUserStore } from "../../stores/user-store";
import { FavoriteToggleButton } from "./favorite-toggle-button";

jest.mock("../../lib/api", () => ({
  addFavorite: jest.fn(),
  removeFavorite: jest.fn()
}));

function buildProduct(overrides: Partial<Product> = {}): Product {
  return {
    id: 21,
    name: "Neon Ronin Shell",
    slug: "neon-ronin-shell",
    category: { id: 1, name: "Jackets", slug: "jackets", description: "" },
    franchise: { id: 1, name: "AnimeAttire", slug: "animeattire", description: "" },
    base_price: "14800.00",
    is_featured: true,
    main_image: null,
    total_stock: 24,
    ...overrides
  };
}

function buildFavorite(product: Product): FavoriteProductEntry {
  return {
    id: 9,
    product_id: product.id,
    product,
    created_at: "2026-04-06T10:00:00Z"
  };
}

describe("FavoriteToggleButton", () => {
  let redirectSpy: jest.Mock | null = null;

  beforeEach(() => {
    useUserStore.setState({
      accessToken: null,
      refreshToken: null,
      profile: null
    });
    useFavoritesStore.setState({
      favorites: []
    });
    redirectSpy = jest.fn();
    (window as unknown as { __APP_REDIRECT__?: jest.Mock }).__APP_REDIRECT__ = redirectSpy;
    jest.clearAllMocks();
  });

  it("redirects anonymous visitors to registration", () => {
    window.history.pushState({}, "", "/catalog");
    render(<FavoriteToggleButton product={buildProduct()} />);

    const button = screen.getByRole("button");

    expect(button).not.toBeDisabled();
    expect(button).toHaveAttribute("aria-label", expect.stringContaining("Neon Ronin Shell"));

    fireEvent.click(button);
    expect(redirectSpy).toHaveBeenCalledWith("/register?next=%2Fcatalog");
  });

  it("adds and removes favorites through the store-backed toggle state", async () => {
    const product = buildProduct();
    const favorite = buildFavorite(product);
    useUserStore.setState({ accessToken: "access-token" });
    jest.mocked(addFavorite).mockResolvedValue(favorite);
    jest.mocked(removeFavorite).mockResolvedValue({
      product_id: product.id,
      deleted: true
    });

    render(<FavoriteToggleButton product={product} />);

    const button = screen.getByRole("button");
    fireEvent.click(button);

    await waitFor(() => {
      expect(addFavorite).toHaveBeenCalledWith("access-token", product.id);
      expect(useFavoritesStore.getState().favorites).toHaveLength(1);
      expect(button).toHaveTextContent("В избранном");
    });

    fireEvent.click(button);

    await waitFor(() => {
      expect(removeFavorite).toHaveBeenCalledWith("access-token", product.id);
      expect(useFavoritesStore.getState().favorites).toHaveLength(0);
      expect(button).toHaveTextContent("В избранное");
    });
  });
});
