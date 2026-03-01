"use client";

import { motion, type TargetAndTransition } from "framer-motion";
import { useNegotiationStore } from "@/stores/negotiation";
import { cn } from "@/lib/utils";

type AvatarState = "idle" | "thinking" | "flinch" | "deal";

function deriveAvatarState(
  isLoading: boolean,
  state: string | null,
  tactic: string,
  currentPrice: number,
  anchorPrice: number,
): AvatarState {
  if (state === "agreed") return "deal";
  if (isLoading) return "thinking";
  if (currentPrice > 0 && anchorPrice > 0 && currentPrice < anchorPrice * 0.3) return "flinch";
  return "idle";
}

const stateAnimations: Record<AvatarState, TargetAndTransition> = {
  idle: {
    scale: [1, 1.03, 1],
    transition: { repeat: Infinity, duration: 3, ease: "easeInOut" },
  },
  thinking: {
    scale: [1, 1.05, 1],
    opacity: [1, 0.7, 1],
    transition: { repeat: Infinity, duration: 1.2, ease: "easeInOut" },
  },
  flinch: {
    x: [-5, 5, -3, 3, 0],
    scale: 1.1,
    transition: { duration: 0.4, ease: "easeOut" },
  },
  deal: {
    scale: [1, 1.2, 1],
    rotate: [0, 5, -5, 0],
    transition: { duration: 0.6, ease: "easeOut" },
  },
};

const stateEmoji: Record<AvatarState, string> = {
  idle: "🧔",
  thinking: "🤔",
  flinch: "😲",
  deal: "🤝",
};

interface BazaarBotAvatarProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function BazaarBotAvatar({ size = "md", className }: BazaarBotAvatarProps) {
  const isLoading = useNegotiationStore((s) => s.isLoading);
  const state = useNegotiationStore((s) => s.state);
  const tactic = useNegotiationStore((s) => s.tactic);
  const currentPrice = useNegotiationStore((s) => s.currentPrice);
  const anchorPrice = useNegotiationStore((s) => s.anchorPrice);

  const avatarState = deriveAvatarState(isLoading, state, tactic, currentPrice, anchorPrice);

  const sizeClasses = {
    sm: "h-9 w-9 text-lg",
    md: "h-12 w-12 text-2xl",
    lg: "h-16 w-16 text-3xl",
  };

  return (
    <div className={cn("relative", className)}>
      <motion.div
        className={cn(
          "flex items-center justify-center rounded-full bg-primary/10 ring-2 ring-primary/20",
          sizeClasses[size],
        )}
        animate={stateAnimations[avatarState]}
        key={avatarState}
      >
        {stateEmoji[avatarState]}
      </motion.div>

      {/* Thinking ring */}
      {avatarState === "thinking" && (
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-primary/40"
          animate={{ scale: [1, 1.5], opacity: [0.6, 0] }}
          transition={{ repeat: Infinity, duration: 1, ease: "easeOut" }}
        />
      )}
    </div>
  );
}
