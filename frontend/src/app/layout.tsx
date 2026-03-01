import type { Metadata } from "next";
import { Outfit, DM_Sans } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Navbar } from "@/components/Navbar";
import "./globals.css";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
  display: "swap",
});

const dmSans = DM_Sans({
  variable: "--font-dm-sans",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Mol-Bhav | AI Bazaar Negotiation",
  description:
    "Haggle like a pro — AI-powered Indian bazaar-style price negotiation for e-commerce",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${outfit.variable} ${dmSans.variable} antialiased`}>
        <TooltipProvider delayDuration={300}>
          <Navbar />
          {children}
        </TooltipProvider>
        <Toaster richColors position="top-center" />
      </body>
    </html>
  );
}
