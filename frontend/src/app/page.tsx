import { fetchProducts } from "@/lib/api";
import { ProductGrid } from "@/components/ProductGrid";
import { Store } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const products = await fetchProducts();

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Hero */}
      <section className="mb-10 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
          <Store className="h-8 w-8 text-primary" />
        </div>
        <h1 className="font-outfit text-4xl font-bold tracking-tight sm:text-5xl">
          The Bazaar
        </h1>
        <p className="mx-auto mt-3 max-w-lg text-lg text-muted-foreground">
          Browse products and haggle with our AI shopkeeper.
          Every price is negotiable — just like in a real Indian market.
        </p>
      </section>

      {/* Product Grid */}
      {products.length === 0 ? (
        <div className="py-20 text-center">
          <p className="text-lg text-muted-foreground">
            No products available yet. Seed the database and refresh.
          </p>
        </div>
      ) : (
        <ProductGrid products={products} />
      )}
    </main>
  );
}
