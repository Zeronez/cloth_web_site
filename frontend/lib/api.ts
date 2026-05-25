const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";
const API_PREFIX = process.env.NEXT_PUBLIC_API_PREFIX ?? "/api/v1";

function apiPath(path: string) {
  return `${API_PREFIX}${path}`;
}

export type AuthTokens = {
  access: string;
  refresh: string;
};

export type RefreshedTokens = {
  access: string;
  refresh?: string;
};

export type UserProfile = {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  avatar?: string | null;
  has_accepted_privacy_policy?: boolean;
  privacy_policy_version?: string;
  has_accepted_offer_agreement?: boolean;
  offer_agreement_version?: string;
  is_marketing_subscribed?: boolean;
  marketing_opt_in_version?: string;
  fit_profile?: Partial<FitProfile>;
  fit_profile_updated_at?: string | null;
};

export type Address = {
  id: number;
  label: string;
  recipient_name: string;
  phone: string;
  country: string;
  city: string;
  postal_code: string;
  line1: string;
  line2: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
};

export type LoginInput = {
  username: string;
  password: string;
};

export type RegisterInput = {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone: string;
  privacy_policy_accepted: boolean;
  offer_agreement_accepted: boolean;
  marketing_opt_in?: boolean;
};

export type AddressInput = {
  label: string;
  recipient_name: string;
  phone: string;
  country: string;
  city: string;
  postal_code: string;
  line1: string;
  line2: string;
  is_default: boolean;
};

export type ContactRequestTopic =
  | "order"
  | "delivery"
  | "return"
  | "product"
  | "partnership"
  | "other";

export type ContactRequestInput = {
  name: string;
  email: string;
  phone: string;
  topic: ContactRequestTopic;
  order_number: string;
  message: string;
};

export type ContactRequestStatus = "new" | "in_progress" | "resolved" | "spam";

export type ContactRequestResponse = {
  id?: number;
  status: ContactRequestStatus;
};

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export type Category = {
  id: number;
  name: string;
  slug: string;
  description: string;
};

export type Franchise = {
  id: number;
  name: string;
  slug: string;
  description: string;
};

export type ProductImage = {
  id: number;
  url: string;
  alt_text: string;
  is_main: boolean;
  sort_order: number;
};

export type ProductTag = {
  id: number;
  name: string;
  slug: string;
  label: string;
};

export type FitProfileSize = "XS" | "S" | "M" | "L" | "XL" | "XXL" | "ONE_SIZE";

export type FitProfilePreferredFit =
  | "slim"
  | "regular"
  | "relaxed"
  | "oversized";

export type FitProfilePreferredStyle =
  | "minimal"
  | "streetwear"
  | "dark_fantasy"
  | "sport"
  | "casual";

export type FitProfilePreferredSeason =
  | "spring"
  | "summer"
  | "autumn"
  | "winter"
  | "all_season";

export type FitProfile = {
  height_cm?: number | null;
  weight_kg?: string | null;
  chest_cm?: number | null;
  waist_cm?: number | null;
  hips_cm?: number | null;
  inseam_cm?: number | null;
  preferred_fit?: FitProfilePreferredFit | null;
  preferred_style?: FitProfilePreferredStyle | null;
  preferred_season?: FitProfilePreferredSeason | null;
  tops_usual_size?: FitProfileSize | null;
  bottoms_usual_size?: FitProfileSize | null;
  notes?: string | null;
  budget_min_rub?: number | null;
  budget_max_rub?: number | null;
  updated_at?: string | null;
  is_complete?: boolean;
};

export type FitRecommendationConfidence = "none" | "low" | "medium" | "high";

export type FitRecommendationWarning =
  | "fit_profile_incomplete"
  | "no_active_sizes"
  | "one_size_only"
  | "closest_available_size_selected"
  | "recommended_size_out_of_stock"
  | "style_fit_mismatch"
  | "season_mismatch"
  | "style_mismatch";

export type FitRecommendationOutfitItem = {
  id: number;
  name: string;
  slug: string;
  category: string;
  franchise: string | null;
  base_price: string;
  main_image_url: string | null;
  reason: string;
};

