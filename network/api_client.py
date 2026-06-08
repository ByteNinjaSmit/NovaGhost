import json
import logging
import threading
import base64
import io
import requests
from typing import Optional
from abc import ABC, abstractmethod
from PIL import Image
from config import Config

logger = logging.getLogger(__name__)

def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    buffered = io.BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

class VisionProvider(ABC):
    @abstractmethod
    def analyze_image(self, image: Image.Image, api_key: str, model: str, timeout: int) -> Optional[str]:
        pass

    def get_system_prompt(self) -> str:
        return (
            "You are a visual analysis answering engine. "
            "Examine the image carefully. "
            "Identify the question or task presented in the image and answer it directly and completely. "
            "Provide the full answer, not just an option letter. "
            "If the question is multiple choice, return the complete answer text, not A, B, C, or D. "
            "Do not explain your reasoning. "
            "Do not add introductions, conclusions, apologies, warnings, or extra commentary. "
            "Do not say phrases like 'The answer is'. "
            "Return only the final answer."
        )

class GeminiVisionProvider(VisionProvider):
    def analyze_image(self, image: Image.Image, api_key: str, model: str, timeout: int) -> Optional[str]:
        if not api_key:
            logger.warning("Gemini: Missing API Key.")
            return None
        try:
            b64_data = image_to_base64(image)
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": self.get_system_prompt()
                            },
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
                    "maxOutputTokens": 150,
                    "temperature": 0.2
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
    def analyze_image(self, image: Image.Image, api_key: str, model: str, timeout: int) -> Optional[str]:
        if not api_key:
            logger.warning("OpenAI: Missing API Key.")
            return None
        try:
            b64_data = image_to_base64(image)
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.get_system_prompt()
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 150,
                "temperature": 0.2
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
    def analyze_image(self, image: Image.Image, api_key: str, model: str, timeout: int) -> Optional[str]:
        if not api_key:
            logger.warning("OpenRouter: Missing API Key.")
            return None
        try:
            b64_data = image_to_base64(image)
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.get_system_prompt()
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 150,
                "temperature": 0.2
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

    def analyze_image(self, image: Image.Image, api_key: str, model: str, timeout: int) -> Optional[str]:
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
            payload = {
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": self.get_system_prompt(),
                    "images": [b64_data]
                }],
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 150}
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
    def __init__(self, config: Config):
        self.config = config
        self.providers = {
            "gemini": GeminiVisionProvider(),
            "openai": OpenAiVisionProvider(),
            "openrouter": OpenRouterVisionProvider(),
            "ollama": get_ollama_provider()
        }
        self._last_error: str = ""

    def query_image(self, image: Image.Image) -> Optional[str]:
        errors = []
        provider_name = self.config.ACTIVE_PROVIDER.lower()
        model = self.config.ACTIVE_MODEL
        api_key = self.config.get_api_key(provider_name)

        if not api_key:
            errors.append(f"No {provider_name} key")
        else:
            provider = self.providers.get(provider_name)
            if provider:
                logger.info(f"Querying '{provider_name}' model '{model}'")
                res = provider.analyze_image(image, api_key, model, self.config.API_TIMEOUT)
                if res:
                    return self._clean_response(res)
                detail = getattr(provider, "_last_error", "")
                errors.append(detail if detail else f"{provider_name}/{model} failed")

        if self.config.FALLBACK_ENABLED:
            fb_name = self.config.FALLBACK_PROVIDER.lower()
            fb_model = self.config.FALLBACK_MODEL
            fb_key = self.config.get_api_key(fb_name)
            if not fb_key:
                errors.append(f"No {fb_name} fallback key")
            else:
                fb_provider = self.providers.get(fb_name)
                if fb_provider:
                    logger.warning(f"Fallback: '{fb_name}' model '{fb_model}'")
                    res = fb_provider.analyze_image(image, fb_key, fb_model, self.config.API_TIMEOUT)
                    if res:
                        return self._clean_response(res)
                    detail = getattr(fb_provider, "_last_error", "")
                    errors.append(detail if detail else f"{fb_name}/{fb_model} failed")

        self._last_error = " | ".join(errors)
        logger.error(f"All providers failed: {self._last_error}")
        return None

    def query(self, image: Image.Image) -> Optional[str]:
        # Alias for backward-compatibility with caller modules
        return self.query_image(image)

    def _clean_response(self, ai_response: str) -> str:
        clean_text = " ".join(ai_response.split())
        if clean_text.endswith("."):
            clean_text = clean_text[:-1]
        return clean_text[:self.config.MAX_RESPONSE_LENGTH].strip()

APIHandler = ApiClient
