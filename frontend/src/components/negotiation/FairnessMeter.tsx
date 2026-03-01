"use client";

import { motion } from "framer-motion";
import { useNegotiationStore } from "@/stores/negotiation";
import { cn } from "@/lib/utils";

const ZONES = [
  { label: "Too Low", color: "bg-red-500", from: 0, to: 25 },
  { label: "Getting Warmer", color: "bg-yellow-500", from: 25, to: 55 },
  { label: "Fair Deal", color: "bg-green-500", from: 55, to: 85 },
  { label: "Shop Price", color: "bg-blue-500", from: 85, to: 100 },
];

function formatPrice(price: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(price);
}

interface FairnessMeterProps {
  anchorPrice: number;
  visualFloorPercent?: number;
}

export function FairnessMeter({ anchorPrice, visualFloorPercent = 0.6 }: FairnessMeterProps) {
  const currentPrice = useNegotiationStore((s) => s.currentPrice);
  const state = useNegotiationStore((s) => s.state);

  // Visual floor (don't reveal exact reservation price)
  const visualFloor = anchorPrice * visualFloorPercent;
  const range = anchorPrice - visualFloor;

  // Clamp percentage between 0 and 100
  const percentage =
    range > 0
      ? Math.max(0, Math.min(100, ((currentPrice - visualFloor) / range) * 100))
      : 50;

  const activeZone = ZONES.find((z) => percentage >= z.from && percentage < z.to) || ZONES[0];

  if (!state) {
    return (
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <div className="h-2 flex-1 rounded-full bg-muted" />
        <span>Start negotiating to see fairness</span>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {/* Zone labels */}
      <div className="flex justify-between text-[10px] text-muted-foreground">
        <span>{formatPrice(visualFloor)}</span>
        <span className={cn("font-medium", {
          "text-red-600": activeZone.label === "Too Low",
          "text-yellow-600": activeZone.label === "Getting Warmer",
          "text-green-600": activeZone.label === "Fair Deal",
          "text-blue-600": activeZone.label === "Shop Price",
        })}>
          {activeZone.label}
        </span>
        <span>{formatPrice(anchorPrice)}</span>
      </div>

      {/* Bar */}
      <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-muted">
        {ZONES.map((zone) => (
          <div
            key={zone.label}
            className={cn("absolute top-0 h-full opacity-30", zone.color)}
            style={{
              left: `${zone.from}%`,
              width: `${zone.to - zone.from}%`,
            }}
          />
        ))}

        {/* Pointer */}
        <motion.div
          className="absolute top-0 h-full w-1 rounded-full bg-foreground shadow-md"
          animate={{ left: `${percentage}%` }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
        />
      </div>

      {/* Current counter-offer display */}
      <div className="flex justify-center">
        <motion.span
          className="text-xs font-semibold"
          key={currentPrice}
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          Current: {formatPrice(currentPrice)}
        </motion.span>
      </div>
    </div>
  );
}
