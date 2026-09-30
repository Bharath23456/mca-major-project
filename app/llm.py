import os
import asyncio
from typing import Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4o-mini")

try:
    import openai
    openai.api_key = OPENAI_API_KEY
except Exception:
    openai = None


class LLM:
    def __init__(self, dialect: str = "sqlite"):
        self.api_key = OPENAI_API_KEY
        self.dialect = dialect.lower()

    async def text_to_sql(self, prompt: str, schema: Optional[str] = None) -> Tuple[str, bool, str]:
        if openai is None or not self.api_key:
            lower = prompt.lower()
            if "count" in lower or "how many" in lower or "average" in lower:
                return "", True, "Do you want the result grouped by any column or overall?"
            if lower.startswith("list") or lower.startswith("show") or lower.startswith("get"):
                parts = lower.split()
                table = parts[-1] if len(parts) >= 2 else "items"
                sql = f"SELECT * FROM {table} LIMIT 50;"
                return sql, False, ""
            return "", True, "Can you clarify which table and fields you mean?"

        system = (
            f"You are an assistant that converts natural language to safe, read-only SQL for a {self.dialect} database. "
            "Return only the SQL in your reply unless you need clarification."
        )
        user_msg = (
            f"Convert to SQL ({self.dialect.upper()}). Schema:\n{schema or 'unknown'}\n\n"
            f"Natural language: {prompt}\nIf ambiguous, ask one concise clarification question."
        )

        try:
            resp = await asyncio.get_event_loop().run_in_executor(None, lambda: openai.ChatCompletion.create(
                model=MODEL,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
                max_tokens=512,
                temperature=0,
            ))
            text = resp.choices[0].message.content.strip()
        except Exception as e:
            return "", True, f"LLM error: {e}"

        if text.endswith("?") or text.lower().startswith("clarify") or "?" in text:
            return "", True, text

        return text, False, ""
