import { ProductDetailPage } from "../../../components/product/product-detail-page";

export const metadata = {
  title: "Товар"
};

export default async function ProductRoute({
  params
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return <ProductDetailPage slug={slug} />;
}
