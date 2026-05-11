from pathlib import Path
import uuid
from fastapi import APIRouter, HTTPException
from app.services.pptx_service import extract_ppt_metadata, generate_presentation
from fastapi.responses import FileResponse
from app.schemas.generate_schema import GeneratePresentationRequest

router = APIRouter()

@router.get("/template-metadata")
def get_template_metadata():

    metadata = extract_ppt_metadata(
        "templates/template.pptx"
    )

    return {
        "success": True,
        "data": metadata
    }

@router.post("/generate-ppt")
def generate_ppt(request: GeneratePresentationRequest):
    template_name = f"{request.template_name}.pptx"
    print(f"Received request to generate presentation using template: {template_name}")
    templates_dir = Path("templates").resolve()
    template_path = (templates_dir / template_name).resolve()

    try:
        template_path.relative_to(templates_dir)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid template name"
        )

    if not template_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_name}' not found"
        )

    dummy_ai_response = {}
    
    metadata = extract_ppt_metadata(template_path=str(template_path))
    fields = [placeholder["placeholder"] for slide in metadata for placeholder in slide["placeholders"]]
    
    for field in fields:
        dummy_ai_response[field] = f"Sample content for {field}"  
    
    output_file = f"generated/{uuid.uuid4()}.pptx"

    generate_presentation(
        template_path=str(template_path),
        output_path=output_file,
        replacements=dummy_ai_response
    )

    return FileResponse(
        path=output_file,
        filename="generated_presentation.pptx",
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    
