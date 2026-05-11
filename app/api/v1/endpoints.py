from fastapi import APIRouter
from app.services.pptx_service import extract_ppt_metadata
from fastapi.responses import FileResponse
from app.services.pptx_service import generate_presentation

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
def generate_ppt():

    dummy_ai_response = {
        "title": "AI Presentation Generator",
        "summary": "This presentation was generated automatically",
        "problem_title": "The Problem",
        "problem_description": "Creating presentations manually takes time"
    }

    output_file = "generated/result.pptx"

    generate_presentation(
        template_path="templates/template.pptx",
        output_path=output_file,
        replacements=dummy_ai_response
    )

    return FileResponse(
        path=output_file,
        filename="generated_presentation.pptx",
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )