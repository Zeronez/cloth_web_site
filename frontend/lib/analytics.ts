export type AnalyticsEventName =
  | "product_view"
  | "add_to_cart"
  | "checkout_start"
  | "payment_success";

type AnalyticsPayload = Record<string, unknown>;

function safeConsoleInfo(message: string, payload?: AnalyticsPayload) {
  if (process.env.NODE_ENV === "production") {
    return;
  }

  // eslint-disable-next-line no-console
  console.info(`[analytics] ${message}`, payload ?? {});
}

export function trackEvent(name: AnalyticsEventName, payload: AnalyticsPayload = {}) {
  if (typeof window === "undefined") {
    return;
  }

  const win = window as unknown as { dataLayer?: Array<Record<string, unknown>> };
  if (Array.isArray(win.dataLayer)) {
    win.dataLayer.push({ event: name, ...payload });
  }

  safeConsoleInfo(name, payload);
}

