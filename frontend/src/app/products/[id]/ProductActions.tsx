"use client";

import { Button } from "@/components/ui/button";
import { NegotiationDrawer } from "@/components/negotiation/NegotiationDrawer";
import { useNegotiationStore } from "@/stores/negotiation";
import type { Product } from "@/types";
import { MessageCircle, ShoppingCart } from "lucide-react";

export function ProductActions({ product }: { product: Product }) {
  const setDrawerOpen = useNegotiationStore((s) => s.setDrawerOpen);
  const startSession = useNegotiationStore((s) => s.startSession);
  const drawerOpen = useNegotiationStore((s) => s.drawerOpen);

  async function handleNegotiate() {
    setDrawerOpen(true);
    await startSession(product.id, product.name);
  }

  return (
    <>
      <div className="flex flex-col gap-3 sm:flex-row">
        <Button
          size="lg"
          className="flex-1 gap-2 text-base"
          onClick={handleNegotiate}
        >
          <MessageCircle className="h-5 w-5" />
          Negotiate Price
        </Button>
        <Button
          size="lg"
          variant="outline"
          className="flex-1 gap-2 text-base"
          disabled
        >
          <ShoppingCart className="h-5 w-5" />
          Add to Cart
        </Button>
      </div>

      <NegotiationDrawer
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        productName={product.name}
        anchorPrice={product.anchor_price}
      />
    </>
  );
}
