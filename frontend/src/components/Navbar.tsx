"use client";

import Link from "next/link";
import { Store } from "lucide-react";
import { LanguageToggle } from "@/components/LanguageToggle";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link
          href="/"
          className="flex items-center gap-2 font-outfit text-lg font-bold tracking-tight text-primary"
        >
          <Store className="h-5 w-5" />
          Mol-Bhav
        </Link>

        <LanguageToggle />
      </div>
    </header>
  );
}
