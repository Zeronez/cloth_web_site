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
