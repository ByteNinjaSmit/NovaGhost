import logging
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

class ApiClient:
    def __init__(self, config: Config):
        self.config = config
        self.providers = {
            "gemini": GeminiVisionProvider(),
            "openai": OpenAiVisionProvider(),
            "openrouter": OpenRouterVisionProvider()
        }

    def query_image(self, image: Image.Image) -> Optional[str]:
        provider_name = self.config.ACTIVE_PROVIDER.lower()
        model = self.config.ACTIVE_MODEL
        api_key = self.config.get_api_key(provider_name)
        
        provider = self.providers.get(provider_name)
        if provider:
            logger.info(f"Querying active visual provider '{provider_name}' using model '{model}'")
            res = provider.analyze_image(image, api_key, model, self.config.API_TIMEOUT)
            if res:
                return self._clean_response(res)
        
        if self.config.FALLBACK_ENABLED:
            fb_provider_name = self.config.FALLBACK_PROVIDER.lower()
            fb_model = self.config.FALLBACK_MODEL
            fb_key = self.config.get_api_key(fb_provider_name)
            
            logger.warning(f"Active provider failed. Triggering fallback provider '{fb_provider_name}' with model '{fb_model}'")
            fb_provider = self.providers.get(fb_provider_name)
            if fb_provider:
                res = fb_provider.analyze_image(image, fb_key, fb_model, self.config.API_TIMEOUT)
                if res:
                    return self._clean_response(res)
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