export type FitRecommendation = {
  recommended_size: FitProfileSize | null;
  confidence: FitRecommendationConfidence;
  profile_ready: boolean;
  missing_profile_fields: Array<keyof FitProfile | string>;
  summary: string;
  explanation: string;
  reasons: string[];
  warnings: Array<FitRecommendationWarning | string>;
  outfit: {
    items: FitRecommendationOutfitItem[];
    total_price: string | null;
  };
};

export type ProductVariant = {
  id: number;
  sku: string;
  size: FitProfileSize;
  color: string;
  stock_quantity: number;
  price_delta: string;
  price: string;
  is_active: boolean;
};

export type Product = {
  id: number;
  name: string;
  slug: string;
  category: Category;
  franchise: Franchise | null;
  base_price: string;
  is_featured: boolean;
  main_image: ProductImage | null;
  total_stock: number;
  tags?: ProductTag[];
  description?: string;
  images?: ProductImage[];
  variants?: ProductVariant[];
  fit_recommendation?: FitRecommendation | null;
};

export type OrderStatus =
  | "pending"
  | "paid"
  | "picking"
  | "packed"
  | "shipped"
  | "delivered"
  | "cancelled"
  | "returned";

export type OrderItem = {
  id: number;
  variant_id: number;
  product: {
    id: number;
    name: string;
    slug: string;
    is_active: boolean;
    main_image: ProductImage | null;
  };
  product_name: string;
  sku: string;
  size: string;
  color: string;
  quantity: number;
  price_at_purchase: string;
  line_total: string;
};

export type OrderDeliverySnapshot = {
  method_code: string;
  method_name: string;
  method_kind: string;
  method_kind_label: string;
  price_amount: string;
  currency: string;
  estimated_days_min: number | null;
  estimated_days_max: number | null;
  provider_code: string;
  tracking_status: string;
  tracking_status_label: string;
  external_shipment_id: string;
  current_location: string;
  last_tracking_sync_at: string | null;
  recipient_name: string;
  recipient_phone: string;
  country: string;
  city: string;
  postal_code: string;
  line1: string;
  line2: string;
  tracking_events: Array<{
    id: number;
    event_type: string;
    previous_status: string;
    new_status: string;
    new_status_label: string;
    message: string;
    location: string;
    payload: unknown;
    external_event_id: string;
    happened_at: string | null;
    created_at: string;
  }>;
};

export type Order = {
  id: number;
  status: OrderStatus;
  status_label?: string;
  total_amount: string;
  track_number: string;
  items_count: number;
  shipping_address: {
    name: string;
    phone: string;
    country: string;
    city: string;
    postal_code: string;
    line1: string;
    line2: string;
  };
  delivery: OrderDeliverySnapshot | null;
  shipping_name: string;
  shipping_phone: string;
  shipping_country: string;
  shipping_city: string;
  shipping_postal_code: string;
  shipping_line1: string;
  shipping_line2: string;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
};

export type DeliveryMethod = {
  code: string;
  name: string;
  kind: string;
  kind_label: string;
  description: string;
  price_amount: string;
  currency: string;
  estimated_days_min: number | null;
  estimated_days_max: number | null;
  requires_address: boolean;
  sort_order: number;
};

export type PaymentMethod = {
  code: string;
  name: string;
  description: string;
  provider_code: string;
  session_mode: string;
  session_mode_label: string;
  currency: string;
  sort_order: number;
};

export type PaymentStatus =
  | "pending"
  | "session_created"
  | "authorized"
  | "succeeded"
  | "failed"
  | "cancelled"
  | "refunded"
  | "expired";

export type PaymentEvent = {
  id: number;
  event_type: string;
  previous_status: string;
  new_status: PaymentStatus;
  new_status_label: string;
  message: string;
  payload: unknown;
  external_event_id: string;
  created_at: string;
};

export type Payment = {
  id: number;
  order: number;
  method_code: string;
  provider_code: string;
  status: PaymentStatus;
  status_label: string;
  amount: string;
  currency: string;
  external_payment_id: string;
  session_expires_at: string | null;
  events: PaymentEvent[];
  created_at: string;
  updated_at: string;
};

