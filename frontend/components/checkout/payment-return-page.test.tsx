import type { ReactNode } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import {
  createPaymentSession,
  fetchPaymentReturnStatus
} from "../../lib/api";
import { useUserStore } from "../../stores/user-store";
import { PaymentReturnPage } from "./payment-return-page";

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
  createPaymentSession: jest.fn(),
  fetchPaymentReturnStatus: jest.fn()
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

function makeReturnStatus(status: string, confirmationUrl: string | null = null) {
  return {
    payment: {
      id: 3001,
      order: 9001,
      method_code: "yookassa-card",
      provider_code: "yookassa",
      status,
      status_label: "Статус",
      amount: "605.00",
      currency: "RUB",
      external_payment_id: "ext-3001",
      session_expires_at: null,
      events: [],
      created_at: "2026-04-22T10:00:00Z",
      updated_at: "2026-04-22T10:00:00Z"
    },
    order: {
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
      delivery: null,
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
    },
    provider: "yookassa",
    return_state:
      status === "succeeded"
        ? "paid"
        : status === "session_created" || status === "authorized"
          ? "awaiting_webhook"
          : "retry_available",
    message: "Тестовое сообщение по возврату.",
    confirmation_url: confirmationUrl,
    can_retry: true
  };
}

describe("PaymentReturnPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useUserStore.setState({
      accessToken: null,
      refreshToken: null,
      profile: null
    });
  });

  it("shows a safe fallback when payment id is missing", () => {
    renderWithQueryClient(<PaymentReturnPage paymentId={null} provider="" />);

    expect(
      screen.getByRole("heading", { name: /не удалось определить платеж/i })
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /открыть кабинет/i })).toBeInTheDocument();
  });

  it("asks the user to sign in before reading return status", () => {
    renderWithQueryClient(
      <PaymentReturnPage paymentId={3001} provider="yookassa" />
    );

    expect(
      screen.getByRole("heading", {
        name: /войдите, чтобы проверить статус оплаты/i
      })
    ).toBeInTheDocument();
  });

  it("renders the resolved return status and provider payment link", async () => {
    useUserStore.setState({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile: null
    });
    jest.mocked(fetchPaymentReturnStatus).mockResolvedValue(
      makeReturnStatus(
        "session_created",
        "https://pay.example.test/checkout/return-session"
      ) as any
    );

    renderWithQueryClient(
      <PaymentReturnPage
        paymentId={3001}
        provider="yookassa"
        externalPaymentId="ext-3001"
      />
    );

    expect(
      await screen.findByRole("heading", {
        name: /заказ #9001/i
      })
    ).toBeInTheDocument();
    expect(fetchPaymentReturnStatus).toHaveBeenCalledWith("access-token", 3001, {
      provider: "yookassa",
      external_payment_id: "ext-3001"
    });
    expect(
      screen.getByRole("link", { name: /перейти к оплате/i })
    ).toHaveAttribute("href", "https://pay.example.test/checkout/return-session");
  });

  it("can prepare a new payment session when retry is available", async () => {
    useUserStore.setState({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile: null
    });
    jest.mocked(fetchPaymentReturnStatus).mockResolvedValue(
      makeReturnStatus("failed", null) as any
    );
    jest.mocked(createPaymentSession).mockResolvedValue({
      payment: makeReturnStatus("failed").payment,
      created: true,
      provider: "yookassa",
      confirmation_url: "https://pay.example.test/checkout/new-session",
      message: "Новая платежная сессия готова."
    } as any);

    renderWithQueryClient(
      <PaymentReturnPage paymentId={3001} provider="yookassa" />
    );

    const button = await screen.findByRole("button", {
      name: /подготовить новую оплату/i
    });
    fireEvent.click(button);

    await waitFor(() => {
      expect(createPaymentSession).toHaveBeenCalledWith("access-token", {
        order_id: 9001,
        payment_method_code: "yookassa-card",
        idempotency_key: expect.stringMatching(
          /^return-9001-yookassa-card-\d+$/
        )
      });
    });

    expect(
      await screen.findByRole("link", { name: /повторить оплату/i })
    ).toHaveAttribute("href", "https://pay.example.test/checkout/new-session");
    expect(screen.getByText(/новая платежная сессия готова/i)).toBeInTheDocument();
  });
});
