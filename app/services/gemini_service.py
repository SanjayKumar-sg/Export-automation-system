"""
app/services/gemini_service.py — Gemini AI classification service.

Uses the official Google Generative AI SDK to classify buyers
in batches with retry logic and token usage tracking.
"""
from __future__ import annotations

import json
import logging
import time
import threading
from typing import Any, Dict, List, Optional

from app.extensions import db
from app.models.buyer import Buyer
from app.models.classification import Classification

logger = logging.getLogger("search")

# ── Global classification job state ───────────────────────────────────────
_classify_state: Dict[str, Any] = {
    "running": False,
    "progress": 0,
    "total": 0,
    "classified": 0,
    "failed": 0,
    "total_tokens": 0,
    "log": [],
    "errors": [],
}
_classify_lock = threading.Lock()


def get_classify_state() -> Dict[str, Any]:
    with _classify_lock:
        return dict(_classify_state)


class GeminiService:
    """Classifies buyers using the Gemini API."""

    CLASSIFICATION_PROMPT = """You are an expert export market analyst.

Classify the following buyer based on their email, company name, and website.

Respond ONLY with a valid JSON object (no markdown, no explanation):
{{
  "buyer_type": "<business|individual|manufacturer|distributor|importer|retailer|wholesaler>",
  "intent_level": "<high_intent|medium_intent|low_intent>",
  "confidence": <0.0-1.0>,
  "reasoning": "<one sentence>"
}}

Buyer Information:
- Email: {email}
- Company: {company}
- Website: {website}
- Country: {country}
- Source: {source}
"""

    def __init__(self, api_key: str, model_name: str = "gemini-3.5-flash", groq_api_key: str = "", groq_model_name: str = "qwen/qwen3.6-27b"):
        self.api_key = api_key
        self.groq_api_key = groq_api_key
        self.model_name = model_name
        self.groq_model_name = groq_model_name
        self._model = None
        self._groq_client = None
        self._init_models()

    def _init_models(self) -> None:
        """Initialise the AI models."""
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel(self.model_name)
                logger.info("Gemini model initialised: %s", self.model_name)
            except Exception as e:
                logger.error("Failed to initialise Gemini: %s", e)
                self._model = None

        if self.groq_api_key:
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=self.groq_api_key)
                logger.info("Groq client initialised.")
            except Exception as e:
                logger.error("Failed to initialise Groq: %s", e)
                self._groq_client = None

    def classify_buyer(self, buyer: Buyer, max_retries: int = 3) -> Optional[dict]:
        """
        Classify a single buyer using Gemini.
        Returns parsed classification dict or None on failure.
        """
        if self._model is None and self._groq_client is None:
            return None

        prompt = self.CLASSIFICATION_PROMPT.format(
            email=buyer.email or "unknown",
            company=buyer.company_name or "unknown",
            website=buyer.website or "unknown",
            country=buyer.country or "unknown",
            source=buyer.source_platform or "unknown",
        )

        for attempt in range(1, max_retries + 1):
            try:
                token_info = {"prompt_tokens": 0, "response_tokens": 0, "total_tokens": 0}

                # Prefer Groq if available (since the user requested it specifically), otherwise Gemini
                if self._groq_client:
                    try:
                        response = self._groq_client.chat.completions.create(
                            model=self.groq_model_name,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0,
                            response_format={"type": "json_object"}
                        )
                        text = response.choices[0].message.content.strip()
                        if response.usage:
                            token_info = {
                                "prompt_tokens": response.usage.prompt_tokens,
                                "response_tokens": response.usage.completion_tokens,
                                "total_tokens": response.usage.total_tokens,
                            }
                    except Exception as e:
                        logger.warning("Groq API error, falling back to Gemini: %s", e)
                        if self._model:
                            response = self._model.generate_content(prompt)
                            text = response.text.strip()
                            try:
                                meta = response.usage_metadata
                                token_info = {
                                    "prompt_tokens": meta.prompt_token_count,
                                    "response_tokens": meta.candidates_token_count,
                                    "total_tokens": meta.total_token_count,
                                }
                            except Exception:
                                pass
                        else:
                            raise e
                elif self._model:
                    response = self._model.generate_content(prompt)
                    text = response.text.strip()
                    try:
                        meta = response.usage_metadata
                        token_info = {
                            "prompt_tokens": meta.prompt_token_count,
                            "response_tokens": meta.candidates_token_count,
                            "total_tokens": meta.total_token_count,
                        }
                    except Exception:
                        pass

                # Strip markdown code fences if present
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]

                parsed = json.loads(text)
                parsed.update(token_info)
                return parsed

            except json.JSONDecodeError as e:
                logger.warning("Gemini JSON parse error (attempt %d): %s", attempt, e)
            except Exception as e:
                logger.warning("Gemini API error (attempt %d): %s", attempt, e)
                if attempt < max_retries:
                    time.sleep(2 ** attempt)  # Exponential backoff

        return None

    def generate_domains_for_keyword(self, keyword: str, max_domains: int = 10) -> List[str]:
        """Ask the LLM to generate a list of known company website domains for a given niche/keyword."""
        if self._model is None and self._groq_client is None:
            return []

        prompt = f"List {max_domains} real, active company website domains that are buyers, importers, or retailers of '{keyword}'. Return ONLY a JSON list of strings (e.g. ['example.com', 'shop.com']). Do not include https://."

        try:
            if self._groq_client:
                try:
                    response = self._groq_client.chat.completions.create(
                        model=self.groq_model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        response_format={"type": "json_object"}
                    )
                    text = response.choices[0].message.content.strip()
                except Exception as e:
                    logger.warning("Groq API error in domains, falling back to Gemini: %s", e)
                    if self._model:
                        response = self._model.generate_content(prompt)
                        text = response.text.strip()
                    else:
                        raise e
            elif self._model:
                response = self._model.generate_content(prompt)
                text = response.text.strip()
            else:
                return []

            import json
            import re
            
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                domains = json.loads(match.group(0))
                return [d.strip().replace("http://", "").replace("https://", "").replace("www.", "") for d in domains if "." in d]
            
            return [d for d in json.loads(text).values() if isinstance(d, list)][0]
        except Exception as e:
            logger.error("Failed to generate domains: %s", e)
            return []
    @staticmethod
    def start_classification(batch_size: int = 20, app=None) -> None:
        """Launch background classification thread."""
        with _classify_lock:
            if _classify_state["running"]:
                return
            _classify_state.update(
                running=True, progress=0, total=0,
                classified=0, failed=0, total_tokens=0, log=[], errors=[]
            )

        thread = threading.Thread(
            target=GeminiService._run_classification,
            args=(batch_size, app),
            daemon=True,
        )
        thread.start()

    @staticmethod
    def _run_classification(batch_size: int, app) -> None:
        """Worker function for batch classification."""
        from flask import current_app

        ctx = app.app_context() if app else None
        context_manager = ctx if ctx else _NullContext()

        with context_manager:
            from flask import current_app as ca
            from app.services.settings_service import SettingsService
            
            api_key = SettingsService.get("gemini_api_key") or ca.config.get("GEMINI_API_KEY", "")
            groq_api_key = SettingsService.get("groq_api_key") or ca.config.get("GROQ_API_KEY", "")
            model_name = SettingsService.get("gemini_model") or ca.config.get("GEMINI_MODEL", "gemini-3.5-flash")
            groq_model_name = SettingsService.get("groq_model") or ca.config.get("GROQ_MODEL", "qwen/qwen3.6-27b")
            max_retries = ca.config.get("GEMINI_MAX_RETRIES", 3)

            service = GeminiService(api_key=api_key, model_name=model_name, groq_api_key=groq_api_key, groq_model_name=groq_model_name)

            # Get unclassified valid buyers
            buyers = Buyer.query.filter(
                Buyer.buyer_type == "unclassified",
                Buyer.email_status == "valid",
            ).all()

            with _classify_lock:
                _classify_state["total"] = len(buyers)

            GeminiService._log_msg(f"Starting classification of {len(buyers)} buyers.")

            for i, buyer in enumerate(buyers):
                result = service.classify_buyer(buyer, max_retries=max_retries)

                if result:
                    # Update buyer record
                    buyer.buyer_type = result.get("buyer_type", "business")
                    buyer.intent_level = result.get("intent_level", "unknown")
                    buyer.classification_confidence = result.get("confidence")
                    buyer.classification_notes = result.get("reasoning")

                    # Save classification record
                    cl = Classification(
                        buyer_id=buyer.id,
                        buyer_type=buyer.buyer_type,
                        intent_level=buyer.intent_level,
                        confidence_score=buyer.classification_confidence,
                        reasoning=buyer.classification_notes,
                        model_name=model_name,
                        prompt_tokens=result.get("prompt_tokens", 0),
                        response_tokens=result.get("response_tokens", 0),
                        total_tokens=result.get("total_tokens", 0),
                        status="success",
                    )  # type: ignore
                    db.session.add(cl)

                    with _classify_lock:
                        _classify_state["classified"] += 1
                        _classify_state["total_tokens"] += result.get("total_tokens", 0)
                else:
                    buyer.classification_notes = "Gemini classification failed"
                    cl = Classification(
                        buyer_id=buyer.id,
                        buyer_type="unclassified",
                        intent_level="unknown",
                        status="failed",
                        error_message="Max retries exceeded",
                    )  # type: ignore
                    db.session.add(cl)
                    with _classify_lock:
                        _classify_state["failed"] += 1

                with _classify_lock:
                    _classify_state["progress"] = i + 1

                # Batch commit
                if (i + 1) % batch_size == 0:
                    try:
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        logger.error("Batch commit error: %s", e)

                # Rate limiting: ~2 requests/second to avoid 429
                time.sleep(0.6)

            # Final commit
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()

            with _classify_lock:
                _classify_state["running"] = False

            GeminiService._log_msg(
                f"Classification complete. "
                f"Classified: {_classify_state['classified']}, "
                f"Failed: {_classify_state['failed']}, "
                f"Tokens: {_classify_state['total_tokens']}"
            )

    @staticmethod
    def _log_msg(msg: str, level: str = "info") -> None:
        with _classify_lock:
            _classify_state["log"].append(msg)
        getattr(logger, level)(msg)


class _NullContext:
    """No-op context manager for when app context already exists."""
    def __enter__(self): return self
    def __exit__(self, *args): pass
