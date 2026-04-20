const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      Accept: "application/json"
    }
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
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
