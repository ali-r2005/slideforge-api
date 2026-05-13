from pathlib import Path
import uuid
from fastapi import APIRouter, HTTPException
from app.services.pptx_service import (
    attach_placeholder_values,
    convert_pptx_to_pdf,
    extract_ppt_metadata,
    generate_presentation
)
from app.schemas.generate_schema import GeneratePresentationRequest, UpdatePresentationRequest
from app.services.ai_service import generate_ai_content
from app.utils.ai_validation import AIResponseValidationError
import logging

logging.basicConfig(level=logging.INFO)
router = APIRouter()

@router.get("/templates")
def get_templates():
    templates_dir = Path("templates").resolve()

    if not templates_dir.is_dir():
        return {
            "success": True,
            "data": []
        }

    templates = [
        {
            "name": template_path.stem,
            "filename": template_path.name
        }
        for template_path in sorted(templates_dir.glob("*.pptx"))
        if template_path.is_file()
    ]

    return {
        "success": True,
        "data": templates
    }

@router.post("/generate-ppt")
async def generate_ppt(request: GeneratePresentationRequest):
    template_name = f"{request.template_name}.pptx"
    logging.info(f"Received request to generate presentation using template: {template_name}")
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
    
    metadata = extract_ppt_metadata(template_path=str(template_path))
    fields = [
        placeholder
        for slide in metadata
        for placeholder in slide["placeholders"]
    ]
    
    try:
        ai_response = await generate_ai_content(
            user_prompt=request.prompt,
            fields=fields
        )
    except AIResponseValidationError as error:
        raise HTTPException(
            status_code=502,
            detail=f"AI returned invalid content: {error}"
        ) from error

    print(f"AI response: {ai_response}")
    
    file_id = uuid.uuid4()
    output_file = f"generated/{file_id}.pptx"

    generate_presentation(
        template_path=str(template_path),
        output_path=output_file,
        replacements=ai_response
    )

    try:
        pdf_file = convert_pptx_to_pdf(
            pptx_path=output_file,
            output_dir="generated"
        )
    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        ) from error

    metadata_with_values = attach_placeholder_values(
        metadata=metadata,
        replacements=ai_response
    )

    return {
        "template_name": request.template_name,
        "presentation_data": metadata_with_values,
        "pdf_url": f"/generated/{Path(pdf_file).name}",
        "pptx_url": f"/generated/{Path(output_file).name}"
    }


@router.post("/update-ppt")
async def update_ppt(request: UpdatePresentationRequest):
    template_name = f"{request.template_name}.pptx"
    logging.info(f"Received request to update presentation: {request.file_id} using template: {template_name}")
    
    templates_dir = Path("templates").resolve()
    template_path = (templates_dir / template_name).resolve()

    try:
        template_path.relative_to(templates_dir)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template name")

    if not template_path.is_file():
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    
    output_file = f"generated/{request.file_id}.pptx"
    
    generate_presentation(
        template_path=str(template_path),
        output_path=output_file,
        replacements=request.replacements
    )

    try:
        pdf_file = convert_pptx_to_pdf(
            pptx_path=output_file,
            output_dir="generated"
        )
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error))

    metadata = extract_ppt_metadata(template_path=str(template_path))
    metadata_with_values = attach_placeholder_values(
        metadata=metadata,
        replacements=request.replacements
    )

    return {
        "success": True,
        "template_name": request.template_name,
        "presentation_data": metadata_with_values,
        "pdf_url": f"/generated/{Path(pdf_file).name}",
        "pptx_url": f"/generated/{Path(output_file).name}"
    }

    
