from pydantic import BaseModel, Field

class GeneratePresentationRequest(BaseModel):
    template_name: str = Field(
        min_length=1,
        max_length=100
    )

    prompt: str = Field(
        min_length=5,
        max_length=5000
    )