import type { ReactNode } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import {
  addCartItem,
  checkoutOrder,
  createPaymentSession,
  deleteCartItem,
  fetchAddresses,
  fetchCart,
  fetchDeliveryMethods,
  fetchPaymentMethods,
  updateCartItemQuantity
} from "../../lib/api";
import { useCartStore } from "../../stores/cart-store";
import { useUserStore } from "../../stores/user-store";
import { CheckoutPage } from "./checkout-page";

jest.mock("next/link", () => {
  const React = require("react");

  return React.forwardRef(function LinkMock(
    { href, children, ...props }: any,
    ref: any
  ) {
    return React.createElement("a", { ref, href, ...props }, children);
  });
});

jest.mock("../product-image-placeholder", () => ({
  ProductImagePlaceholder: ({ label }: { label: string }) => (
    <div data-testid="product-image-placeholder">{label}</div>
  )
}));

jest.mock("../../lib/api", () => ({
  ApiError: class ApiError extends Error {
    status: number;
    payload: unknown;

    constructor(message: string, status: number, payload: unknown) {
      super(message);
      this.status = status;
      this.payload = payload;
    }
  },
  addCartItem: jest.fn(),
  checkoutOrder: jest.fn(),
  createPaymentSession: jest.fn(),
  deleteCartItem: jest.fn(),
  fetchAddresses: jest.fn(),
  fetchCart: jest.fn(),
  fetchDeliveryMethods: jest.fn(),
  fetchPaymentMethods: jest.fn(),
  updateCartItemQuantity: jest.fn()
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

function makeServerCart() {
  return {
    id: 1,
    items: [
      {
        id: 501,
        variant: {
          id: 101,
          sku: "SYNC-TEE-M",
          size: "M",
          color: "Black",
          stock_quantity: 3,
          price_delta: "0.00",
          price: "100.00",
          is_active: true
        },
        product: {
          id: 11,
          name: "Sync Tee",
          slug: "sync-tee",
          base_price: "100.00",
          is_active: true
        },
        quantity: 1,
        unit_price: "100.00",
        line_total: "100.00",
        created_at: "2026-04-22T10:00:00Z",
        updated_at: "2026-04-22T10:00:00Z"
      },
      {
        id: 502,
        variant: {
          id: 300,
          sku: "OBSOLETE-TEE-L",
          size: "L",
          color: "Black",
          stock_quantity: 1,
          price_delta: "0.00",
          price: "55.00",
          is_active: true
        },
        product: {
          id: 12,
          name: "Obsolete Tee",
          slug: "obsolete-tee",
          base_price: "55.00",
          is_active: true
        },
        quantity: 1,
        unit_price: "55.00",
        line_total: "55.00",
        created_at: "2026-04-22T10:00:00Z",
        updated_at: "2026-04-22T10:00:00Z"
      }
    ],
    total_amount: "155.00",
    subtotal_amount: "155.00",
    total_quantity: 2,
    created_at: "2026-04-22T10:00:00Z",
    updated_at: "2026-04-22T10:00:00Z"
  };
}

function makeDeliveryMethods() {
  return {
    count: 1,
    next: null,
    previous: null,
    results: [
      {
        code: "courier-msk",
        name: "Курьер по Москве",
        kind: "courier",
        kind_label: "Курьер",
        description: "Доставим до двери.",
        price_amount: "350.00",
        currency: "RUB",
        estimated_days_min: 1,
        estimated_days_max: 2,
        requires_address: true,
        sort_order: 10
      }
    ]
  };
}

function makePaymentMethods() {
  return {
    count: 1,
    next: null,
    previous: null,
    results: [
      {
        code: "local-card",
        name: "Банковская карта",
        description: "Локальная платежная сессия.",
        provider_code: "placeholder",
        session_mode: "placeholder",
        session_mode_label: "Локальная сессия",
        currency: "RUB",
        sort_order: 10
      }
    ]
  };
}

describe("CheckoutPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.mocked(fetchDeliveryMethods).mockResolvedValue(makeDeliveryMethods());
    jest.mocked(fetchPaymentMethods).mockResolvedValue(makePaymentMethods());
    useUserStore.setState({
      accessToken: null,
      refreshToken: null,
      profile: null
    });
    useCartStore.setState({
      items: [],
      isOpen: false
    });
  });

  it("shows login prompts for anonymous visitors", async () => {
    useCartStore.setState({
      isOpen: false,
      items: [
        {
          id: "101",
          name: "Guest Tee",
          price: 100,
          size: "M",
          quantity: 1
        }
      ]
    });

    const { container } = renderWithQueryClient(<CheckoutPage />);

    await waitFor(() => {
      expect(container.querySelector('a[href="/login"]')).toBeInTheDocument();
      expect(container.querySelector('a[href="/register"]')).toBeInTheDocument();
    });
  });

  it("renders the empty-cart state when checkout has no items", async () => {
    renderWithQueryClient(<CheckoutPage />);

    expect(await screen.findByRole("heading", { level: 1 })).toHaveTextContent(
      "Корзина пока пуста."
    );
    expect(screen.getByRole("link", { name: /каталог/i })).toBeInTheDocument();
  });

  it("syncs the local cart before creating the checkout order", async () => {
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
    useCartStore.setState({
      isOpen: false,
      items: [
        {
          id: "101",
          name: "Sync Tee",
          price: 100,
          size: "M",
          quantity: 2
        },
        {
          id: "200",
          name: "New Tee",
          price: 55,
          size: "L",
          quantity: 1
        }
      ]
    });

    jest.mocked(fetchAddresses).mockResolvedValue([]);
    jest.mocked(fetchCart).mockResolvedValue(makeServerCart());
    jest.mocked(deleteCartItem).mockResolvedValue(makeServerCart());
    jest.mocked(updateCartItemQuantity).mockResolvedValue(makeServerCart());
    jest.mocked(addCartItem).mockResolvedValue(makeServerCart());
    jest.mocked(checkoutOrder).mockResolvedValue({
      id: 9001,
      status: "pending",
      total_amount: "605.00",
      track_number: "",
      items_count: 3,
      shipping_address: {
        name: "QA Shopper",
        phone: "+15551234567",
        country: "RU",
        city: "Moscow",
        postal_code: "101000",
        line1: "Test street 1",
        line2: ""
      },
      delivery: {
        method_code: "courier-msk",
        method_name: "Курьер по Москве",
        method_kind: "courier",
        method_kind_label: "Курьер",
        price_amount: "350.00",
        currency: "RUB",
        estimated_days_min: 1,
        estimated_days_max: 2,
        recipient_name: "QA Shopper",
        recipient_phone: "+15551234567",
        country: "RU",
        city: "Moscow",
        postal_code: "101000",
        line1: "Test street 1",
        line2: ""
      },
      shipping_name: "QA Shopper",
      shipping_phone: "+15551234567",
      shipping_country: "RU",
      shipping_city: "Moscow",
      shipping_postal_code: "101000",
      shipping_line1: "Test street 1",
      shipping_line2: "",
      items: [],
      created_at: "2026-04-22T10:00:00Z",
      updated_at: "2026-04-22T10:00:00Z"
    });
    jest.mocked(createPaymentSession).mockResolvedValue({
      payment: {
        id: 3001,
        order: 9001,
        method_code: "local-card",
        provider_code: "placeholder",
        status: "session_created",
        status_label: "Сессия создана",
        amount: "605.00",
        currency: "RUB",
        external_payment_id: "",
        session_expires_at: null,
        events: [],
        created_at: "2026-04-22T10:00:00Z",
        updated_at: "2026-04-22T10:00:00Z"
      },
      created: true,
      provider: "placeholder",
      confirmation_url: null,
      message:
        "Платежная сессия создана локально. Внешний провайдер не подключен."
    });

    const { container } = renderWithQueryClient(<CheckoutPage />);

    await waitFor(() => {
      expect(fetchAddresses).toHaveBeenCalledWith("access-token");
    });
    expect(await screen.findByText("Курьер по Москве")).toBeInTheDocument();
    expect(screen.getByText("Банковская карта")).toBeInTheDocument();

    fireEvent.change(container.querySelector('input[name="shipping_city"]')!, {
      target: { value: "Moscow" }
    });
    fireEvent.change(
      container.querySelector('input[name="shipping_postal_code"]')!,
      {
        target: { value: "101000" }
      }
    );
    fireEvent.change(container.querySelector('input[name="shipping_line1"]')!, {
      target: { value: "Test street 1" }
    });

    fireEvent.click(container.querySelector('button[type="submit"]')!);

    await waitFor(() => {
      expect(fetchCart).toHaveBeenCalledWith("access-token");
      expect(deleteCartItem).toHaveBeenCalledWith("access-token", 502);
      expect(updateCartItemQuantity).toHaveBeenCalledWith(
        "access-token",
        501,
        2
      );
      expect(addCartItem).toHaveBeenCalledWith("access-token", 200, 1);
      expect(checkoutOrder).toHaveBeenCalledWith("access-token", {
        delivery_method_code: "courier-msk",
        idempotency_key: expect.stringMatching(/^checkout-/),
        shipping_name: "QA Shopper",
        shipping_phone: "+15551234567",
        shipping_country: "RU",
        shipping_city: "Moscow",
        shipping_postal_code: "101000",
        shipping_line1: "Test street 1",
        shipping_line2: ""
      });
      expect(createPaymentSession).toHaveBeenCalledWith("access-token", {
        order_id: 9001,
        payment_method_code: "local-card",
        idempotency_key: "checkout-9001-local-card"
      });
    });

    expect(
      await screen.findByText(/внешний платежный провайдер пока не подключен/i)
    ).toBeInTheDocument();
  });
});
