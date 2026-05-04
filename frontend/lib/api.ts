const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type AuthTokens = {
  access: string;
  refresh: string;
};

export type UserProfile = {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  avatar?: string | null;
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

export type ProductVariant = {
  id: number;
  sku: string;
  size: string;
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
  description?: string;
  images?: ProductImage[];
  variants?: ProductVariant[];
};

export type OrderStatus = "pending" | "paid" | "shipped" | "cancelled";

export type OrderItem = {
  id: number;
  variant_id: number;
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
  recipient_name: string;
  recipient_phone: string;
  country: string;
  city: string;
  postal_code: string;
  line1: string;
  line2: string;
};

export type Order = {
  id: number;
  status: OrderStatus;
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
  pending: "Ожидает оплаты",
  paid: "Оплачен",
  shipped: "Отправлен",
  cancelled: "Отменён"
};

const ORDER_STATUS_TONES: Record<OrderStatus, string> = {
  pending: "border-neon-amber/40 bg-neon-amber/10 text-neon-amber",
  paid: "border-neon-teal/40 bg-neon-teal/10 text-neon-teal",
  shipped: "border-neon-amber/40 bg-neon-amber/10 text-neon-amber",
  cancelled: "border-red-400/30 bg-red-500/10 text-red-100"
};

export function getOrderStatusLabel(status: OrderStatus) {
  return ORDER_STATUS_LABELS[status] ?? "Статус неизвестен";
}

export function getOrderStatusTone(status: OrderStatus) {
  return ORDER_STATUS_TONES[status] ?? "border-neon-crimson/40 bg-neon-crimson/10 text-neon-crimson";
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

export async function fetchProducts(params: URLSearchParams) {
  const query = params.toString();
  return apiGet<Paginated<Product>>(`/api/products/${query ? `?${query}` : ""}`);
}

export async function fetchProduct(slug: string) {
  return apiGet<Product>(`/api/products/${slug}/`);
}

export async function fetchCategories() {
  return apiGet<Paginated<Category>>("/api/categories/");
}

export async function fetchFranchises() {
  return apiGet<Paginated<Franchise>>("/api/franchises/");
}

export async function fetchOrders(token: string) {
  return apiRequest<Paginated<Order>>("/api/orders/", { token });
}

export async function fetchOrder(token: string, orderId: number) {
  return apiRequest<Order>(`/api/orders/${orderId}/`, { token });
}

export async function fetchDeliveryMethods() {
  return apiRequest<Paginated<DeliveryMethod>>("/api/delivery-methods/");
}

export async function fetchPaymentMethods() {
  return apiRequest<Paginated<PaymentMethod>>("/api/payment-methods/");
}

export async function fetchCart(token?: string | null) {
  return apiRequest<ServerCart>("/api/cart/", { token });
}

export async function addCartItem(
  token: string | null,
  variantId: number,
  quantity: number
) {
  return apiRequest<ServerCart>("/api/cart/items/", {
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
  return apiRequest<ServerCart>(`/api/cart/items/${itemId}/`, {
    method: "PATCH",
    token,
    body: { quantity }
  });
}

export async function deleteCartItem(token: string | null, itemId: number) {
  return apiRequest<ServerCart>(`/api/cart/items/${itemId}/`, {
    method: "DELETE",
    token
  });
}

export async function checkoutOrder(token: string, input: CheckoutInput) {
  return apiRequest<Order>("/api/orders/checkout/", {
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
  return apiRequest<PaymentSession>("/api/payments/sessions/", {
    method: "POST",
    token,
    body: input
  });
}

export async function fetchPayment(token: string, paymentId: number) {
  return apiRequest<Payment>(`/api/payments/${paymentId}/`, { token });
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
    `/api/payments/${paymentId}/return-status/${query ? `?${query}` : ""}`,
    {
      token
    }
  );
}

export async function fetchFavorites(token: string) {
  return apiRequest<FavoriteProductEntry[]>("/api/favorites/", { token });
}

export async function addFavorite(token: string, productId: number) {
  return apiRequest<FavoriteProductMutationResult>("/api/favorites/", {
    method: "POST",
    token,
    body: { product_id: productId }
  });
}

export async function removeFavorite(token: string, productId: number) {
  return apiRequest<{ product_id: number; deleted: boolean }>(
    `/api/favorites/products/${productId}/`,
    {
      method: "DELETE",
      token
    }
  );
}

export async function loginUser(input: LoginInput) {
  return apiRequest<AuthTokens>("/api/auth/token/", {
    method: "POST",
    body: input
  });
}

export async function registerUser(input: RegisterInput) {
  return apiRequest<UserProfile>("/api/auth/register/", {
    method: "POST",
    body: input
  });
}

export async function fetchMe(token: string) {
  return apiRequest<UserProfile>("/api/users/me/", { token });
}

export async function updateMe(token: string, input: Partial<UserProfile>) {
  return apiRequest<UserProfile>("/api/users/me/", {
    method: "PATCH",
    token,
    body: input
  });
}

export async function fetchAddresses(token: string) {
  return apiRequest<Address[]>("/api/addresses/", { token });
}

export async function createAddress(token: string, input: AddressInput) {
  return apiRequest<Address>("/api/addresses/", {
    method: "POST",
    token,
    body: input
  });
}

export async function createContactRequest(input: ContactRequestInput) {
  return apiRequest<ContactRequestResponse>("/api/contact-requests/", {
    method: "POST",
    body: input
  });
}

export async function updateAddress(
  token: string,
  id: number,
  input: Partial<AddressInput>
) {
  return apiRequest<Address>(`/api/addresses/${id}/`, {
    method: "PATCH",
    token,
    body: input
  });
}

export async function deleteAddress(token: string, id: number) {
  return apiRequest<void>(`/api/addresses/${id}/`, {
    method: "DELETE",
    token
  });
}

export async function logoutUser(token: string, refresh: string) {
  return apiRequest<void>("/api/auth/logout/", {
    method: "POST",
    token,
    body: { refresh }
  });
}