export type PaymentSession = {
  payment: Payment;
  created: boolean;
  provider: string;
  confirmation_url: string | null;
  message: string;
};

export type PaymentReturnState =
  | "awaiting_webhook"
  | "paid"
  | "retry_available"
  | "refunded";

export type PaymentReturnStatus = {
  payment: Payment;
  order: Order;
  provider: string;
  return_state: PaymentReturnState;
  message: string;
  confirmation_url: string | null;
  can_retry: boolean;
};

const ORDER_STATUS_LABELS: Record<OrderStatus, string> = {
  pending: "\u041e\u0436\u0438\u0434\u0430\u0435\u0442 \u043e\u043f\u043b\u0430\u0442\u044b",
  paid: "\u041e\u043f\u043b\u0430\u0447\u0435\u043d",
  picking: "\u041d\u0430 \u0441\u0431\u043e\u0440\u043a\u0435",
  packed: "\u0423\u043f\u0430\u043a\u043e\u0432\u0430\u043d",
  shipped: "\u041f\u0435\u0440\u0435\u0434\u0430\u043d \u0432 \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0443",
  delivered: "\u0414\u043e\u0441\u0442\u0430\u0432\u043b\u0435\u043d",
  cancelled: "\u041e\u0442\u043c\u0435\u043d\u0451\u043d",
  returned: "\u0412\u043e\u0437\u0432\u0440\u0430\u0449\u0451\u043d"
};

const ORDER_STATUS_TONES: Record<OrderStatus, string> = {
  pending: "border-neon-amber/40 bg-neon-amber/10 text-neon-amber",
  paid: "border-neon-teal/40 bg-neon-teal/10 text-neon-teal",
  picking: "border-neon-teal/40 bg-neon-teal/10 text-neon-teal",
  packed: "border-fuchsia-400/40 bg-fuchsia-500/10 text-fuchsia-100",
  shipped: "border-neon-amber/40 bg-neon-amber/10 text-neon-amber",
  delivered: "border-emerald-400/40 bg-emerald-500/10 text-emerald-100",
  cancelled: "border-red-400/30 bg-red-500/10 text-red-100",
  returned: "border-red-400/30 bg-red-500/10 text-red-100"
};

const ORDER_STATUS_NOTES: Record<OrderStatus, string> = {
  pending: "\u0416\u0434\u0451\u043c \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u0435 \u043e\u043f\u043b\u0430\u0442\u044b, \u043f\u043e\u0441\u043b\u0435 \u044d\u0442\u043e\u0433\u043e \u0437\u0430\u043a\u0430\u0437 \u0443\u0439\u0434\u0451\u0442 \u0432 \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0443.",
  paid: "\u041e\u043f\u043b\u0430\u0442\u0430 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0430, \u0437\u0430\u043a\u0430\u0437 \u0433\u043e\u0442\u043e\u0432\u0438\u043c \u043a \u0441\u0431\u043e\u0440\u043a\u0435.",
  picking: "\u041a\u043e\u043c\u0430\u043d\u0434\u0430 AnimeAttire \u0441\u043e\u0431\u0438\u0440\u0430\u0435\u0442 \u043f\u043e\u0437\u0438\u0446\u0438\u0438 \u043f\u043e \u0441\u043a\u043b\u0430\u0434\u0443.",
  packed: "\u0417\u0430\u043a\u0430\u0437 \u0443\u043f\u0430\u043a\u043e\u0432\u0430\u043d \u0438 \u0436\u0434\u0451\u0442 \u043f\u0435\u0440\u0435\u0434\u0430\u0447\u0443 \u0432 \u0441\u043b\u0443\u0436\u0431\u0443 \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438.",
  shipped: "\u041f\u043e\u0441\u044b\u043b\u043a\u0430 \u0443\u0436\u0435 \u0432 \u043f\u0443\u0442\u0438. \u041e\u0442\u0441\u043b\u0435\u0436\u0438\u0432\u0430\u043d\u0438\u0435 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e \u043f\u043e \u0442\u0440\u0435\u043a-\u043d\u043e\u043c\u0435\u0440\u0443.",
  delivered: "\u0417\u0430\u043a\u0430\u0437 \u0434\u043e\u0441\u0442\u0430\u0432\u043b\u0435\u043d. \u0415\u0441\u043b\u0438 \u0447\u0442\u043e-\u0442\u043e \u043d\u0435 \u043f\u043e\u0434\u043e\u0448\u043b\u043e, \u043c\u043e\u0436\u043d\u043e \u043e\u0444\u043e\u0440\u043c\u0438\u0442\u044c \u0432\u043e\u0437\u0432\u0440\u0430\u0442.",
  cancelled: "\u0417\u0430\u043a\u0430\u0437 \u043e\u0442\u043c\u0435\u043d\u0451\u043d. \u0415\u0441\u043b\u0438 \u044d\u0442\u043e \u043f\u0440\u043e\u0438\u0437\u043e\u0448\u043b\u043e \u043d\u0435\u043e\u0436\u0438\u0434\u0430\u043d\u043d\u043e, \u0441\u0432\u044f\u0436\u0438\u0442\u0435\u0441\u044c \u0441 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u043e\u0439.",
  returned: "\u041f\u043e \u0437\u0430\u043a\u0430\u0437\u0443 \u043e\u0444\u043e\u0440\u043c\u043b\u0435\u043d \u0432\u043e\u0437\u0432\u0440\u0430\u0442 \u0438\u043b\u0438 \u043e\u0431\u0440\u0430\u0442\u043d\u0430\u044f \u043b\u043e\u0433\u0438\u0441\u0442\u0438\u043a\u0430 \u0443\u0436\u0435 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0430."
};

