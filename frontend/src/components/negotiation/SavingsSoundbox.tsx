"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import confetti from "canvas-confetti";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useNegotiationStore } from "@/stores/negotiation";
import { toast } from "sonner";
import { X } from "lucide-react";

function formatPrice(price: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(price);
}

interface SavingsSoundboxProps {
  anchorPrice: number;
}

export function SavingsSoundbox({ anchorPrice }: SavingsSoundboxProps) {
  const state = useNegotiationStore((s) => s.state);
  const agreedPrice = useNegotiationStore((s) => s.agreedPrice);
  const [show, setShow] = useState(false);
  const [firedRef, setFiredRef] = useState(false);

  const isDeal = state === "agreed" && agreedPrice !== null;
  const saved = isDeal ? anchorPrice - agreedPrice : 0;

  useEffect(() => {
    if (isDeal && !firedRef) {
      setShow(true);
      setFiredRef(true);

      // Confetti
      confetti({
        particleCount: 120,
        spread: 80,
        origin: { y: 0.6 },
        colors: ["#FF6B35", "#FFB400", "#004E89"],
      });

      // Sound
      try {
        const audio = new Audio("/sounds/ding.mp3");
        audio.volume = 0.5;
        audio.play().catch(() => {});
      } catch {
        // no-op if audio unavailable
      }

      toast.success("Deal sealed! 🎉");
    }
  }, [isDeal, firedRef]);

  // Reset when session changes
  useEffect(() => {
    if (!isDeal) {
      setFiredRef(false);
      setShow(false);
    }
  }, [isDeal]);

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setShow(false)}
        >
          <motion.div
            className="relative mx-4 w-full max-w-sm rounded-2xl bg-card p-6 text-center shadow-2xl"
            initial={{ scale: 0.8, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.8, y: 20 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            onClick={(e) => e.stopPropagation()}
          >
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-2 top-2"
              onClick={() => setShow(false)}
              aria-label="Close celebration"
            >
              <X className="h-4 w-4" />
            </Button>

            <motion.div
              className="mb-3 text-5xl"
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              🎉
            </motion.div>

            <h2 className="font-outfit text-2xl font-bold">Deal Done!</h2>

            <p className="mt-2 text-lg text-muted-foreground">
              You saved{" "}
              <span className="font-bold text-green-600">
                {formatPrice(saved)}
              </span>
            </p>

            <div className="mt-2 text-sm text-muted-foreground">
              <span className="line-through">{formatPrice(anchorPrice)}</span>
              {" → "}
              <span className="font-semibold text-primary">
                {formatPrice(agreedPrice!)}
              </span>
            </div>

            <div className="mt-4 flex justify-center gap-2">
              <Badge variant="outline" className="text-xs">
                ONDC-Verified ✓
              </Badge>
              <Badge variant="outline" className="text-xs">
                DPDP Secure 🔒
              </Badge>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
