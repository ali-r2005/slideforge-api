import json
import logging
import re
from typing import Optional, Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)

from dotenv import load_dotenv
import os
from pydantic import SecretStr
from app.utils.ai_validation import AIResponseValidationError, validate_ai_response
from app.utils.prompts import (
    SYSTEM_PROMPT,
    build_correction_prompt,
    build_user_prompt
)

load_dotenv()

# We use JSON mode to force the model to return valid JSON
llm = ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL") or "gpt-4o-mini",
    base_url="https://openrouter.ai/api/v1",
    api_key=SecretStr(os.getenv("OPENROUTER_API_KEY") or ""),
    temperature=0.7,
    model_kwargs={"response_format": {"type": "json_object"}}
)

def extract_json(content: str) -> str:
    """
    Cleans the AI response by removing markdown code blocks if present.
    """
    # Remove markdown code blocks like ```json ... ```
    content = re.sub(r"```json\s*", "", content)
    content = re.sub(r"```\s*", "", content)
    return content.strip()

async def _request_ai_content(prompt: str) -> str | list[str | dict[Any, Any]]:
    try:
        response = await llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
    except Exception as error:
        raise AIResponseValidationError(
            f"AI provider request failed: {error}"
        ) from error

    return response.content

async def generate_ai_content(user_prompt: str, fields: List[Dict[str, Any]], template_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    prompt = build_user_prompt(
        user_prompt=user_prompt,
        fields=fields,
        template_metadata=template_metadata
    )
    logging.info(f"Initial AI prompt: \n{prompt}")

    last_error = None

    for _ in range(2):
        raw_content = await _request_ai_content(prompt)
        content = extract_json(raw_content)

        logging.info(f"Raw AI content: {raw_content}")

        try:
            data = json.loads(content)
            return validate_ai_response(
                data=data,
                fields=fields,
                trim_long_fields=True
            )
        except (json.JSONDecodeError, AIResponseValidationError) as error:
            last_error = error
            prompt = build_correction_prompt(
                original_prompt=prompt,
                invalid_content=content,
                validation_error=str(error)
            )

    raise AIResponseValidationError(
        f"AI returned invalid content after retry: {last_error}"
    )
