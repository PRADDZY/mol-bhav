"""NVIDIA NIM dialogue generator — the "Mouth" of Mol-Bhav.

Takes the engine's strategic output (counter-price, tactic) and wraps it
in a culturally resonant Hinglish shopkeeper response.

Uses NVIDIA NIM's OpenAI-compatible API with Chain-of-Thought reasoning.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import openai
from openai import AsyncOpenAI

from app.config import settings
from app.engine.state_machine import EngineResult
from app.engine.validator import validate_price
from app.models.session import NegotiationSession

logger = logging.getLogger(__name__)

_PROMPT_DIR = Path(__file__).parent / "prompts"

_MAX_BUYER_MSG_LEN = 500
_INJECTION_PATTERNS = re.compile(
    r"(ignore\s+(all\s+)?previous|system\s*:|you\s+are\s+now|forget\s+(your|all)|disregard\s+(above|instructions))",
    re.IGNORECASE,
)

_THINK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL)
_JSON_RE = re.compile(r"\{[\s\S]*\}")


def _load_prompt(name: str) -> str:
    return (_PROMPT_DIR / name).read_text(encoding="utf-8")


def _extract_think_and_json(raw: str) -> tuple[str, dict]:
    """Parse CoT <think> block and JSON payload from LLM output.

    Returns (reasoning_text, parsed_json_dict).
    """
    reasoning = ""
    think_match = _THINK_RE.search(raw)
    if think_match:
        reasoning = think_match.group(1).strip()
        raw = raw[think_match.end() :]  # everything after </think>

    # Try strict JSON parse first
    try:
        return reasoning, json.loads(raw.strip())
    except json.JSONDecodeError:
        pass

    # Fallback: extract first JSON object from text
    json_match = _JSON_RE.search(raw)
    if json_match:
        try:
            return reasoning, json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return reasoning, {}


class DialogueResponse:
    def __init__(
        self,
        message: str,
        price: float,
        sentiment: str,
        tactic: str,
        reasoning: str = "",
    ):
        self.message = message
        self.price = price
        self.sentiment = sentiment
        self.tactic = tactic
        self.reasoning = reasoning


class DialogueGenerator:
    def __init__(self):
        self._client = AsyncOpenAI(
            base_url=settings.nim_base_url,
            api_key=settings.nim_api_key,
            timeout=30.0,
        )
        self._system_prompt = _load_prompt("system.txt")
        self._walk_away_prompt = _load_prompt("walk_away.txt")
        self._bundle_prompt = _load_prompt("bundle.txt")

    @staticmethod
    def _sanitize_template_value(val: str | float | int) -> str:
        """Sanitize a value before template interpolation to prevent prompt injection."""
        s = str(val)
        # Strip any characters that could be used for prompt injection in templates
        s = re.sub(r"[\x00-\x09\x0b-\x1f\x7f]", "", s)
        if _INJECTION_PATTERNS.search(s):
            return "[redacted]"
        return s[:200]  # cap length to prevent prompt stuffing

    @staticmethod
    def _sanitize_buyer_message(msg: str) -> str:
        """Truncate, strip control chars, redact prompt injection attempts."""
        msg = msg[:_MAX_BUYER_MSG_LEN]
        # Remove control characters except newline
        msg = re.sub(r"[\x00-\x09\x0b-\x1f\x7f]", "", msg)
        if _INJECTION_PATTERNS.search(msg):
            logger.warning("Prompt injection attempt detected in buyer message")
            msg = "[message redacted]"
        return msg

    async def generate_response(
        self,
        session: NegotiationSession,
        engine_result: EngineResult,
        buyer_message: str = "",
        language: str = "en",
    ) -> DialogueResponse:
        """Generate a Hinglish shopkeeper response for the current turn."""
        system = self._system_prompt
        buyer_message = self._sanitize_buyer_message(buyer_message)

        # Build context for the LLM
        user_context = self._build_user_prompt(
            session, engine_result, buyer_message, language
        )

        # Pick template overlay based on tactic
        if engine_result.tactic == "walk_away_save":
            extra = self._walk_away_prompt.format(
                product_name=self._sanitize_template_value(session.product_name),
                buyer_price=self._sanitize_template_value(
                    session.offer_history.last_buyer_offer.price
                    if session.offer_history.last_buyer_offer
                    else "?"
                ),
                current_price=self._sanitize_template_value(session.current_seller_price),
                save_price=self._sanitize_template_value(engine_result.counter_price),
            )
            user_context += f"\n\nSPECIAL INSTRUCTION:\n{extra}"

        elif engine_result.tactic == "quantity_pivot":
            meta = engine_result.metadata
            extra = self._bundle_prompt.format(
                product_name=self._sanitize_template_value(session.product_name),
                unit_price=self._sanitize_template_value(engine_result.counter_price),
                quantity=self._sanitize_template_value(meta.get("quantity", 2)),
                bundle_price=self._sanitize_template_value(engine_result.counter_price),
                bundle_total=self._sanitize_template_value(meta.get("bundle_total", 0)),
            )
            user_context += f"\n\nSPECIAL INSTRUCTION:\n{extra}"

        reasoning, data = await self._call_nim(system, user_context, engine_result)

        # Validate: LLM must not override the engine's price
        llm_price = data.get("suggested_price", engine_result.counter_price)
        validated = validate_price(
            float(llm_price), session.reservation_price, session.anchor_price
        )
        final_price = engine_result.counter_price  # always trust engine over LLM

        if validated.was_overridden:
            logger.warning("LLM tried to override price: %s", validated.override_reason)

        return DialogueResponse(
            message=data.get("message", f"₹{final_price} — final offer, bhaiya."),
            price=final_price,
            sentiment=data.get("sentiment", "firm"),
            tactic=data.get("tactic", engine_result.tactic),
            reasoning=reasoning,
        )

    async def _call_nim(
        self,
        system: str,
        user_context: str,
        engine_result: EngineResult,
    ) -> tuple[str, dict]:
        """Call NVIDIA NIM API with JSON-mode fallback and CoT extraction."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_context},
        ]
        fallback = {
            "message": f"Bhaiya, best price for you — ₹{engine_result.counter_price}. Isse kam nahi hoga.",
            "suggested_price": engine_result.counter_price,
            "sentiment": "firm",
            "tactic": engine_result.tactic,
        }

        # Attempt 1: with response_format JSON mode
        try:
            resp = await self._client.chat.completions.create(
                model=settings.nim_model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.8,
                max_tokens=512,
            )
            raw = resp.choices[0].message.content or "{}"
            reasoning, data = _extract_think_and_json(raw)
            if data:
                return reasoning, data
        except openai.BadRequestError:
            # NIM may not support response_format — fall through to attempt 2
            logger.info("NIM rejected JSON mode, retrying without response_format")
        except (openai.APIError, openai.APITimeoutError):
            logger.exception("NIM API call failed, using fallback response")
            return "", fallback

        # Attempt 2: without response_format (extract JSON from text)
        try:
            resp = await self._client.chat.completions.create(
                model=settings.nim_model,
                messages=messages,
                temperature=0.8,
                max_tokens=512,
            )
            raw = resp.choices[0].message.content or ""
            reasoning, data = _extract_think_and_json(raw)
            if data:
                return reasoning, data
            logger.warning("Could not parse JSON from NIM response, using fallback")
            return reasoning, fallback
        except (openai.APIError, openai.APITimeoutError):
            logger.exception("NIM API call failed (attempt 2), using fallback response")
            return "", fallback

    def _build_user_prompt(
        self,
        session: NegotiationSession,
        engine_result: EngineResult,
        buyer_message: str,
        language: str = "en",
    ) -> str:
        history_lines = []
        for o in session.offer_history.offers[-6:]:  # last 6 turns for context
            who = "Customer" if o.actor.value == "buyer" else "You"
            history_lines.append(f"  {who}: ₹{o.price}" + (f' — "{o.message}"' if o.message else ""))

        history_str = "\n".join(history_lines) if history_lines else "  (No history yet)"

        lang_note = ""
        if language != "en":
            lang_note = f"\nLANGUAGE PREFERENCE: The customer prefers '{language}'. Adjust your Hinglish accordingly.\n"

        return f"""CURRENT NEGOTIATION STATE:
Product: {session.product_name}
List price: ₹{session.anchor_price}
Round: {session.current_round} / {session.max_rounds}
{lang_note}
OFFER HISTORY (recent):
{history_str}

CUSTOMER JUST SAID: "{buyer_message}"
CUSTOMER'S OFFER: ₹{session.offer_history.last_buyer_offer.price if session.offer_history.last_buyer_offer else 'none yet'}

SYSTEM DECISION:
- Your counter-price is: ₹{engine_result.counter_price}  (USE THIS EXACT PRICE)
- Tactic: {engine_result.tactic}
- Negotiation state: {engine_result.state.value}

Generate your Hinglish response. Remember: use EXACTLY ₹{engine_result.counter_price} as your price."""
