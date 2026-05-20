from pathlib import Path
import uuid
from fastapi import APIRouter, HTTPException
from app.services.pptx_service import (
    attach_placeholder_values,
    convert_pptx_to_pdf,
    extract_ppt_metadata,
    generate_presentation,
    generate_template_thumbnail
)
from app.schemas.generate_schema import GeneratePresentationRequest, UpdatePresentationRequest
from app.services.ai_service import generate_ai_content
from app.utils.ai_validation import AIResponseValidationError
from app.utils.template_metadata import load_template_metadata
from app.utils.schema_loader import load_schema, has_schema
from app.utils.schema_validator import SchemaValidator
from app.utils.enhanced_prompt_builder import build_enhanced_prompt
import logging

logging.basicConfig(level=logging.INFO)
router = APIRouter()

#get metadata endpoint just for debuging
@router.get("/metadata/{template_name}")
async def get_metadata(template_name: str):
    template_path = Path(f"templates/{template_name}.pptx").resolve()
    metadata = extract_ppt_metadata(template_path=str(template_path))
    return {
        "success": True,
        "data": metadata
    }

@router.get("/templates")
def get_templates():
    templates_dir = Path("templates").resolve()

    if not templates_dir.is_dir():
        return {
            "success": True,
            "data": []
        }

    templates = []
    for template_path in sorted(templates_dir.glob("*.pptx")):
        if template_path.is_file():
            # Generate thumbnail if it doesn't exist
            generate_template_thumbnail(str(template_path))
            
            templates.append({
                "name": template_path.stem,
                "filename": template_path.name,
                "thumbnail_url": f"/thumbnails/{template_path.stem}.png"
            })

    return {
        "success": True,
        "data": templates
    }

@router.get("/schema/{template_name}")
def get_schema(template_name: str):
    """
    Get the form schema for a template, if it exists.
    Returns empty object if template has no schema (graceful fallback).
    """
    schema = load_schema(template_name)

    if schema is None:
        # No schema found - return empty object (graceful fallback)
        return {
            "success": True,
            "data": None,
            "has_schema": False
        }

    return {
        "success": True,
        "data": schema,
        "has_schema": True
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

    # Load template metadata
    template_metadata = load_template_metadata(request.template_name, str(templates_dir))

    # Validate form_data if provided
    if request.form_data:
        schema = load_schema(request.template_name)
        if schema:
            is_valid, errors = SchemaValidator.validate(request.form_data, schema)
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Form validation failed: {'; '.join(errors)}"
                )
            # Filter out optional empty fields
            request.form_data = SchemaValidator.filter_optional_fields(request.form_data, schema)
            logging.info(f"Form data validated successfully: {request.form_data}")

    # Check that either prompt or form_data is provided
    if not request.prompt and not request.form_data:
        raise HTTPException(
            status_code=400,
            detail="Either 'prompt' or 'form_data' must be provided"
        )

    metadata = extract_ppt_metadata(template_path=str(template_path))
    fields = [
        placeholder
        for slide in metadata
        for placeholder in slide["placeholders"]
    ]
    logging.info(f"Fields: {fields}")

    # Build enhanced prompt if form_data exists
    user_prompt = request.prompt or ""
    if request.form_data:
        schema = load_schema(request.template_name)
        user_prompt = build_enhanced_prompt(user_prompt, request.form_data, schema)
        logging.info(f"Enhanced prompt built from form_data")

    try:
        ai_response = await generate_ai_content(
            user_prompt=user_prompt,
            fields=fields,
            template_metadata=template_metadata
        )
    except AIResponseValidationError as error:
        raise HTTPException(
            status_code=502,
            detail=f"AI returned invalid content: {error}"
        ) from error

    logging.info(f"AI response: {ai_response}")
    
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

    
