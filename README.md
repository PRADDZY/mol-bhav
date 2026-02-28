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
docker compose up -d

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Configure
cp .env.example .env
# Edit .env with your OpenAI API key

# 4. Run
uvicorn app.main:app --reload

# 5. Test
pytest tests/ -v
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
