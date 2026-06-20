import type { FavoriteProductEntry } from "../lib/api";
import { useFavoritesStore } from "./favorites-store";
import { useUserStore } from "./user-store";

const profile = {
  id: 1,
  username: "shopper",
  email: "shopper@example.com",
  first_name: "QA",
  last_name: "Shopper",
  phone: "+79990001122"
};

const favorite = {
  id: 10,
  product_id: 20,
  product: {
    id: 20,
    name: "Cyber Hoodie",
    slug: "cyber-hoodie",
    category: {
      id: 1,
      name: "Hoodies",
      slug: "hoodies",
      description: ""
    },
    franchise: null,
    base_price: "4900.00",
    is_featured: true,
    main_image: null,
    total_stock: 5
  },
  created_at: "2026-05-09T00:00:00Z"
} satisfies FavoriteProductEntry;

describe("useUserStore persistence policy", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    useUserStore.setState({
      accessToken: null,
      refreshToken: null,
      profile: null
    });
    useFavoritesStore.setState({ favorites: [] });
  });

  it("keeps access token and profile in memory only", () => {
    useUserStore.getState().setSession({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile
    });

    expect(useUserStore.getState()).toMatchObject({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile
    });
    const persisted = JSON.parse(localStorage.getItem("animeattire-user") ?? "{}");

    expect(persisted.state).toEqual({ refreshToken: "refresh-token" });
    expect(JSON.stringify(persisted)).not.toContain("access-token");
    expect(JSON.stringify(persisted)).not.toContain("shopper@example.com");
  });

  it("clears session state and user-scoped favorites on logout", () => {
    useUserStore.getState().setSession({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile
    });
    useFavoritesStore.getState().setFavorites([favorite]);

    useUserStore.getState().clearSession();

    expect(useUserStore.getState()).toMatchObject({
      accessToken: null,
      refreshToken: null,
      profile: null
    });
    expect(useFavoritesStore.getState().favorites).toEqual([]);

    const persisted = JSON.parse(localStorage.getItem("animeattire-user") ?? "{}");
    expect(persisted.state).toEqual({ refreshToken: null });
  });
});
