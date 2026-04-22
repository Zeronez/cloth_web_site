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
