import type { NegotiationResponse, Product } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    const err = new Error(body.detail || `API error ${res.status}`);
    (err as ApiError).status = res.status;
    throw err;
  }

  return res.json();
}

export interface ApiError extends Error {
  status: number;
}

export async function fetchProducts(): Promise<Product[]> {
  return apiFetch<Product[]>("/api/v1/products");
}

export async function fetchProduct(id: string): Promise<Product> {
  return apiFetch<Product>(`/api/v1/products/${encodeURIComponent(id)}`);
}

export async function startNegotiation(
  productId: string,
  buyerName: string = "",
  language: string = "en",
): Promise<NegotiationResponse> {
  return apiFetch<NegotiationResponse>("/api/v1/negotiate/start", {
    method: "POST",
    body: JSON.stringify({
      product_id: productId,
      buyer_name: buyerName,
      language,
    }),
  });
}

export async function sendOffer(
  sessionId: string,
  sessionToken: string,
  price: number,
  message: string = "",
  language: string = "en",
): Promise<NegotiationResponse> {
  return apiFetch<NegotiationResponse>(
    `/api/v1/negotiate/${encodeURIComponent(sessionId)}/offer`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Session-Token": sessionToken,
      },
      body: JSON.stringify({ price, message, language }),
    },
  );
}

export async function getStatus(
  sessionId: string,
  sessionToken: string,
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(
    `/api/v1/negotiate/${encodeURIComponent(sessionId)}/status`,
    {
      headers: {
        "X-Session-Token": sessionToken,
      },
    },
  );
}