export function getOrderStatusLabel(status: OrderStatus) {
  return ORDER_STATUS_LABELS[status] ?? "\u0421\u0442\u0430\u0442\u0443\u0441 \u043d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u0435\u043d";
}

export function getOrderStatusTone(status: OrderStatus) {
  return (
    ORDER_STATUS_TONES[status] ??
    "border-neon-crimson/40 bg-neon-crimson/10 text-neon-crimson"
  );
}

export function getOrderStatusNote(status: OrderStatus) {
  return (
    ORDER_STATUS_NOTES[status] ??
    "\u0421\u0442\u0430\u0442\u0443\u0441 \u0437\u0430\u043a\u0430\u0437\u0430 \u043c\u043e\u0436\u043d\u043e \u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u043f\u043e\u0437\u0436\u0435 \u0432 \u043b\u0438\u0447\u043d\u043e\u043c \u043a\u0430\u0431\u0438\u043d\u0435\u0442\u0435."
  );
}

const PAYMENT_STATUS_LABELS: Record<PaymentStatus, string> = {
  pending: "Ожидает оплаты",
  session_created: "Сессия создана",
  authorized: "Авторизован",
  succeeded: "Оплачен",
  failed: "Платёж не прошёл",
  cancelled: "Отменён",
  refunded: "Возврат оформлен",
  expired: "Сессия истекла"
};

const PAYMENT_STATUS_TONES: Record<PaymentStatus, string> = {
  pending: "border-neon-amber/40 bg-neon-amber/10 text-neon-amber",
  session_created: "border-neon-amber/40 bg-neon-amber/10 text-neon-amber",
  authorized: "border-neon-teal/40 bg-neon-teal/10 text-neon-teal",
  succeeded: "border-neon-teal/40 bg-neon-teal/10 text-neon-teal",
  failed: "border-red-400/30 bg-red-500/10 text-red-100",
  cancelled: "border-red-400/30 bg-red-500/10 text-red-100",
  refunded: "border-red-400/30 bg-red-500/10 text-red-100",
  expired: "border-red-400/30 bg-red-500/10 text-red-100"
};

