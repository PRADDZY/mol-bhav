"use client";

import { motion } from "framer-motion";
import type { Product } from "@/types";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ShoppingBag } from "lucide-react";
import { GRADIENTS } from "@/lib/constants";

function formatPrice(price: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(price);
}

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

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const item = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" as const } },
};

export function ProductGrid({ products }: { products: Product[] }) {
  return (
    <motion.div
      className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {products.map((product, i) => (
        <motion.div key={product.id} variants={item}>
          <Link href={`/products/${product.id}`} className="block h-full">
            <Card className="group h-full cursor-pointer transition-shadow hover:shadow-lg hover:shadow-primary/10">
              {/* Gradient placeholder for product image */}
              <div
                className={`relative h-44 rounded-t-xl bg-linear-to-br ${GRADIENTS[i % GRADIENTS.length]} flex items-center justify-center`}
              >
                <span className="text-5xl drop-shadow-md">
                  {getCategoryIcon(product.category)}
                </span>
                <Badge
                  variant="secondary"
                  className="absolute right-3 top-3 text-xs"
                >
                  {product.category}
                </Badge>
              </div>

              <CardHeader className="pb-2">
                <CardTitle className="font-outfit text-lg leading-snug group-hover:text-primary transition-colors">
                  {product.name}
                </CardTitle>
              </CardHeader>

              <CardContent className="pb-2">
                <p className="font-outfit text-2xl font-bold text-primary">
                  {formatPrice(product.anchor_price)}
                </p>
                {typeof product.metadata?.brand === "string" && (
                  <p className="mt-1 text-sm text-muted-foreground">
                    {product.metadata.brand}
                  </p>
                )}
              </CardContent>

              <CardFooter>
                <Button
                  variant="default"
                  className="w-full gap-2"
                  size="sm"
                  asChild
                >
                  <span>
                    <ShoppingBag className="h-4 w-4" />
                    View & Negotiate
                  </span>
                </Button>
              </CardFooter>
            </Card>
          </Link>
        </motion.div>
      ))}
    </motion.div>
  );
}
