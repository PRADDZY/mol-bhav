"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useNegotiationStore } from "@/stores/negotiation";
import { toast } from "sonner";
import type { ApiError } from "@/lib/api";

function formatPrice(price: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(price);
}

interface DigitalFlounceProps {
  open: boolean;
  onClose: () => void;
  onLeave: () => void;
}

export function DigitalFlounce({ open, onClose, onLeave }: DigitalFlounceProps) {
  const currentPrice = useNegotiationStore((s) => s.currentPrice);
  const sendOffer = useNegotiationStore((s) => s.sendOffer);

  // Offer a slightly better deal as walk-away price (5% below current counter)
  const walkAwayPrice = Math.round(currentPrice * 0.95);

  async function handleAcceptDeal() {
    try {
      await sendOffer(walkAwayPrice, "Walk-away deal accepted");
      onClose();
      // Mark flounce as used
      useNegotiationStore.setState({ flounceUsed: true });
    } catch (err) {
      const apiErr = err as ApiError;
      toast.error(apiErr.message || "Failed to accept deal");
      onClose();
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={(o) => !o && onClose()}>
      <AnimatePresence>
        {open && (
          <AlertDialogContent asChild>
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
            >
              <AlertDialogHeader>
                <AlertDialogTitle className="font-outfit text-xl">
                  Ruko Bhaiya! 🙏
                </AlertDialogTitle>
                <AlertDialogDescription className="text-base">
                  Ek final deal hai — {formatPrice(walkAwayPrice)}.{" "}
                  Pakka deal?
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel onClick={onLeave}>
                  No, I&apos;m leaving
                </AlertDialogCancel>
                <AlertDialogAction onClick={handleAcceptDeal}>
                  Accept Deal! 🤝
                </AlertDialogAction>
              </AlertDialogFooter>
            </motion.div>
          </AlertDialogContent>
        )}
      </AnimatePresence>
    </AlertDialog>
  );
}
