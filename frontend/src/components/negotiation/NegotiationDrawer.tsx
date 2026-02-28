"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useNegotiationStore } from "@/stores/negotiation";
import { ChatThread } from "./ChatThread";
import { PriceInput } from "./PriceInput";
import { BazaarBotAvatar } from "./BazaarBotAvatar";
import { FairnessMeter } from "./FairnessMeter";
import { DigitalFlounce } from "./DigitalFlounce";
import { SavingsSoundbox } from "./SavingsSoundbox";
import { useState } from "react";

interface NegotiationDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  productName: string;
  anchorPrice: number;
}

export function NegotiationDrawer({
  open,
  onOpenChange,
  productName,
  anchorPrice,
}: NegotiationDrawerProps) {
  const state = useNegotiationStore((s) => s.state);
  const flounceUsed = useNegotiationStore((s) => s.flounceUsed);
  const reset = useNegotiationStore((s) => s.reset);
  const [showFlounce, setShowFlounce] = useState(false);

  const isActive = state && state !== "agreed" && state !== "broken" && state !== "timed_out";

  function handleOpenChange(nextOpen: boolean) {
    // Intercept close if session is active and flounce not yet used
    if (!nextOpen && isActive && !flounceUsed) {
      setShowFlounce(true);
      return;
    }

    onOpenChange(nextOpen);
    if (!nextOpen) {
      reset();
    }
  }

  function handleFlounceClose() {
    setShowFlounce(false);
  }

  function handleFlouceLeave() {
    setShowFlounce(false);
    onOpenChange(false);
    reset();
  }

  return (
    <>
      <Sheet open={open} onOpenChange={handleOpenChange}>
        <SheetContent
          side="bottom"
          className="flex h-[85vh] max-h-[85vh] flex-col rounded-t-2xl p-0 md:mx-auto md:max-w-md"
        >
          {/* Header */}
          <SheetHeader className="flex-shrink-0 border-b px-4 py-3">
            <div className="flex items-center gap-3">
              <BazaarBotAvatar size="sm" />
              <div className="min-w-0 flex-1">
                <SheetTitle className="font-outfit text-base leading-tight truncate">
                  {productName}
                </SheetTitle>
                <p className="text-xs text-muted-foreground">
                  Negotiate with Bazaar Bot
                </p>
              </div>
            </div>
          </SheetHeader>

          {/* FairnessMeter */}
          <div className="flex-shrink-0 border-b px-4 py-2">
            <FairnessMeter anchorPrice={anchorPrice} />
          </div>

          {/* Chat Area */}
          <ScrollArea className="flex-1 overflow-hidden">
            <div className="px-4 py-3">
              <ChatThread />
            </div>
          </ScrollArea>

          {/* Input */}
          <div className="flex-shrink-0 border-t px-4 py-3">
            <PriceInput />
          </div>
        </SheetContent>
      </Sheet>

      {/* Digital Flounce Dialog */}
      <DigitalFlounce
        open={showFlounce}
        onClose={handleFlounceClose}
        onLeave={handleFlouceLeave}
      />

      {/* Celebration overlay */}
      <SavingsSoundbox anchorPrice={anchorPrice} />
    </>
  );
}
