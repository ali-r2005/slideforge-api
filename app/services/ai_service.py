import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)

from dotenv import load_dotenv
import os

from app.utils.prompts import SYSTEM_PROMPT

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL"),
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.7
)

def build_user_prompt(user_prompt: str, fields: list[str]):
    fields_text = "\n".join(
        [f"- {field}" for field in fields]
    )

    return f"""
Generate presentation content for this request:

{user_prompt}

Return JSON with these fields:

{fields_text}
"""

async def generate_ai_content(user_prompt: str, fields: list[str]):
    prompt = build_user_prompt(
        user_prompt=user_prompt,
        fields=fields
    )

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])

    content = response.content

    return json.loads(content)
