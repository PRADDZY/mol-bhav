# Mol-Bhav — AI Negotiation Engine

Indian Bazaar-style haggling engine for e-commerce. Combines a deterministic SAO (Stacked Alternating Offers) strategy engine with GPT-4o-powered Hinglish dialogue to simulate real shopkeeper negotiation.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI Server                     │
│  /api/v1/negotiate    /api/v1/products    /beckn     │
└──────────────┬──────────────┬──────────────┬─────────┘
               │              │              │
       ┌───────▼───────┐  ┌──▼──┐  ┌────────▼────────┐
       │  Negotiation   │  │CRUD │  │  Beckn Protocol  │
       │   Service      │  │     │  │     Stubs        │
       └───┬───┬───┬────┘  └─────┘  └─────────────────┘
           │   │   │
    ┌──────▼┐ ┌▼────────┐ ┌▼──────────┐
    │Engine │ │Dialogue  │ │ Bot       │
    │(Brain)│ │(Mouth)   │ │ Detector  │
    ├───────┤ ├──────────┤ └───────────┘
    │Concess│ │GPT-4o    │
    │Recipro│ │Hinglish  │
    │Validat│ │Persona   │
    └───────┘ └──────────┘
```

**Three layers:**
- **Strategy Engine** — Concession curves, TFT reciprocity, price validation
- **Dialogue Engine** — GPT-4o Hinglish "Bhaiya/Didi" persona
- **Protocol Layer** — Beckn/ONDC-compatible quote objects with TTL

## Quick Start

```bash
# 1. Start MongoDB + Redis
docker compose up -d mongodb redis

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Configure
cp .env.example .env
# Edit .env with your OpenAI API key and DB credentials

# 4. Seed demo data
python -m scripts.seed

# 5. Run
uvicorn app.main:app --reload

# 6. Test
pytest tests/ -v
```

### Docker (Full Stack)

```bash
cp .env.example .env   # configure secrets
docker compose up --build
# App at http://localhost:8000, health at /health
```

## API

### Start Negotiation
```bash
POST /api/v1/negotiate/start
{"product_id": "phone-001", "buyer_name": "Rahul"}
```

### Make Offer
```bash
POST /api/v1/negotiate/{session_id}/offer
{"message": "Bhaiya thoda kam karo", "price": 800}
```

### Check Status
```bash
GET /api/v1/negotiate/{session_id}/status
```

### Add Product
```bash
POST /api/v1/products
{
  "id": "phone-001",
  "name": "Samsung Galaxy M15",
  "category": "electronics",
  "anchor_price": 12999,
  "cost_price": 9000,
  "min_margin": 0.05,
  "target_margin": 0.30
}
```

## Negotiation Strategy

The engine uses a **time-dependent concession curve**:

$$P(t) = P_a + (R_s - P_a) \cdot \left(\frac{t}{T}\right)^\beta$$

- $\beta > 1$ → **Boulware** (hardliner, holds firm until deadline)
- $\beta = 1$ → **Linear**
- $\beta < 1$ → **Conceder** (gives in early)

Combined with **Tit-for-Tat reciprocity**: mirrors buyer concessions at a damped rate ($\alpha \cdot \Delta_{buyer}$, default $\alpha = 0.6$).

## Features

- **F-01** Dynamic floor price from `{cost_price, min_margin, target_margin}`
- **F-02** Walk-away detection + "Digital Flounce" save-the-deal (5% concession)
- **F-03** Invisible coupons — applies promos without showing codes
- **F-04** Quantity bargaining pivot when price negotiation stalls
- **Bot Defense** — Composite scoring (timing + pattern analysis) with 2s cooldown
- **Hallucination Guardrail** — Deterministic validator overrides LLM if price < floor

## Stack

- Python 3.11+ / FastAPI
- MongoDB (Motor async) — durable session history
- Redis (aioredis) — active session TTL management
- OpenAI GPT-4o — Hinglish dialogue generation
- Beckn/ONDC protocol stubs (ready for gateway integration)

### Frontend

- Next.js 16 (App Router) / React 19 / TypeScript
- shadcn/ui — Sheet, Dialog, Card, Button, Input, Skeleton, Badge, etc.
- Framer Motion — avatar animations, chat transitions, meter physics
- Zustand — client-side negotiation state
- Tailwind CSS v4 — Indian bazaar palette (saffron/gold/deep-blue)

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

Create `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The frontend proxies `/api/v1/*` calls to the backend via Next.js rewrites.

### Frontend Features

| Feature | Description |
|---------|-------------|
| **Product Listing** | Animated card grid with category icons, staggered Framer Motion fade-in |
| **Product Detail** | Full metadata display, "Negotiate Price" button opens drawer |
| **NegotiationDrawer** | Bottom Sheet with chat, fairness meter, price input |
| **ChatThread** | WhatsApp-style bubbles, optimistic sends, typing indicator |
| **BazaarBotAvatar** | Animated states: idle, thinking, flinch, deal celebration |
| **FairnessMeter** | 4-zone colored bar with spring-animated pointer |
| **RationaleChips** | Explainable AI badges showing negotiation tactic |
| **Digital Flounce** | AlertDialog intercept: "Ruko Bhaiya!" walk-away save-the-deal |
| **Bohni Mode** | Golden "Pehli Bohni!" badge for morning negotiations |
| **Savings Soundbox** | Confetti + celebration overlay with ONDC/DPDP badges |
| **Language Toggle** | English, हिन्दी, தமிழ், తెలుగు, मराठी |

## Security

| Layer | Protection |
|-------|-----------|
| **Admin routes** | `X-API-Key` header validated against `API_ADMIN_KEY` env var |
| **Buyer routes** | `X-Session-Token` header (returned on `/start`, required on `/offer` and `/status`) |
| **Rate limiting** | Per-IP limit on `/start` (default 30/min), per-session cooldown on `/offer` (2s) |
| **Input validation** | Session ID format (`^[a-f0-9]{32}$`), product ID format (`^[a-zA-Z0-9_-]{1,100}$`) |
| **Body size** | 64 KB max request body |
| **Prompt injection** | Buyer messages sanitized — control chars stripped, injection patterns redacted |
| **CORS** | Restricted origins, methods, and headers |
| **Swagger** | `/docs` and `/redoc` auto-disabled when `ENV=production` |
| **Database auth** | MongoDB + Redis credentials configured via env vars |
| **Distributed locks** | Redis-based per-session lock prevents concurrent offer processing |
| **Structured logging** | JSON-formatted logs with `X-Request-ID` tracing |
