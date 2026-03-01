"use client";

import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";

function getChipText(
  tactic: string,
  round: number,
  metadata?: Record<string, unknown>,
): { label: string; emoji: string } {
  const tacticLower = tactic.toLowerCase();

  if (metadata?.coupon_applied) {
    return { label: "Special discount applied! Sirf aapke liye", emoji: "🎁" };
  }
  if (tacticLower.includes("quantity") || tacticLower.includes("pivot")) {
    const qty = metadata?.quantity || 2;
    return { label: `Buy ${qty}, save more!`, emoji: "📦" };
  }
  if (tacticLower.includes("walk_away") || tacticLower.includes("save")) {
    return { label: "Final offer just for you!", emoji: "💯" };
  }
  if (tacticLower.includes("concession")) {
    return { label: "Price adjusted — competitive analysis", emoji: "📊" };
  }
  if (tacticLower.includes("anchor")) {
    return { label: "Premium quality product", emoji: "⭐" };
  }
  if (tacticLower.includes("recipro")) {
    return { label: "Matching your bargaining spirit", emoji: "🤝" };
  }
  if (tacticLower.includes("deadline") || tacticLower.includes("time")) {
    return { label: "Limited time offer", emoji: "⏰" };
  }
  return { label: `Round ${round} consideration`, emoji: "💬" };
}

interface RationaleChipsProps {
  tactic: string;
  round: number;
  metadata?: Record<string, unknown>;
}

export function RationaleChips({ tactic, round, metadata }: RationaleChipsProps) {
  const { label, emoji } = getChipText(tactic, round, metadata);

  return (
    <motion.div
      className="mt-1.5"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2, duration: 0.3 }}
    >
      <Badge variant="secondary" className="text-[11px] font-normal gap-1">
        <span>{emoji}</span>
        {label}
      </Badge>
    </motion.div>
  );
}
