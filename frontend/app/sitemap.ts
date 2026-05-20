import type { MetadataRoute } from "next";

import { fetchCategories, fetchProducts } from "../lib/api";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

  const staticRoutes: MetadataRoute.Sitemap = [
    { url: `${baseUrl}/`, changeFrequency: "daily", priority: 1 },
    { url: `${baseUrl}/catalog`, changeFrequency: "daily", priority: 0.9 },
    { url: `${baseUrl}/search`, changeFrequency: "weekly", priority: 0.6 },
    { url: `${baseUrl}/delivery`, changeFrequency: "monthly", priority: 0.3 },
    { url: `${baseUrl}/returns`, changeFrequency: "monthly", priority: 0.3 },
    { url: `${baseUrl}/offer`, changeFrequency: "monthly", priority: 0.2 },
    { url: `${baseUrl}/privacy`, changeFrequency: "monthly", priority: 0.2 },
    { url: `${baseUrl}/contacts`, changeFrequency: "monthly", priority: 0.2 }
  ];

  try {
    const params = new URLSearchParams();
    params.set("page_size", "200");
    const [products, categories] = await Promise.all([
      fetchProducts(params),
      fetchCategories()
    ]);

    const productRoutes = products.results.map((product) => ({
      url: `${baseUrl}/products/${product.slug}`,
      changeFrequency: "weekly" as const,
      priority: 0.7
    }));

    const categoryRoutes = categories.results.map((category) => ({
      url: `${baseUrl}/catalog?category=${category.slug}`,
      changeFrequency: "weekly" as const,
      priority: 0.5
    }));

    return [...staticRoutes, ...productRoutes, ...categoryRoutes];
  } catch {
    return staticRoutes;
  }
}

