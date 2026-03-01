"use client";

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNegotiationStore } from "@/stores/negotiation";
import { Badge } from "@/components/ui/badge";
import { RationaleChips } from "./RationaleChips";
import { cn } from "@/lib/utils";

function formatTime(date: Date) {
  return new Date(date).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
}

function formatPrice(price: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(price);
}

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2">
      <div className="flex gap-1 rounded-2xl rounded-bl-md bg-primary/10 px-4 py-3">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="block h-2 w-2 rounded-full bg-primary/60"
            animate={{ y: [0, -6, 0] }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              delay: i * 0.15,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>
    </div>
  );
}

function isMorning() {
  return new Date().getHours() < 11;
}

export function ChatThread() {
  const messages = useNegotiationStore((s) => s.messages);
  const isLoading = useNegotiationStore((s) => s.isLoading);
  const round = useNegotiationStore((s) => s.round);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isLoading]);

  return (
    <div className="space-y-3">
      <AnimatePresence initial={false}>
        {messages.map((msg, idx) => {
          const isBuyer = msg.actor === "buyer";
          const isFirstSeller = !isBuyer && idx === 0;
          const showBohni = isFirstSeller && isMorning();

          return (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 12, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
              className={cn(
                "flex",
                isBuyer ? "justify-end" : "justify-start",
              )}
            >
              <div
                className={cn(
                  "relative max-w-[80%] rounded-2xl px-4 py-2.5",
                  isBuyer
                    ? "rounded-br-md bg-secondary text-secondary-foreground"
                    : "rounded-bl-md bg-primary/10 text-foreground",
                  showBohni && "ring-2 ring-accent/60",
                )}
              >
                {showBohni && (
                  <motion.div
                    className="mb-1"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.3 }}
                  >
                    <Badge
                      variant="outline"
                      className="border-accent bg-accent/10 text-accent-foreground text-xs"
                    >
                      ☀️ Pehli Bohni!
                    </Badge>
                  </motion.div>
                )}

                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                  {msg.text}
                </p>

                <div className="mt-1 flex items-center justify-between gap-2">
                  {msg.price > 0 && (
                    <Badge
                      variant={isBuyer ? "secondary" : "default"}
                      className="text-xs font-semibold"
                    >
                      {formatPrice(msg.price)}
                    </Badge>
                  )}
                  <span className="text-[10px] text-muted-foreground">
                    {msg.status === "sending" ? "sending..." : formatTime(msg.timestamp)}
                  </span>
                </div>

                {/* Rationale chips for seller messages */}
                {!isBuyer && msg.tactic && (
                  <RationaleChips
                    tactic={msg.tactic}
                    round={round}
                    metadata={msg.metadata}
                  />
                )}
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>

      {isLoading && <TypingIndicator />}

      <div ref={bottomRef} />
    </div>
  );
}
