from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class GeneratePresentationRequest(BaseModel):
    template_name: str = Field(
        min_length=1,
        max_length=100
    )

    prompt: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=5000,
        description="User prompt (optional if form_data is provided)"
    )

    form_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured form data from schema (optional)"
    )

class UpdatePresentationRequest(BaseModel):
    template_name: str = Field(min_length=1)
    file_id: str = Field(min_length=1)
    replacements: dict