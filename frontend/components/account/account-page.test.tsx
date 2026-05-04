import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { ReactNode } from "react";

import { fetchAddresses, fetchFavorites, fetchMe, fetchOrders } from "../../lib/api";
import { useFavoritesStore } from "../../stores/favorites-store";
import { useUserStore } from "../../stores/user-store";
import { AccountPage } from "./account-page";

const push = jest.fn();
const refresh = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push,
    refresh
  })
}));

jest.mock("../../lib/api", () => ({
  ...jest.requireActual("../../lib/api"),
  ApiError: class ApiError extends Error {
    status: number;
    payload: unknown;

    constructor(message: string, status: number, payload: unknown) {
      super(message);
      this.status = status;
      this.payload = payload;
    }
  },
  addFavorite: jest.fn(),
  createAddress: jest.fn(),
  deleteAddress: jest.fn(),
  fetchAddresses: jest.fn(),
  fetchFavorites: jest.fn(),
  fetchMe: jest.fn(),
  fetchOrders: jest.fn(),
  logoutUser: jest.fn(),
  removeFavorite: jest.fn(),
  updateAddress: jest.fn(),
  updateMe: jest.fn()
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

describe("AccountPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useUserStore.setState({
      accessToken: null,
      refreshToken: null,
      profile: null
    });
    useFavoritesStore.setState({
      favorites: []
    });
  });

  it("shows login and registration links for anonymous visitors", async () => {
    const { container } = renderWithQueryClient(<AccountPage />);

    await waitFor(() => {
      expect(container.querySelector('a[href="/login"]')).toBeInTheDocument();
      expect(container.querySelector('a[href="/register"]')).toBeInTheDocument();
    });
  });

  it("renders authenticated profile and address data from the API", async () => {
    useUserStore.setState({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile: {
        id: 7,
        username: "shopper",
        email: "cached@example.com",
        first_name: "Cached",
        last_name: "User",
        phone: "+15550000000"
      }
    });
    jest.mocked(fetchMe).mockResolvedValue({
      id: 7,
      username: "shopper",
      email: "shopper@example.com",
      first_name: "QA",
      last_name: "Shopper",
      phone: "+15551234567"
    });
    jest.mocked(fetchAddresses).mockResolvedValue([
      {
        id: 3,
        label: "Home",
        recipient_name: "QA Shopper",
        phone: "+15551234567",
        country: "US",
        city: "New York",
        postal_code: "10001",
        line1: "11 Test Avenue",
        line2: "Apt 5",
        is_default: true,
        created_at: "2026-04-01T10:00:00Z",
        updated_at: "2026-04-02T10:00:00Z"
      }
    ]);
    jest.mocked(fetchOrders).mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: 11,
          status: "pending",
          total_amount: "28900.00",
          track_number: "",
          items_count: 2,
          shipping_address: {
            name: "QA Shopper",
            phone: "+15551234567",
            country: "US",
            city: "New York",
            postal_code: "10001",
            line1: "11 Test Avenue",
            line2: "Apt 5"
          },
          shipping_name: "QA Shopper",
          shipping_phone: "+15551234567",
          shipping_country: "US",
          shipping_city: "New York",
          shipping_postal_code: "10001",
          shipping_line1: "11 Test Avenue",
          shipping_line2: "Apt 5",
          delivery: null,
          items: [
            {
              id: 1,
              variant_id: 44,
              product_name: "Neon Ronin Shell",
              sku: "NRS-001",
              size: "M",
              color: "Black",
              quantity: 2,
              price_at_purchase: "14450.00",
              line_total: "28900.00"
            }
          ],
          created_at: "2026-04-05T10:00:00Z",
          updated_at: "2026-04-05T10:05:00Z"
        },
        {
          id: 12,
          status: "delivered",
          status_label: "\u0414\u043e\u0441\u0442\u0430\u0432\u043b\u0435\u043d",
          total_amount: "14900.00",
          track_number: "TRACK-4242",
          items_count: 1,
          shipping_address: {
            name: "QA Shopper",
            phone: "+15551234567",
            country: "US",
            city: "New York",
            postal_code: "10001",
            line1: "11 Test Avenue",
            line2: ""
          },
          shipping_name: "QA Shopper",
          shipping_phone: "+15551234567",
          shipping_country: "US",
          shipping_city: "New York",
          shipping_postal_code: "10001",
          shipping_line1: "11 Test Avenue",
          shipping_line2: "",
          delivery: null,
          items: [
            {
              id: 2,
              variant_id: 45,
              product_name: "Neon Ronin Shell",
              sku: "NRS-002",
              size: "L",
              color: "Black",
              quantity: 1,
              price_at_purchase: "14900.00",
              line_total: "14900.00"
            }
          ],
          created_at: "2026-04-06T10:00:00Z",
          updated_at: "2026-04-06T10:05:00Z"
        }
      ]
    });
    jest.mocked(fetchFavorites).mockResolvedValue([
      {
        id: 9,
        product_id: 21,
        product: {
          id: 21,
          name: "Neon Ronin Shell",
          slug: "neon-ronin-shell",
          category: {
            id: 1,
            name: "Куртки",
            slug: "jackets",
            description: ""
          },
          franchise: {
            id: 1,
            name: "Оригинал",
            slug: "original",
            description: ""
          },
          base_price: "14800.00",
          is_featured: true,
          main_image: null,
          total_stock: 24
        },
        created_at: "2026-04-06T10:00:00Z"
      }
    ]);

    renderWithQueryClient(<AccountPage />);

    await waitFor(() => {
      expect(fetchMe).toHaveBeenCalledWith("access-token");
      expect(fetchAddresses).toHaveBeenCalledWith("access-token");
      expect(fetchOrders).toHaveBeenCalledWith("access-token");
      expect(fetchFavorites).toHaveBeenCalledWith("access-token");
    });
    expect(await screen.findByText("QA Shopper")).toBeInTheDocument();
    expect(screen.getByText("shopper@example.com")).toBeInTheDocument();
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getAllByText(/11 Test Avenue/).length).toBeGreaterThan(0);
    expect(screen.getByText("История покупок")).toBeInTheDocument();
    expect(screen.getByText("Любимые вещи")).toBeInTheDocument();
    expect(screen.getAllByText("Neon Ronin Shell").length).toBeGreaterThan(0);
    expect(screen.getByText("Заказ #11")).toBeInTheDocument();
    expect(screen.getByText("Ожидает оплаты")).toBeInTheDocument();
    expect(screen.getByText("\u0414\u043e\u0441\u0442\u0430\u0432\u043b\u0435\u043d")).toBeInTheDocument();
    expect(screen.getByText(/TRACK-4242/)).toBeInTheDocument();
    expect(
      screen.getByText("\u0417\u0430\u043a\u0430\u0437 \u0434\u043e\u0441\u0442\u0430\u0432\u043b\u0435\u043d. \u0415\u0441\u043b\u0438 \u0447\u0442\u043e-\u0442\u043e \u043d\u0435 \u043f\u043e\u0434\u043e\u0448\u043b\u043e, \u043c\u043e\u0436\u043d\u043e \u043e\u0444\u043e\u0440\u043c\u0438\u0442\u044c \u0432\u043e\u0437\u0432\u0440\u0430\u0442.")
    ).toBeInTheDocument();
  });

  it("smokes the empty orders and favorites sections for an authenticated account", async () => {
    useUserStore.setState({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile: {
        id: 7,
        username: "shopper",
        email: "shopper@example.com",
        first_name: "QA",
        last_name: "Shopper",
        phone: "+15551234567"
      }
    });
    jest.mocked(fetchMe).mockResolvedValue({
      id: 7,
      username: "shopper",
      email: "shopper@example.com",
      first_name: "QA",
      last_name: "Shopper",
      phone: "+15551234567"
    });
    jest.mocked(fetchAddresses).mockResolvedValue([]);
    jest.mocked(fetchOrders).mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: []
    });
    jest.mocked(fetchFavorites).mockResolvedValue([]);

    renderWithQueryClient(<AccountPage />);

    await waitFor(() => {
      expect(fetchMe).toHaveBeenCalledWith("access-token");
      expect(fetchAddresses).toHaveBeenCalledWith("access-token");
      expect(fetchOrders).toHaveBeenCalledWith("access-token");
      expect(fetchFavorites).toHaveBeenCalledWith("access-token");
    });

    expect(await screen.findByText("История покупок")).toBeInTheDocument();
    expect(screen.getByText("Любимые вещи")).toBeInTheDocument();
    expect(
      screen.getByText("Пока нет заказов. Первый оформленный дроп появится здесь.")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Здесь будут вещи, которые вы отложили на потом.")
    ).toBeInTheDocument();
  });
});