const PAYMENT_STATUS_FOLLOW_UP: Record<PaymentStatus, string> = {
  pending:
    "Платёж ожидает подтверждения. Заказ сохранён, статус можно проверить в личном кабинете.",
  session_created:
    "Платёжная сессия создана. Если ссылка на оплату доступна, завершите платёж по ней.",
  authorized:
    "Платёж авторизован. Финальный статус может обновиться после обработки провайдера.",
  succeeded:
    "Платёж прошёл успешно. Статус и детали заказа доступны в личном кабинете.",
  failed:
    "Оплата не прошла. Заказ сохранён, попробуйте повторить платёж позже.",
  cancelled:
    "Оплата отменена. Заказ сохранён, вы сможете повторить попытку позже.",
  refunded:
    "Платёж возвращён. Если это не плановый возврат, проверьте детали заказа.",
  expired:
    "Сессия оплаты истекла. Заказ сохранён, потребуется новая попытка оплаты."
};

const PAYMENT_STATUS_ACTIONS: Record<PaymentStatus, string> = {
  pending: "Перейти к оплате",
  session_created: "Перейти к оплате",
  authorized: "Перейти к оплате",
  succeeded: "Перейти к заказу",
  failed: "Повторить оплату",
  cancelled: "Повторить оплату",
  refunded: "Повторить оплату",
  expired: "Повторить оплату"
};

export function getPaymentStatusLabel(status: PaymentStatus) {
  return PAYMENT_STATUS_LABELS[status] ?? "Статус неизвестен";
}

export function getPaymentStatusTone(status: PaymentStatus) {
  return PAYMENT_STATUS_TONES[status] ?? "border-neon-crimson/40 bg-neon-crimson/10 text-neon-crimson";
}

export function getPaymentStatusFollowUp(status: PaymentStatus) {
  return PAYMENT_STATUS_FOLLOW_UP[status] ?? "Статус оплаты можно проверить в личном кабинете.";
}

export function getPaymentStatusActionLabel(status: PaymentStatus) {
  return PAYMENT_STATUS_ACTIONS[status] ?? "Перейти к оплате";
}

export type ServerCartItem = {
  id: number;
  variant: ProductVariant;
  product: {
    id: number;
    name: string;
    slug: string;
    base_price: string;
    is_active: boolean;
    main_image: ProductImage | null;
  };
  quantity: number;
  unit_price: string;
  line_total: string;
  created_at: string;
  updated_at: string;
};

export type ServerCart = {
  id: number;
  items: ServerCartItem[];
  total_amount: string;
  subtotal_amount: string;
  total_quantity: number;
  created_at: string;
  updated_at: string;
};

export type CheckoutInput = {
  idempotency_key?: string;
  delivery_method_code?: string;
  shipping_name: string;
  shipping_phone: string;
  shipping_country: string;
  shipping_city: string;
  shipping_postal_code: string;
  shipping_line1: string;
  shipping_line2: string;
};

export type FavoriteProductEntry = {
  id: number;
  product_id: number;
  product: Product;
  created_at: string;
};

export type FavoriteProductMutationResult = FavoriteProductEntry & {
  created: boolean;
};

export type AccountExportPayload = {
  exported_at: string;
  profile: UserProfile;
  addresses: Address[];
  favorites: FavoriteProductEntry[];
  cart: ServerCart | null;
  orders: Order[];
  payments: Payment[];
  notifications: Array<{
    id: number;
    order_id: number;
    notification_type: string;
    channel: string;
    status: string;
    recipient: string;
    subject: string;
    body: string;
    error_message: string;
    delivered_at: string | null;
    created_at: string;
    updated_at: string;
    attempts: Array<{
      id: number;
      status: string;
      provider_message_id: string;
      error_message: string;
      created_at: string;
    }>;
  }>;
  contact_requests: Array<{
    id: number;
    name: string;
    email: string;
    phone: string;
    topic: string;
    order_number: string;
    message: string;
    status: string;
    created_at: string;
  }>;
};

export type DeleteAccountResponse = {
  status: "deleted";
  deleted_at: string;
  retained_order_count: number;
  retained_payment_count: number;
  deleted_email: string;
};

type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

async function apiGet<T>(path: string): Promise<T> {
  return apiRequest<T>(path);
}

async function readResponseBody(response: Response) {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text().catch(() => "");
}

