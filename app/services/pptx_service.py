from pptx import Presentation
import re
import shutil
import subprocess
from pathlib import Path
from app.utils.placeholder import infer_placeholder_type, TYPE_MAX_CHARS

# metadata extraction and presentation generation logic will be use by an ai agent to create pptx files based on user input and a template file. The pptx template will have placeholders like {{title}}, {{summary}}, etc. which will be replaced by the ai agent with actual content before generating the final presentation.
def extract_ppt_metadata(template_path: str):

    presentation = Presentation(template_path)

    slides_data = []

    pattern = r"\{\{(.*?)\}\}"

    for slide_index, slide in enumerate(presentation.slides):

        slide_info = {
            "slide_number": slide_index + 1,
            "placeholders": []
        }

        for shape_index, shape in enumerate(slide.shapes):

            if not hasattr(shape, "text"):
                continue

            text = shape.text.strip()

            if not text:
                continue

            matches = re.findall(pattern, text)

            for match in matches:

                placeholder_type = infer_placeholder_type(match)

                slide_info["placeholders"].append({
                    "placeholder": match,
                    "slide_number": slide_index + 1,
                    "shape_index": shape_index,
                    "type": placeholder_type,
                    "max_chars": TYPE_MAX_CHARS.get(
                        placeholder_type,
                        100
                    )
                })

        slides_data.append(slide_info)

    return slides_data

def generate_presentation(
    template_path: str,
    output_path: str,
    replacements: dict
):

    presentation = Presentation(template_path)

    for slide in presentation.slides:
        for shape in slide.shapes:

            if hasattr(shape, "text"):

                for key, value in replacements.items():
                    if isinstance(value, list):
                        value = "\n".join(value)

                    placeholder = f"{{{{{key}}}}}"

                    if placeholder in shape.text:
                        shape.text = shape.text.replace(
                            placeholder,
                            value
                        )

    presentation.save(output_path)

    return output_path

def attach_placeholder_values(metadata: list[dict], replacements: dict):
    return [
        {
            **slide,
            "placeholders": [
                {
                    **placeholder,
                    "value": replacements.get(placeholder["placeholder"])
                }
                for placeholder in slide["placeholders"]
            ]
        }
        for slide in metadata
    ]

def _find_soffice_path():
    soffice_path = shutil.which("soffice") or shutil.which("libreoffice")

    if soffice_path:
        return soffice_path

    possible_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]

    for possible_path in possible_paths:
        if Path(possible_path).is_file():
            return possible_path

    return None

def convert_pptx_to_pdf(pptx_path: str, output_dir: str = "generated"):
    soffice_path = _find_soffice_path()

    if not soffice_path:
        raise RuntimeError(
            "LibreOffice is required to convert PPTX files to PDF. "
            "Install LibreOffice or add soffice to PATH."
        )

    pptx_file = Path(pptx_path).resolve()
    pdf_dir = Path(output_dir).resolve()
    pdf_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            soffice_path,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(pdf_dir),
            str(pptx_file),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False
    )

    pdf_path = pdf_dir / f"{pptx_file.stem}.pdf"

    if result.returncode != 0 or not pdf_path.is_file():
        raise RuntimeError(
            f"PPTX to PDF conversion failed: {result.stderr or result.stdout}"
        )

    return str(pdf_path)
