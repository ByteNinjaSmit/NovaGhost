"""
NovaGhost — Vision API Client & AI Provider Pipeline.
Handles Gemini, OpenAI, OpenRouter, and local Ollama integrations with
structured JSON response schemas, token optimization, robust fallback, and retries.
"""

import json
import logging
import threading
import base64
import io
import re
import time
import requests
from typing import Optional, Dict, Any, Tuple, Union
from abc import ABC, abstractmethod
from PIL import Image

from config import Config
from engine.schemas import (
    StructuredAnswer, MultiQuestionResult, QuestionCategory, AssessmentFormat, compute_positions
)
from engine.solvers.answer_validator import AnswerValidator
from engine.screenshot_processor import ScreenshotProcessor
from engine.perceptual_cache import get_perceptual_cache
from engine.visual_feature_extractor import VisualFeatureExtractor
from engine.math_engine import SymPyMathEngine
from network.prompt_engine import PromptEngine

logger = logging.getLogger(__name__)


def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    buffered = io.BytesIO()
    # Save as PNG; if mode is RGBA convert to RGB or preserve PNG
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def parse_structured_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Robustly extracts and parses JSON from raw LLM output.
    Handles markdown code blocks, preamble, and trailing text.
    """
    if not raw_text or not raw_text.strip():
        return None

    cleaned = raw_text.strip()

    # 1. Try direct JSON parsing
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 2. Extract from markdown code fence ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # 3. Look for the first outer pair of curly braces { ... }
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_candidate = cleaned[first_brace:last_brace + 1]
        try:
            return json.loads(json_candidate)
        except Exception:
            # Try cleaning trailing commas
            cleaned_candidate = re.sub(r",\s*([\]}])", r"\1", json_candidate)
            try:
                return json.loads(cleaned_candidate)
            except Exception:
                pass

    return None


def parse_fallback_text(text: str) -> StructuredAnswer:
    """
    Fallback parser when a model returns non-JSON plain text.
    Extracts option letters, positions, or numerical values.
    """
    raw = text.strip()
    ans = StructuredAnswer(full_answer=raw, raw_response=raw)

    # Check for unclear screenshot
    if "unclear" in raw.lower() or "cannot read" in raw.lower():
        ans.needs_clarification = True
        ans.missing_information = raw
        return ans

    # Check for pure numerical answer
    num_match = re.fullmatch(r"[-+]?\d*\.?\d+", raw)
    if num_match:
        ans.assessment_format = AssessmentFormat.NAT
        ans.numerical_value = num_match.group(0)
        ans.full_answer = num_match.group(0)
        return ans

    # Check for option letter (e.g., "Option C: 125" or "C")
    opt_match = re.search(r"\b(?:Option\s+)?([A-D1-4])\b", raw, re.IGNORECASE)
    if opt_match:
        ans.option_label = opt_match.group(1).upper()
        # Look for the rest of text
        rem = re.sub(r"^(?:Correct\s+Answer|Option|Answer)?[:\s\-\.]*", "", raw, flags=re.IGNORECASE).strip()
        ans.full_answer = rem or ans.option_label

    return ans


class VisionProvider(ABC):
    @abstractmethod
    def analyze_image(self, image: Image.Image, api_key: str, model: str, timeout: int, prompt: Optional[str] = None) -> Optional[str]:
        pass

    def get_system_prompt(self) -> str:
        return PromptEngine.get_universal_prompt()


class GeminiVisionProvider(VisionProvider):
    def analyze_image(self, image: Image.Image, api_key: str, model: str, timeout: int, prompt: Optional[str] = None) -> Optional[str]:
        if not api_key:
            logger.warning("Gemini: Missing API Key.")
            return None
        try:
            b64_data = image_to_base64(image)
            active_prompt = prompt or self.get_system_prompt()
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": active_prompt},
                            {
                                "inlineData": {
                                    "mimeType": "image/png",
                                    "data": b64_data
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": 1024,
                    "temperature": 0.1
                }
            }
            headers = {"Content-Type": "application/json"}
            params = {"key": api_key}
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            response = requests.post(url, json=payload, headers=headers, params=params, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                if "candidates" in data and data["candidates"]:
                    content = data["candidates"][0].get("content", {})
                    if "parts" in content and content["parts"]:
                        reply = content["parts"][0].get("text", "").strip()
                        if reply:
                            return reply
            logger.error(f"Gemini API returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Gemini Vision call failed: {e}")
        return None


class OpenAiVisionProvider(VisionProvider):
    def analyze_image(self, image: Image.Image, api_key: str, model: str, timeout: int, prompt: Optional[str] = None) -> Optional[str]:
        if not api_key:
            logger.warning("OpenAI: Missing API Key.")
            return None
        try:
            b64_data = image_to_base64(image)
            active_prompt = prompt or self.get_system_prompt()
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": active_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{b64_data}"}
                            }
                        ]
                    }
                ],
                "max_tokens": 1024,
                "temperature": 0.1
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            url = "https://api.openai.com/v1/chat/completions"
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and data["choices"]:
                    reply = data["choices"][0]["message"]["content"].strip()
                    if reply:
                        return reply
            logger.error(f"OpenAI API returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"OpenAI Vision call failed: {e}")
        return None


class OpenRouterVisionProvider(VisionProvider):
    def analyze_image(self, image: Image.Image, api_key: str, model: str, timeout: int, prompt: Optional[str] = None) -> Optional[str]:
        if not api_key:
            logger.warning("OpenRouter: Missing API Key.")
            return None
        try:
            b64_data = image_to_base64(image)
            active_prompt = prompt or self.get_system_prompt()
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": active_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{b64_data}"}
                            }
                        ]
                    }
                ],
                "max_tokens": 1024,
                "temperature": 0.1
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://visualanalysis.local",
                "X-Title": "NovaGhost"
            }
            url = "https://openrouter.ai/api/v1/chat/completions"
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and data["choices"]:
                    reply = data["choices"][0]["message"]["content"].strip()
                    if reply:
                        return reply
            logger.error(f"OpenRouter API returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"OpenRouter Vision call failed: {e}")
        return None


class OllamaVisionProvider(VisionProvider):
    def __init__(self):
        self._pull_threads: dict = {}
        self._pull_status: dict = {}
        self._last_error: str = ""

    def is_running(self, base_url: str) -> bool:
        try:
            r = requests.get(f"{base_url}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def list_models(self, base_url: str) -> list:
        try:
            r = requests.get(f"{base_url}/api/tags", timeout=5)
            if r.status_code == 200:
                return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            pass
        return []

    def is_model_installed(self, base_url: str, model: str) -> bool:
        installed = self.list_models(base_url)
        model_base = model.split(":")[0]
        return any(m == model or m.startswith(model_base + ":") for m in installed)

    def pull_model(self, base_url: str, model: str, status_callback=None) -> bool:
        try:
            r = requests.post(
                f"{base_url}/api/pull",
                json={"name": model, "stream": True},
                stream=True,
                timeout=600
            )
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue
                status = data.get("status", "")
                completed = data.get("completed", 0)
                total = data.get("total", 0)
                if total and completed:
                    pct = int(completed * 100 / total)
                    msg = f"Installing {model}: {pct}%"
                else:
                    msg = f"Installing {model}: {status}"
                if status_callback:
                    status_callback(msg)
                if status == "success":
                    return True
            return True
        except Exception as e:
            logger.error(f"Ollama pull failed: {e}")
            if status_callback:
                status_callback(f"Install failed: {e}")
            return False

    def _start_pull_background(self, base_url: str, model: str) -> None:
        if model in self._pull_threads and self._pull_threads[model].is_alive():
            return
        self._pull_status[model] = f"Installing {model}..."

        def _pull():
            def _cb(msg):
                self._pull_status[model] = msg
            ok = self.pull_model(base_url, model, _cb)
            self._pull_status[model] = "done" if ok else "failed"

        t = threading.Thread(target=_pull, daemon=True)
        self._pull_threads[model] = t
        t.start()

    def analyze_image(self, image: Image.Image, api_key: str, model: str, timeout: int, prompt: Optional[str] = None) -> Optional[str]:
        from config import config as _cfg
        base_url = getattr(_cfg, "OLLAMA_BASE_URL", "http://localhost:11434")

        if not self.is_running(base_url):
            self._last_error = "Ollama not running — install from ollama.com"
            logger.error(self._last_error)
            return None

        pull_st = self._pull_status.get(model, "")
        if pull_st and pull_st not in ("done", "failed"):
            self._last_error = pull_st
            return None

        if not self.is_model_installed(base_url, model):
            self._start_pull_background(base_url, model)
            self._last_error = f"Installing {model}... (first use — triple-tap again when ready)"
            return None

        self._last_error = ""
        try:
            b64_data = image_to_base64(image)
            active_prompt = prompt or self.get_system_prompt()
            payload = {
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": active_prompt,
                    "images": [b64_data]
                }],
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 1024}
            }
            r = requests.post(f"{base_url}/api/chat", json=payload, timeout=timeout)
            if r.status_code == 200:
                content = r.json().get("message", {}).get("content", "").strip()
                if content:
                    return content
            self._last_error = f"Ollama HTTP {r.status_code}"
            logger.error(f"Ollama API returned {r.status_code}: {r.text[:200]}")
        except Exception as e:
            self._last_error = f"Ollama error: {e}"
            logger.error(f"Ollama Vision call failed: {e}")
        return None


_ollama_provider_singleton: Optional[OllamaVisionProvider] = None

def get_ollama_provider() -> OllamaVisionProvider:
    global _ollama_provider_singleton
    if _ollama_provider_singleton is None:
        _ollama_provider_singleton = OllamaVisionProvider()
    return _ollama_provider_singleton


class ApiClient:
    """Manages AI requests, JSON parsing, validation, and strict answer formatting."""

    def __init__(self, config: Config):
        self.config = config
        self.providers = {
            "gemini": GeminiVisionProvider(),
            "openai": OpenAiVisionProvider(),
            "openrouter": OpenRouterVisionProvider(),
            "ollama": get_ollama_provider()
        }
        self._last_error: str = ""
        self._last_structured_answer: Optional[StructuredAnswer] = None

    def query_structured(self, image: Image.Image) -> Tuple[Optional[str], Optional[Union[StructuredAnswer, MultiQuestionResult]]]:
        """
        Executes query pipeline:
        1. Fast Perceptual Cache lookup (<10ms).
        2. Non-destructive image enhancement (contrast, sharpness, resolution).
        3. Deterministic OpenCV visual contour feature extraction.
        4. Structured query to active vision provider (with retry and fallback).
        5. Deterministic SymPy mathematical verification and auto-correction.
        6. Multi-question parsing and AnswerValidator refinement.
        7. Strict format generation and cache storage.
        """
        # 1. Zero-latency perceptual cache check
        cache = get_perceptual_cache()
        cached_hit = cache.lookup(image)
        if cached_hit:
            formatted_text, cached_data = cached_hit
            if "questions" in cached_data and isinstance(cached_data["questions"], list):
                q_list = [self._dict_to_structured_answer(q) for q in cached_data["questions"]]
                multi_res = MultiQuestionResult(questions=q_list, is_cached=True)
            else:
                ans = self._dict_to_structured_answer(cached_data)
                multi_res = MultiQuestionResult(questions=[ans], is_cached=True)
            self._last_structured_answer = multi_res.get_active_answer()
            logger.info("Serving answer from zero-latency perceptual cache (<10ms).")
            return formatted_text, multi_res

        errors = []
        quality = ScreenshotProcessor.assess_image_quality(image)
        enhanced_image = ScreenshotProcessor.enhance_image(image)

        # 2. Geometric contour & layout feature extraction
        layout = ScreenshotProcessor.detect_layout_and_options(enhanced_image)
        visual_features = VisualFeatureExtractor.extract_contour_features(
            enhanced_image, layout.get("detected_options")
        )
        custom_prompt = PromptEngine.get_universal_prompt(
            visual_features.get("summary") if visual_features.get("available") else None
        )

        provider_name = self.config.ACTIVE_PROVIDER.lower()
        model = self.config.ACTIVE_MODEL
        api_key = self.config.get_api_key(provider_name)

        raw_reply = None
        if not api_key:
            errors.append(f"No {provider_name} key")
        else:
            provider = self.providers.get(provider_name)
            if provider:
                logger.info(f"Querying primary provider '{provider_name}' model '{model}'")
                for attempt in range(2):
                    raw_reply = provider.analyze_image(
                        enhanced_image, api_key, model, self.config.API_TIMEOUT, prompt=custom_prompt
                    )
                    if raw_reply:
                        break
                    time.sleep(0.5)
                if not raw_reply:
                    detail = getattr(provider, "_last_error", "")
                    errors.append(detail if detail else f"{provider_name}/{model} failed")

        # Fallback provider if primary failed
        if not raw_reply and self.config.FALLBACK_ENABLED:
            fb_name = self.config.FALLBACK_PROVIDER.lower()
            fb_model = self.config.FALLBACK_MODEL
            fb_key = self.config.get_api_key(fb_name)
            if not fb_key:
                errors.append(f"No {fb_name} fallback key")
            else:
                fb_provider = self.providers.get(fb_name)
                if fb_provider:
                    logger.warning(f"Using fallback provider: '{fb_name}' model '{fb_model}'")
                    raw_reply = fb_provider.analyze_image(
                        enhanced_image, fb_key, fb_model, self.config.API_TIMEOUT, prompt=custom_prompt
                    )
                    if not raw_reply:
                        detail = getattr(fb_provider, "_last_error", "")
                        errors.append(detail if detail else f"{fb_name}/{fb_model} failed")

        if not raw_reply:
            self._last_error = " | ".join(errors)
            logger.error(f"All providers failed: {self._last_error}")
            return None, None

        # Parse reply
        parsed_json = parse_structured_json(raw_reply)

        # 3. Multi-Question Detection and Parsing
        if parsed_json and "questions" in parsed_json and isinstance(parsed_json["questions"], list):
            sub_q_list = []
            for q_data in parsed_json["questions"]:
                ans = self._build_answer_from_dict(q_data, raw_reply)
                # Deterministic SymPy cross-verification for numerical aptitude
                if ans.question_category == QuestionCategory.NUMERICAL_APTITUDE and ans.full_answer:
                    corrected_val, was_corrected = SymPyMathEngine.verify_and_correct(ans.full_answer, ans.numerical_value or ans.full_answer)
                    if was_corrected:
                        ans.numerical_value = corrected_val
                validated_ans = AnswerValidator.validate_and_refine(ans, quality_metadata=quality)
                sub_q_list.append(validated_ans)

            multi_res = MultiQuestionResult(questions=sub_q_list)
            self._last_structured_answer = multi_res.get_active_answer()
            strict_text = multi_res.to_strict_format()

            # Store in perceptual cache
            cache.store(image, strict_text, {"questions": [q.__dict__ for q in sub_q_list]})
            return strict_text, multi_res

        # 4. Single-Question Parsing
        if parsed_json:
            ans = self._build_answer_from_dict(parsed_json, raw_reply)
        else:
            logger.warning("Model did not return JSON — falling back to text parsing.")
            ans = parse_fallback_text(raw_reply)

        # Deterministic SymPy cross-verification for numerical aptitude
        if ans.question_category == QuestionCategory.NUMERICAL_APTITUDE and ans.full_answer:
            target_val = ans.numerical_value or ans.full_answer
            corrected_val, was_corrected = SymPyMathEngine.verify_and_correct(ans.full_answer, target_val)
            if was_corrected:
                ans.numerical_value = corrected_val

        # Validate and refine answer
        validated_ans = AnswerValidator.validate_and_refine(ans, quality_metadata=quality)
        self._last_structured_answer = validated_ans
        multi_res = MultiQuestionResult(questions=[validated_ans])

        # Generate strict format text and cache
        strict_text = validated_ans.to_strict_format()
        cache.store(image, strict_text, validated_ans.__dict__)
        return strict_text, multi_res

    def _dict_to_structured_answer(self, d: Dict[str, Any]) -> StructuredAnswer:
        """Reconstructs StructuredAnswer from dictionary cleanly."""
        return StructuredAnswer(
            question_category=QuestionCategory(d.get("question_category", QuestionCategory.NUMERICAL_APTITUDE)),
            subcategory=str(d.get("subcategory", "General")),
            assessment_format=AssessmentFormat(d.get("assessment_format", AssessmentFormat.MCQ)),
            is_image_options=bool(d.get("is_image_options", False)),
            option_label=d.get("option_label"),
            option_index=d.get("option_index"),
            total_options=int(d.get("total_options", 4)),
            selected_options=d.get("selected_options", []),
            numerical_value=d.get("numerical_value"),
            full_answer=str(d.get("full_answer", "")),
            orientation=str(d.get("orientation", "horizontal")),
            position_from_left=d.get("position_from_left"),
            position_from_right=d.get("position_from_right"),
            grid_row=d.get("grid_row"),
            grid_col=d.get("grid_col"),
            confidence=float(d.get("confidence", 0.95)),
            needs_clarification=bool(d.get("needs_clarification", False)),
            missing_information=d.get("missing_information")
        )

    def query_image(self, image: Image.Image) -> Optional[str]:
        """Backward-compatible query returning formatted answer string."""
        formatted_text, _ = self.query_structured(image)
        return formatted_text

    def query(self, image: Image.Image) -> Optional[str]:
        return self.query_image(image)

    def _build_answer_from_dict(self, data: Dict[str, Any], raw_text: str) -> StructuredAnswer:
        from engine.schemas import QuestionCategory, AssessmentFormat
        cat_str = str(data.get("question_category", "")).lower()
        if "data" in cat_str or "chart" in cat_str or "graph" in cat_str:
            category = QuestionCategory.DATA_INTERPRETATION
        elif "non_verbal" in cat_str or "figure" in cat_str or "matrix" in cat_str:
            category = QuestionCategory.NON_VERBAL_REASONING
        elif "logic" in cat_str:
            category = QuestionCategory.LOGICAL_REASONING
        elif "verbal" in cat_str or "english" in cat_str:
            category = QuestionCategory.ENGLISH_VERBAL
        elif "tech" in cat_str or "computer" in cat_str:
            category = QuestionCategory.TECHNICAL_KNOWLEDGE
        else:
            category = QuestionCategory.NUMERICAL_APTITUDE

        fmt_str = str(data.get("assessment_format", "MCQ")).upper()
        if fmt_str == "NAT":
            fmt = AssessmentFormat.NAT
        elif fmt_str == "MSQ":
            fmt = AssessmentFormat.MSQ
        elif fmt_str == "IMAGE_OPTIONS" or data.get("is_image_options"):
            fmt = AssessmentFormat.IMAGE_OPTIONS
        else:
            fmt = AssessmentFormat.MCQ

        ans = StructuredAnswer(
            question_category=category,
            subcategory=str(data.get("subcategory", "General")),
            assessment_format=fmt,
            is_image_options=bool(data.get("is_image_options", fmt == AssessmentFormat.IMAGE_OPTIONS)),
            option_label=str(data["option_label"]).strip() if data.get("option_label") is not None else None,
            option_index=int(data["option_index"]) if data.get("option_index") is not None else None,
            total_options=int(data.get("total_options") or 4),
            selected_options=data.get("selected_options") or [],
            numerical_value=str(data["numerical_value"]).strip() if data.get("numerical_value") is not None else None,
            full_answer=str(data.get("full_answer") or data.get("numerical_value") or data.get("option_label") or "").strip(),
            orientation=str(data.get("orientation", "horizontal")),
            position_from_left=data.get("position_from_left"),
            position_from_right=data.get("position_from_right"),
            grid_row=data.get("grid_row"),
            grid_col=data.get("grid_col"),
            confidence=float(data.get("confidence", 0.95)),
            needs_clarification=bool(data.get("needs_clarification", False)),
            missing_information=data.get("missing_information"),
            raw_response=raw_text
        )
        return ans

    def _clean_response(self, ai_response: str) -> str:
        """Deprecated legacy cleaner kept for backward compatibility."""
        return ai_response.strip()


APIHandler = ApiClient