function buildApiErrorMessage(payload: unknown, fallback: string) {
  if (typeof payload === "string" && payload.trim()) {
    return payload;
  }

  if (payload && typeof payload === "object") {
    const entries = Object.entries(payload as Record<string, unknown>);

    if (entries.length > 0) {
      return entries
        .flatMap(([key, value]) => {
          if (
            value &&
            typeof value === "object" &&
            !Array.isArray(value) &&
            "message" in value &&
            typeof (value as { message?: unknown }).message === "string"
          ) {
            return [`${key}: ${(value as { message: string }).message}`];
          }

          if (Array.isArray(value)) {
            return value.map((item) => `${key}: ${item}`);
          }

          if (typeof value === "string") {
            return [`${key}: ${value}`];
          }

          return [`${key}: ${JSON.stringify(value)}`];
        })
        .join("; ");
    }
  }

  return fallback;
}

async function apiRequest<T>(
  path: string,
  options: {
    method?: string;
    body?: unknown;
    token?: string | null;
    headers?: Record<string, string>;
  } = {}
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: options.method ?? "GET",
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
      ...options.headers
    },
    body:
      options.body === undefined ? undefined : JSON.stringify(options.body)
  });

  const payload = await readResponseBody(response);

  if (!response.ok) {
    throw new ApiError(
      buildApiErrorMessage(
        payload,
        `API request failed with status ${response.status}`
      ),
      response.status,
      payload
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return payload as T;
}

export async function fetchProducts(
  params: URLSearchParams,
  token?: string | null
) {
  const query = params.toString();
  return apiRequest<Paginated<Product>>(
    apiPath(`/products/${query ? `?${query}` : ""}`),
    { token }
  );
}

export async function fetchProduct(slug: string, token?: string | null) {
  return apiRequest<Product>(apiPath(`/products/${slug}/`), { token });
}

export async function fetchCategories() {
  return apiGet<Paginated<Category>>(apiPath("/categories/"));
}

export async function fetchFranchises() {
  return apiGet<Paginated<Franchise>>(apiPath("/franchises/"));
}

export async function fetchOrders(token: string) {
  return apiRequest<Paginated<Order>>(apiPath("/orders/"), { token });
}

export async function fetchOrder(token: string, orderId: number) {
  return apiRequest<Order>(apiPath(`/orders/${orderId}/`), { token });
}

export async function refreshOrderTracking(token: string, orderId: number) {
  return apiRequest<Order>(apiPath(`/orders/${orderId}/tracking-refresh/`), {
    method: "POST",
    token
  });
}

export async function fetchDeliveryMethods() {
  return apiRequest<Paginated<DeliveryMethod>>(apiPath("/delivery-methods/"));
}

export async function fetchPaymentMethods() {
  return apiRequest<Paginated<PaymentMethod>>(apiPath("/payment-methods/"));
}

export async function fetchCart(token?: string | null) {
  return apiRequest<ServerCart>(apiPath("/cart/"), { token });
}

export async function addCartItem(
  token: string | null,
  variantId: number,
  quantity: number
) {
  return apiRequest<ServerCart>(apiPath("/cart/items/"), {
    method: "POST",
    token,
    body: {
      variant_id: variantId,
      quantity
    }
  });
}

export async function updateCartItemQuantity(
  token: string | null,
  itemId: number,
  quantity: number
) {
  return apiRequest<ServerCart>(apiPath(`/cart/items/${itemId}/`), {
    method: "PATCH",
    token,
    body: { quantity }
  });
}

export async function deleteCartItem(token: string | null, itemId: number) {
  return apiRequest<ServerCart>(apiPath(`/cart/items/${itemId}/`), {
    method: "DELETE",
    token
  });
}

export async function checkoutOrder(token: string, input: CheckoutInput) {
  return apiRequest<Order>(apiPath("/orders/checkout/"), {
    method: "POST",
    token,
    body: input
  });
}

export async function createPaymentSession(
  token: string,
  input: {
    order_id: number;
    payment_method_code: string;
    idempotency_key?: string;
  }
) {
  return apiRequest<PaymentSession>(apiPath("/payments/sessions/"), {
    method: "POST",
    token,
    body: input
  });
}

export async function fetchPayment(token: string, paymentId: number) {
  return apiRequest<Payment>(apiPath(`/payments/${paymentId}/`), { token });
}

export async function fetchPaymentReturnStatus(
  token: string,
  paymentId: number,
  input: {
    provider?: string;
    external_payment_id?: string;
  } = {}
) {
  const params = new URLSearchParams();
  if (input.provider) {
    params.set("provider", input.provider);
  }
  if (input.external_payment_id) {
    params.set("external_payment_id", input.external_payment_id);
  }
  const query = params.toString();
  return apiRequest<PaymentReturnStatus>(
    apiPath(`/payments/${paymentId}/return-status/${query ? `?${query}` : ""}`),
    {
      token
    }
  );
}

export async function fetchFavorites(token: string) {
  return apiRequest<FavoriteProductEntry[]>(apiPath("/favorites/"), { token });
}

export async function addFavorite(token: string, productId: number) {
  return apiRequest<FavoriteProductMutationResult>(apiPath("/favorites/"), {
    method: "POST",
    token,
    body: { product_id: productId }
  });
}

export async function removeFavorite(token: string, productId: number) {
  return apiRequest<{ product_id: number; deleted: boolean }>(
    apiPath(`/favorites/products/${productId}/`),
    {
      method: "DELETE",
      token
    }
  );
}

export async function loginUser(input: LoginInput) {
  return apiRequest<AuthTokens>(apiPath("/auth/token/"), {
    method: "POST",
    body: input
  });
}

export async function refreshTokens(refresh: string) {
  return apiRequest<RefreshedTokens>(apiPath("/auth/token/refresh/"), {
    method: "POST",
    body: { refresh }
  });
}

export async function registerUser(input: RegisterInput) {
  return apiRequest<UserProfile>(apiPath("/auth/register/"), {
    method: "POST",
    body: input
  });
}

export async function fetchMe(token: string) {
  return apiRequest<UserProfile>(apiPath("/users/me/"), { token });
}

export async function updateMe(token: string, input: Partial<UserProfile>) {
  return apiRequest<UserProfile>(apiPath("/users/me/"), {
    method: "PATCH",
    token,
    body: input
  });
}

export async function fetchFitProfile(token: string) {
  return apiRequest<FitProfile>(apiPath("/users/me/fit-profile/"), { token });
}

export async function updateFitProfile(token: string, input: Partial<FitProfile>) {
  return apiRequest<FitProfile>(apiPath("/users/me/fit-profile/"), {
    method: "PATCH",
    token,
    body: input
  });
}

export async function exportAccountData(token: string) {
  return apiRequest<AccountExportPayload>(apiPath("/users/me/export/"), {
    token
  });
}

export async function deleteAccount(token: string, currentPassword: string) {
  return apiRequest<DeleteAccountResponse>(apiPath("/users/me/delete/"), {
    method: "POST",
    token,
    body: { current_password: currentPassword }
  });
}

export async function fetchAddresses(token: string) {
  return apiRequest<Address[]>(apiPath("/addresses/"), { token });
}

export async function createAddress(token: string, input: AddressInput) {
  return apiRequest<Address>(apiPath("/addresses/"), {
    method: "POST",
    token,
    body: input
  });
}

export async function createContactRequest(input: ContactRequestInput) {
  return apiRequest<ContactRequestResponse>(apiPath("/contact-requests/"), {
    method: "POST",
    body: input
  });
}

export async function updateAddress(
  token: string,
  id: number,
  input: Partial<AddressInput>
) {
  return apiRequest<Address>(apiPath(`/addresses/${id}/`), {
    method: "PATCH",
    token,
    body: input
  });
}

export async function deleteAddress(token: string, id: number) {
  return apiRequest<void>(apiPath(`/addresses/${id}/`), {
    method: "DELETE",
    token
  });
}

export async function logoutUser(token: string, refresh: string) {
  return apiRequest<void>(apiPath("/auth/logout/"), {
    method: "POST",
    token,
    body: { refresh }
  });
}
