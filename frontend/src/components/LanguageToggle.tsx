"use client";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Globe } from "lucide-react";
import { useNegotiationStore } from "@/stores/negotiation";
import { LANGUAGE_LABELS, type Language } from "@/types";

export function LanguageToggle() {
  const language = useNegotiationStore((s) => s.language);
  const setLanguage = useNegotiationStore((s) => s.setLanguage);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-2">
          <Globe className="h-4 w-4" />
          <span className="hidden sm:inline">
            {LANGUAGE_LABELS[language]}
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuRadioGroup
          value={language}
          onValueChange={(v) => setLanguage(v as Language)}
        >
          {Object.entries(LANGUAGE_LABELS).map(([code, label]) => (
            <DropdownMenuRadioItem key={code} value={code}>
              {label}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
