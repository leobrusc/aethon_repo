"""
openai_driver.py
Driver para modelos OpenAI via OpenAI Python SDK (client OpenAI()).
Usa o método chat.completions para consistência com o orquestrador.
Observação: a chave API deve ser fornecida via variável de ambiente OPENAI_API_KEY.
"""
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()

class OpenAIDriver:
    NAME = "gpt-4o-mini"
    # permitimos passar any model name to infer via parameter

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.client = OpenAI()
        self.model_name = model_name or "gpt-4o-mini"

    def infer(self, prompt: str, max_tokens: int = 256, temperature: float = 0.2):
        try:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Analyze the user prompt and respond succinctly."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            # SDK returns choices list; handle safely
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
            return f"[OPENAI_ERROR] {e}"
