import { fetchProduct } from "@/lib/api";
import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ProductActions } from "./ProductActions";

export const dynamic = "force-dynamic";

const GRADIENTS = [
  "from-orange-400 via-rose-400 to-pink-500",
  "from-blue-400 via-indigo-500 to-purple-500",
  "from-emerald-400 via-teal-500 to-cyan-500",
  "from-amber-400 via-orange-500 to-red-500",
  "from-violet-400 via-purple-500 to-fuchsia-500",
];

function getCategoryIcon(category: string) {
  const map: Record<string, string> = {
    electronics: "📱",
    footwear: "👟",
    clothing: "👖",
    audio: "🎧",
    appliances: "📺",
  };
  return map[category.toLowerCase()] || "🏷️";
}

function formatPrice(price: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(price);
}

function hashCode(s: string) {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = (Math.imul(31, h) + s.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let product;
  try {
    product = await fetchProduct(id);
  } catch {
    notFound();
  }

  const gradientIndex = hashCode(product.id) % GRADIENTS.length;
  const metadata = product.metadata || {};

  return (
    <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="grid gap-8 md:grid-cols-2">
        {/* Product Image Placeholder */}
        <div
          className={`flex aspect-square items-center justify-center rounded-2xl bg-gradient-to-br ${GRADIENTS[gradientIndex]}`}
        >
          <span className="text-8xl drop-shadow-lg">
            {getCategoryIcon(product.category)}
          </span>
        </div>

        {/* Product Info */}
        <div className="flex flex-col justify-center">
          <Badge variant="secondary" className="mb-3 w-fit">
            {product.category}
          </Badge>

          <h1 className="font-outfit text-3xl font-bold tracking-tight sm:text-4xl">
            {product.name}
          </h1>

          {typeof metadata.brand === "string" && (
            <p className="mt-1 text-muted-foreground">
              by {metadata.brand}
            </p>
          )}

          <p className="mt-4 font-outfit text-4xl font-bold text-primary">
            {formatPrice(product.anchor_price)}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            Listed price • Negotiable
          </p>

          <Separator className="my-6" />

          {/* Metadata attributes */}
          {Object.keys(metadata).length > 0 && (
            <div className="mb-6 space-y-2">
              {Object.entries(metadata)
                .filter(([key]) => key !== "brand")
                .map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="capitalize text-muted-foreground">
                      {key.replace(/_/g, " ")}
                    </span>
                    <span className="font-medium">{String(value)}</span>
                  </div>
                ))}
            </div>
          )}

          <ProductActions product={product} />
        </div>
      </div>
    </main>
  );
}
