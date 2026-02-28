import { create } from "zustand";
import type {
  ChatMessage,
  Language,
  NegotiationResponse,
  NegotiationState,
} from "@/types";
import * as api from "@/lib/api";

interface NegotiationStore {
  /* session */
  sessionId: string | null;
  sessionToken: string | null;
  productId: string | null;
  productName: string;
  anchorPrice: number;
  currentPrice: number;
  agreedPrice: number | null;
  state: NegotiationState | null;
  tactic: string;
  round: number;
  maxRounds: number;

  /* chat */
  messages: ChatMessage[];
  isLoading: boolean;

  /* prefs */
  language: Language;
  flounceUsed: boolean;
  drawerOpen: boolean;

  /* actions */
  setDrawerOpen: (open: boolean) => void;
  setLanguage: (lang: Language) => void;
  startSession: (productId: string, productName: string) => Promise<void>;
  sendOffer: (price: number, message?: string) => Promise<void>;
  reset: () => void;

  /* internal */
  _applyResponse: (res: NegotiationResponse, isStart?: boolean) => void;
}

function generateId() {
  return Math.random().toString(36).slice(2, 10);
}

function getPersistedLanguage(): Language {
  if (typeof window === "undefined") return "en";
  return (localStorage.getItem("mol-bhav-lang") as Language) || "en";
}

export const useNegotiationStore = create<NegotiationStore>((set, get) => ({
  sessionId: null,
  sessionToken: null,
  productId: null,
  productName: "",
  anchorPrice: 0,
  currentPrice: 0,
  agreedPrice: null,
  state: null,
  tactic: "",
  round: 0,
  maxRounds: 15,

  messages: [],
  isLoading: false,

  language: getPersistedLanguage(),
  flounceUsed: false,
  drawerOpen: false,

  setDrawerOpen: (open) => set({ drawerOpen: open }),

  setLanguage: (lang) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("mol-bhav-lang", lang);
    }
    set({ language: lang });
  },

  startSession: async (productId, productName) => {
    set({
      isLoading: true,
      productId,
      productName,
      messages: [],
      flounceUsed: false,
      agreedPrice: null,
      state: null,
    });

    try {
      const res = await api.startNegotiation(
        productId,
        "",
        get().language,
      );
      get()._applyResponse(res, true);
    } catch (err) {
      set({ isLoading: false });
      throw err;
    }
  },

  sendOffer: async (price, message = "") => {
    const { sessionId, sessionToken, language } = get();
    if (!sessionId || !sessionToken) return;

    const buyerMsg: ChatMessage = {
      id: generateId(),
      actor: "buyer",
      text: message || `₹${price.toLocaleString("en-IN")}`,
      price,
      timestamp: new Date(),
      status: "sending",
    };

    set((s) => ({
      messages: [...s.messages, buyerMsg],
      isLoading: true,
    }));

    try {
      const res = await api.sendOffer(
        sessionId,
        sessionToken,
        price,
        message,
        language,
      );

      set((s) => ({
        messages: s.messages.map((m) =>
          m.id === buyerMsg.id ? { ...m, status: "sent" as const } : m,
        ),
      }));

      get()._applyResponse(res);
    } catch (err) {
      set((s) => ({
        isLoading: false,
        messages: s.messages.map((m) =>
          m.id === buyerMsg.id ? { ...m, status: "error" as const } : m,
        ),
      }));
      throw err;
    }
  },

  reset: () =>
    set({
      sessionId: null,
      sessionToken: null,
      productId: null,
      productName: "",
      anchorPrice: 0,
      currentPrice: 0,
      agreedPrice: null,
      state: null,
      tactic: "",
      round: 0,
      maxRounds: 15,
      messages: [],
      isLoading: false,
      flounceUsed: false,
      drawerOpen: false,
    }),

  _applyResponse: (res, isStart = false) => {
    const sellerMsg: ChatMessage = {
      id: generateId(),
      actor: "seller",
      text: res.message,
      price: res.current_price,
      tactic: res.tactic,
      metadata: res.metadata,
      timestamp: new Date(),
      status: "sent",
    };

    set((s) => ({
      sessionId: res.session_id,
      sessionToken: isStart ? res.session_token : s.sessionToken,
      anchorPrice: res.anchor_price || s.anchorPrice,
      currentPrice: res.current_price,
      agreedPrice: res.agreed_price,
      state: res.state,
      tactic: res.tactic,
      round: res.round,
      maxRounds: res.max_rounds,
      messages: [...s.messages, sellerMsg],
      isLoading: false,
    }));
  },
}));
