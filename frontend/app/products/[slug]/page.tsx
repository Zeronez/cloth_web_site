import { ProductDetailPage } from "../../../components/product/product-detail-page";

export const metadata = {
  title: "Товар"
};

export default function ProductRoute({
  params
}: {
  params: { slug: string };
}) {
  return <ProductDetailPage slug={params.slug} />;
}
