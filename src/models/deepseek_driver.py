"""
DeepSeek API driver.

DeepSeek exposes an OpenAI-compatible chat completions API.
Set DEEPSEEK_API_KEY before running live inference.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


class DeepSeekDriver:
    NAME = "deepseek-v4-flash"

    def __init__(self, model_name: str = "deepseek-v4-flash", base_url: str = None):
        self.model_name = model_name
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=self.base_url,
        )

    def infer(self, prompt: str, max_tokens: int = 256, temperature: float = 0.2):
        try:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Analyze the user prompt and respond succinctly."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            if hasattr(resp, "choices") and len(resp.choices) > 0:
                choice = resp.choices[0]
                if hasattr(choice, "message"):
                    content = getattr(choice.message, "content", None)
                    if content is not None:
                        return content
                    if isinstance(choice.message, dict):
                        return choice.message.get("content", "")
                if isinstance(choice, dict):
                    return choice.get("text", "")
            return ""
        except Exception as e:
            return f"[DEEPSEEK_ERROR] {e}"
