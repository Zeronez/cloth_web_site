import type { ReactNode } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { fetchOrder, refreshOrderTracking } from "../../lib/api";
import { useUserStore } from "../../stores/user-store";
import { OrderTrackingPage } from "./order-tracking-page";

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
  fetchOrder: jest.fn(),
  refreshOrderTracking: jest.fn()
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

function deferredPromise<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((resolver) => {
    resolve = resolver;
  });
  return { promise, resolve };
}

function makeOrder() {
  return {
    id: 77,
    status: "shipped",
    status_label: "Передан в доставку",
    total_amount: "18900.00",
    track_number: "TRACK-77",
    items_count: 2,
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
      provider_code: "cdek",
      tracking_status: "out_for_delivery",
      tracking_status_label: "Курьер уже едет",
      external_shipment_id: "SHIP-77",
      current_location: "Москва",
      last_tracking_sync_at: "2026-05-05T10:30:00Z",
      recipient_name: "QA Shopper",
      recipient_phone: "+15551234567",
      country: "RU",
      city: "Moscow",
      postal_code: "101000",
      line1: "Test street 1",
      line2: "",
      tracking_events: [
        {
          id: 1,
          event_type: "tracking_sync",
          previous_status: "in_transit",
          new_status: "out_for_delivery",
          new_status_label: "Курьер уже едет",
          message: "Курьер выехал.",
          location: "Москва",
          payload: {},
          external_event_id: "evt-1",
          happened_at: "2026-05-05T10:30:00Z",
          created_at: "2026-05-05T10:30:00Z"
        }
      ]
    },
    shipping_name: "QA Shopper",
    shipping_phone: "+15551234567",
    shipping_country: "RU",
    shipping_city: "Moscow",
    shipping_postal_code: "101000",
    shipping_line1: "Test street 1",
    shipping_line2: "",
    items: [
      {
        id: 1,
        variant_id: 44,
        product: {
          id: 21,
          name: "Neon Ronin Shell",
          slug: "neon-ronin-shell",
          is_active: true,
          main_image: null
        },
        product_name: "Neon Ronin Shell",
        sku: "NRS-001",
        size: "M",
        color: "Black",
        quantity: 2,
        price_at_purchase: "9450.00",
        line_total: "18900.00"
      }
    ],
    created_at: "2026-05-04T09:00:00Z",
    updated_at: "2026-05-05T10:30:00Z"
  };
}

describe("OrderTrackingPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useUserStore.setState({
      accessToken: null,
      refreshToken: null,
      profile: null
    });
  });

  it("asks the user to sign in when there is no session", () => {
    renderWithQueryClient(<OrderTrackingPage orderId={77} />);

    expect(
      screen.getByRole("heading", {
        name: "Войдите, чтобы открыть историю доставки."
      })
    ).toBeInTheDocument();
  });

  it("shows an order tracking skeleton while the query is pending", async () => {
    useUserStore.setState({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile: null
    });
    const pending = deferredPromise<any>();
    jest.mocked(fetchOrder).mockReturnValue(pending.promise);

    renderWithQueryClient(<OrderTrackingPage orderId={77} />);

    expect(document.querySelector('main[aria-label]')).toBeInTheDocument();

    pending.resolve(makeOrder() as any);

    expect(
      await screen.findByRole("heading", { name: /Заказ #77/i })
    ).toBeInTheDocument();
  });

  it("renders tracking details, timeline, and linked order items", async () => {
    useUserStore.setState({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile: null
    });
    jest.mocked(fetchOrder).mockResolvedValue(makeOrder() as any);

    renderWithQueryClient(<OrderTrackingPage orderId={77} />);

    expect(
      await screen.findByRole("heading", { name: /Заказ #77/i })
    ).toBeInTheDocument();
    expect(fetchOrder).toHaveBeenCalledWith("access-token", 77);
    expect(screen.getByText("TRACK-77")).toBeInTheDocument();
    expect(screen.getAllByText("Курьер уже едет").length).toBeGreaterThan(0);
    expect(screen.getByText("Курьер выехал.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Neon Ronin Shell" })).toHaveAttribute(
      "href",
      "/products/neon-ronin-shell"
    );
  });

  it("can retry after the initial order load fails", async () => {
    useUserStore.setState({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile: null
    });
    jest
      .mocked(fetchOrder)
      .mockRejectedValueOnce(new Error("network down"))
      .mockResolvedValueOnce(makeOrder() as any);

    renderWithQueryClient(<OrderTrackingPage orderId={77} />);

    const retryButton = await screen.findByRole("button", {
      name: "Повторить загрузку"
    });
    fireEvent.click(retryButton);

    expect(
      await screen.findByRole("heading", { name: /Заказ #77/i })
    ).toBeInTheDocument();
    expect(fetchOrder).toHaveBeenCalledTimes(2);
  });

  it("can refresh tracking status from the API", async () => {
    useUserStore.setState({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile: null
    });
    jest.mocked(fetchOrder).mockResolvedValue(makeOrder() as any);
    jest.mocked(refreshOrderTracking).mockResolvedValue(makeOrder() as any);

    renderWithQueryClient(<OrderTrackingPage orderId={77} />);

    const button = await screen.findByRole("button", {
      name: "Обновить статус"
    });
    fireEvent.click(button);

    await waitFor(() => {
      expect(refreshOrderTracking).toHaveBeenCalledWith("access-token", 77);
    });
  });
});
