from pydantic import BaseModel

class GeneratePresentationRequest(BaseModel):
    template_name: str
    prompt: str | None = None