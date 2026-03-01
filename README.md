# Mol-Bhav — AI Negotiation Engine

Indian Bazaar-style haggling engine for e-commerce. Combines a deterministic SAO (Stacked Alternating Offers) strategy engine with NVIDIA NIM-powered Hinglish dialogue (GLM-4.7 via Chain-of-Thought reasoning) to simulate real shopkeeper negotiation.

**Live Demo:** [github.com/PRADDZY/mol-bhav](https://github.com/PRADDZY/mol-bhav)

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
    │Concess│ │NIM/GLM   │
    │Recipro│ │Hinglish  │
    │Validat│ │CoT+JSON  │
    └───────┘ └──────────┘
```

**Three layers:**
- **Strategy Engine** — Concession curves, TFT reciprocity, price validation
- **Dialogue Engine** — NVIDIA NIM (GLM-4.7) Hinglish "Bhaiya/Didi" persona with Chain-of-Thought reasoning
- **Protocol Layer** — Beckn/ONDC-compatible quote objects with TTL

## Project Structure

```
app/
├── api/                  # FastAPI route handlers
│   ├── negotiate.py      # /start, /offer, /status endpoints
│   ├── products.py       # CRUD product management
│   ├── sessions.py       # Session history (paginated)
│   ├── beckn.py          # Beckn /select protocol endpoint
│   └── deps.py           # Shared dependency injection
├── engine/               # Deterministic negotiation brain
│   ├── state_machine.py  # SAO state transitions + input validation
│   ├── concession.py     # Time-dependent concession curves
│   ├── reciprocity.py    # TFT reciprocity tracker + adaptive alpha
│   ├── bot_detector.py   # Composite bot scoring (timing + pattern)
│   └── validator.py      # Hallucination guardrail — price clamping
├── dialogue/             # LLM-powered Hinglish dialogue
│   ├── generator.py      # NIM API integration + CoT parsing
│   ├── sentiment.py      # Exit intent & anger detection
│   └── prompts/          # System + tactic-specific prompts
├── models/               # Pydantic data models
│   ├── session.py        # NegotiationSession (with bot_score constraints)
│   ├── product.py        # Product (with cross-field validation)
│   ├── offer.py          # Offer history
│   └── beckn.py          # Beckn/ONDC protocol models
├── protocol/             # ONDC protocol layer
│   ├── beckn_stub.py     # on_select response builder
│   ├── quote_builder.py  # Quote generation with TTL
│   └── digital_signature.py  # Stub (runtime warning)
├── services/             # Business logic orchestration
│   ├── negotiation_service.py  # Session lifecycle & coordination
│   └── coupon_service.py       # Invisible coupon application
├── db/                   # Database connections
│   ├── mongo.py          # Motor async MongoDB client
│   └── redis.py          # Redis sessions, locks, cooldowns
├── auth.py               # API key + session token verification
├── config.py             # Pydantic Settings (env-driven)
├── main.py               # FastAPI app + lifespan + middleware
├── middleware.py          # X-Request-ID tracing
└── logging_config.py     # JSON structured logging

frontend/
├── src/
│   ├── app/              # Next.js App Router pages
│   ├── components/       # UI components (shadcn/ui + custom)
│   │   └── negotiation/  # Chat, Avatar, FairnessMeter, etc.
│   ├── stores/           # Zustand state management
│   ├── lib/              # API helpers, utils, shared constants
│   └── types/            # TypeScript interfaces
tests/                    # 132 tests — backend only
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Docker & Docker Compose (optional, for DB/full-stack)
- NVIDIA NIM API key (free at [build.nvidia.com](https://build.nvidia.com/))

### Option 1: Docker Compose (Recommended)

```bash
# Clone
git clone https://github.com/PRADDZY/mol-bhav.git
cd mol-bhav

# Configure
cp .env.example .env
# Edit .env — set NIM_API_KEY=nvapi-... (get from build.nvidia.com)

# Launch everything
docker compose up --build

# App at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### Option 2: Local Development

```bash
# 1. Start MongoDB + Redis (via Docker or local install)
docker compose up -d mongodb redis

# 2. Install Python dependencies
pip install -e ".[dev]"

# 3. Configure
cp .env.example .env
# Edit .env with your NIM_API_KEY and DB credentials

# 4. Seed demo products
python -m scripts.seed

# 5. Run backend
uvicorn app.main:app --reload
# Backend at http://localhost:8000

# 6. Run frontend (in a separate terminal)
cd frontend
npm install
cp .env.example .env.local   # or create manually:
# NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
# Frontend at http://localhost:3000

# 7. Run tests
pytest tests/ -v
```

## API Reference

### Start Negotiation
```bash
POST /api/v1/negotiate/start
Content-Type: application/json

{"product_id": "phone-001", "buyer_name": "Rahul", "language": "en"}
```
**Response:** Returns `session_id`, `session_token`, opening message, anchor price.

### Make Offer
```bash
POST /api/v1/negotiate/{session_id}/offer
Content-Type: application/json
X-Session-Token: {session_token}

{"message": "Bhaiya thoda kam karo", "price": 800, "language": "hi"}
```
**Response:** Counter-offer with message, current price, state, tactic, sentiment.

### Check Status
```bash
GET /api/v1/negotiate/{session_id}/status
X-Session-Token: {session_token}
```

### Product CRUD
```bash
# List all
GET /api/v1/products

# Get one
GET /api/v1/products/{id}

# Create (admin)
POST /api/v1/products
X-API-Key: {admin_key}
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

### Beckn/ONDC Protocol
```bash
POST /beckn/select
# Accepts Beckn select messages, maps to internal negotiation
```

## Negotiation Strategy

The engine uses a **time-dependent concession curve**:

$$P(t) = P_a + (R_s - P_a) \cdot \left(\frac{t}{T}\right)^\beta$$

- $\beta > 1$ → **Boulware** (hardliner, holds firm until deadline)
- $\beta = 1$ → **Linear**
- $\beta < 1$ → **Conceder** (gives in early)

Combined with **Tit-for-Tat reciprocity**: mirrors buyer concessions at a damped rate ($\alpha \cdot \Delta_{buyer}$, default $\alpha = 0.6$), with adaptive alpha that increases near deadline.

## Features

- **F-01** Dynamic floor price from `{cost_price, min_margin, target_margin}`
- **F-02** Walk-away detection + "Digital Flounce" save-the-deal (5% concession)
- **F-03** Invisible coupons — applies promos without showing codes
- **F-04** Quantity bargaining pivot when price negotiation stalls
- **Bot Defense** — Composite scoring (timing + pattern analysis) with 2s cooldown
- **Hallucination Guardrail** — Deterministic validator overrides LLM if price < floor

## Stack

### Backend
- **Python 3.11+** / **FastAPI** — async-first API server
- **MongoDB** (Motor async) — durable session history + product catalog
- **Redis** (aioredis) — active session TTL, distributed locks, rate limiting, cooldowns
- **NVIDIA NIM** (GLM-4.7, configurable) — Hinglish dialogue generation with CoT reasoning
- **Beckn/ONDC** protocol stubs (ready for gateway integration)

### Frontend
- **Next.js 16** (App Router) / **React 19** / **TypeScript**
- **shadcn/ui** — Sheet, Dialog, Card, Button, Input, Skeleton, Badge, etc.
- **Framer Motion** — avatar animations, chat transitions, meter physics
- **Zustand** — client-side negotiation state
- **Tailwind CSS v4** — Indian bazaar palette (saffron/gold/deep-blue)

### Frontend Features

| Feature | Description |
|---------|-------------|
| **Product Listing** | Animated card grid with category icons, staggered Framer Motion fade-in |
| **Product Detail** | Full metadata display, "Negotiate Price" button opens drawer |
| **NegotiationDrawer** | Bottom Sheet with chat, fairness meter, price input |
| **ChatThread** | WhatsApp-style bubbles, optimistic sends, typing indicator |
| **BazaarBotAvatar** | Animated states: idle, thinking, flinch, deal celebration |
| **FairnessMeter** | 4-zone colored bar with spring-animated pointer (configurable floor) |
| **RationaleChips** | Explainable AI badges showing negotiation tactic |
| **Digital Flounce** | AlertDialog intercept: "Ruko Bhaiya!" walk-away save-the-deal |
| **Bohni Mode** | Golden "Pehli Bohni!" badge for morning negotiations |
| **Savings Soundbox** | Confetti + celebration overlay with ONDC/DPDP badges |
| **Language Toggle** | English, हिन्दी, தமிழ், తెలుగు, मराठी |

## Security

| Layer | Protection |
|-------|-----------|
| **Admin routes** | `X-API-Key` header validated against `API_ADMIN_KEY` env var (timing-safe comparison) |
| **Buyer routes** | `X-Session-Token` header (returned on `/start`, required on `/offer` and `/status`) |
| **Rate limiting** | Per-IP limit on `/start` (default 30/min), per-session cooldown on `/offer` (2s) |
| **Input validation** | Session ID format (`^[a-f0-9]{32}$`), product ID format (`^[a-zA-Z0-9_-]{1,100}$`), buyer_price (finite, positive) |
| **Body size** | 64 KB max request body |
| **Prompt injection** | Buyer messages + template values sanitized — control chars stripped, injection patterns redacted |
| **CORS** | Restricted origins, methods, and headers |
| **Swagger** | `/docs` and `/redoc` auto-disabled when `ENV=production` |
| **Database auth** | MongoDB + Redis credentials configured via env vars |
| **Distributed locks** | Redis-based per-session lock prevents concurrent offer processing |
| **Structured logging** | JSON-formatted logs with `X-Request-ID` tracing |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NIM_API_KEY` | — | NVIDIA NIM API key (`nvapi-...`). Get at [build.nvidia.com](https://build.nvidia.com/) |
| `NIM_BASE_URL` | `https://integrate.api.nvidia.com/v1` | NIM API endpoint |
| `NIM_MODEL` | `z-ai/glm4_7` | Model identifier |
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DB_NAME` | `mol_bhav` | Database name |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `DEFAULT_BETA` | `5.0` | Concession curve aggressiveness |
| `DEFAULT_ALPHA` | `0.6` | TFT reciprocity damping factor |
| `DEFAULT_MAX_ROUNDS` | `15` | Max negotiation rounds |
| `DEFAULT_SESSION_TTL_SECONDS` | `300` | Session timeout |
| `MIN_RESPONSE_DELAY_MS` | `2000` | Anti-bot cooldown between offers |
| `CORS_ALLOWED_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins |
| `API_ADMIN_KEY` | — | Admin API key (blank = no auth in dev) |
| `ENV` | `development` | `development` or `production` |

## LLM Configuration (NVIDIA NIM)

The dialogue engine uses [NVIDIA NIM](https://build.nvidia.com/) — a free-tier, OpenAI-compatible inference API.

### Chain-of-Thought Reasoning

The dialogue generator uses `<think>` tags for step-by-step reasoning before generating Hinglish responses. CoT reasoning is:
- **Visible** in `metadata.reasoning` when `ENV=development`
- **Stripped** from responses when `ENV=production`

### JSON Mode Fallback

The generator tries `response_format={"type": "json_object"}` first. If the model doesn't support it, it automatically falls back to regex-based JSON extraction from plain text.

## Deployment

### Production Deployment (Docker)

```bash
# 1. Clone and configure
git clone https://github.com/PRADDZY/mol-bhav.git
cd mol-bhav
cp .env.example .env

# 2. Edit .env for production
#    - Set NIM_API_KEY=nvapi-...
#    - Set strong MONGO_PASSWORD and REDIS_PASSWORD
#    - Set API_ADMIN_KEY to a strong random string
#    - Set ENV=production (disables /docs, /redoc)
#    - Set CORS_ALLOWED_ORIGINS to your frontend domain

# 3. Launch
docker compose up -d --build

# 4. Seed demo products
docker compose exec app python -m scripts.seed

# 5. Verify health
curl http://localhost:8000/health
```

### Production Checklist

- [ ] Set `ENV=production` — disables Swagger docs
- [ ] Set strong `API_ADMIN_KEY` for admin routes
- [ ] Set strong `MONGO_PASSWORD` and `REDIS_PASSWORD`
- [ ] Set `NIM_API_KEY` to your NVIDIA NIM key
- [ ] Set `CORS_ALLOWED_ORIGINS` to your frontend domain(s)
- [ ] Put behind a reverse proxy (nginx/Caddy) with HTTPS
- [ ] Configure log aggregation (structured JSON logs to stdout)
- [ ] Set up MongoDB replica set for durability (optional)

### Frontend Deployment

```bash
cd frontend
npm install
npm run build

# Static export or Node.js server:
npm start
# Or deploy to Vercel/Netlify with NEXT_PUBLIC_API_URL env var
```

## Testing

```bash
# Run all 132 tests
pytest tests/ -v

# Run specific test module
pytest tests/test_state_machine.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing
```

**Test coverage includes:**
- Negotiation engine (state machine, concession curves, reciprocity, bot detection)
- Price validator (edge cases: NaN, infinity, negative, boundary)
- Dialogue generator (CoT parsing, sanitization, injection, API fallback)
- API endpoints (auth, rate limiting, Beckn protocol, products)
- End-to-end flow (start → offer → status)

## License

MIT
