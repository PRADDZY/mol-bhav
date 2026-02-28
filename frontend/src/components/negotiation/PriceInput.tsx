"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useNegotiationStore } from "@/stores/negotiation";
import { Loader2, Mic, Send, MessageSquare } from "lucide-react";
import { toast } from "sonner";
import type { ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";

export function PriceInput() {
  const [priceStr, setPriceStr] = useState("");
  const [message, setMessage] = useState("");
  const [showMessage, setShowMessage] = useState(false);

  const sendOffer = useNegotiationStore((s) => s.sendOffer);
  const isLoading = useNegotiationStore((s) => s.isLoading);
  const state = useNegotiationStore((s) => s.state);

  const isTerminal =
    state === "agreed" || state === "broken" || state === "timed_out";
  const disabled = isLoading || isTerminal;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const price = parseFloat(priceStr.replace(/,/g, ""));
    if (isNaN(price) || price <= 0) {
      toast.error("Enter a valid price");
      return;
    }

    try {
      await sendOffer(price, message.trim());
      setPriceStr("");
      setMessage("");
      setShowMessage(false);
    } catch (err) {
      const apiErr = err as ApiError;
      if (apiErr.status === 429) {
        toast.error("Thoda ruko! Too fast 😅");
      } else if (apiErr.status === 410 || apiErr.status === 404) {
        toast.error("Session expired. Start a new negotiation.");
      } else {
        toast.error(apiErr.message || "Something went wrong");
      }
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      {showMessage && (
        <Input
          placeholder="Add a message (optional)..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          disabled={disabled}
          className="text-sm"
        />
      )}

      <div className="flex items-center gap-2">
        {/* Message toggle */}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className={cn("h-10 w-10 shrink-0", showMessage && "text-primary")}
          onClick={() => setShowMessage(!showMessage)}
          disabled={disabled}
          aria-label="Toggle message field"
        >
          <MessageSquare className="h-4 w-4" />
        </Button>

        {/* Price input with ₹ prefix */}
        <div className="relative flex-1">
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
            ₹
          </span>
          <Input
            type="text"
            inputMode="decimal"
            placeholder="Your offer"
            value={priceStr}
            onChange={(e) => setPriceStr(e.target.value)}
            disabled={disabled}
            className="pl-7 text-base font-medium"
            aria-label="Enter your price offer"
          />
        </div>

        {/* Send */}
        <Button
          type="submit"
          size="icon"
          className="h-10 w-10 shrink-0"
          disabled={disabled || !priceStr}
          aria-label="Send offer"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>

        {/* Voice placeholder */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-10 w-10 shrink-0"
              disabled
              aria-label="Voice input"
            >
              <Mic className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Voice coming soon</TooltipContent>
        </Tooltip>
      </div>

      {isTerminal && (
        <p className="text-center text-xs text-muted-foreground">
          {state === "agreed"
            ? "Deal sealed! 🎉"
            : state === "broken"
              ? "Negotiation ended."
              : "Session timed out."}
        </p>
      )}
    </form>
  );
}
