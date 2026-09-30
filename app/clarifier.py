class Clarifier:
    def __init__(self, llm):
        self.llm = llm

    async def handle_clarification(self, original_prompt: str, answer: str, schema: str = None) -> str:
        combined = f"{original_prompt} Clarification: {answer}"
        sql, need_clarify, question = await self.llm.text_to_sql(combined, schema=schema)
        return sql, need_clarify, question
