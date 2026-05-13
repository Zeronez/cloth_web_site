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
    status_label: "РџРµСЂРµРґР°РЅ РІ РґРѕСЃС‚Р°РІРєСѓ",
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
      method_name: "РљСѓСЂСЊРµСЂ РїРѕ РњРѕСЃРєРІРµ",
      method_kind: "courier",
      method_kind_label: "РљСѓСЂСЊРµСЂ",
      price_amount: "350.00",
      currency: "RUB",
      estimated_days_min: 1,
      estimated_days_max: 2,
      provider_code: "cdek",
      tracking_status: "out_for_delivery",
      tracking_status_label: "РљСѓСЂСЊРµСЂ СѓР¶Рµ РµРґРµС‚",
      external_shipment_id: "SHIP-77",
      current_location: "РњРѕСЃРєРІР°",
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
          new_status_label: "РљСѓСЂСЊРµСЂ СѓР¶Рµ РµРґРµС‚",
          message: "РљСѓСЂСЊРµСЂ РІС‹РµС…Р°Р».",
          location: "РњРѕСЃРєРІР°",
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
    items: [],
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
        name: /Р’РѕР№РґРёС‚Рµ, С‡С‚РѕР±С‹ РѕС‚РєСЂС‹С‚СЊ РёСЃС‚РѕСЂРёСЋ РґРѕСЃС‚Р°РІРєРё/i
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

    expect(
      screen.getByLabelText("Р—Р°РіСЂСѓР·РєР° РѕС‚СЃР»РµР¶РёРІР°РЅРёСЏ Р·Р°РєР°Р·Р°")
    ).toBeInTheDocument();

    pending.resolve(makeOrder() as any);

    expect(
      await screen.findByRole("heading", { name: /Р—Р°РєР°Р· #77/i })
    ).toBeInTheDocument();
  });

  it("renders tracking details and timeline", async () => {
    useUserStore.setState({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile: null
    });
    jest.mocked(fetchOrder).mockResolvedValue(makeOrder() as any);

    renderWithQueryClient(<OrderTrackingPage orderId={77} />);

    expect(
      await screen.findByRole("heading", { name: /Р—Р°РєР°Р· #77/i })
    ).toBeInTheDocument();
    expect(fetchOrder).toHaveBeenCalledWith("access-token", 77);
    expect(screen.getByText("TRACK-77")).toBeInTheDocument();
    expect(screen.getAllByText("РљСѓСЂСЊРµСЂ СѓР¶Рµ РµРґРµС‚").length).toBeGreaterThan(0);
    expect(screen.getByText("РљСѓСЂСЊРµСЂ РІС‹РµС…Р°Р».")).toBeInTheDocument();
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
      name: /РћР±РЅРѕРІРёС‚СЊ СЃС‚Р°С‚СѓСЃ/i
    });
    fireEvent.click(button);

    await waitFor(() => {
      expect(refreshOrderTracking).toHaveBeenCalledWith("access-token", 77);
    });
  });
});
