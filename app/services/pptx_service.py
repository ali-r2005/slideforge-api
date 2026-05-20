from pptx import Presentation
import re
import shutil
import subprocess
from pathlib import Path
from app.utils.placeholder import infer_placeholder_type, TYPE_MAX_CHARS, extract_placeholder_metadata
from app.utils.map_logic import apply_map_logic
from app.utils.pptx_utils import get_shape_alt_text
from app.services.image_service import get_company_logo_path, get_topic_image_path, cleanup_temp_images
import logging
import copy

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
        # logging.info(f"Slide {slide_index + 1}")

        for shape_index, shape in enumerate(slide.shapes):
            # logging.info(f"Shape {shape_index} in slide {slide_index + 1}")
            # logging.info(f"Shape: {shape}")
            # logging.info(f"Shape text: {getattr(shape, 'text', 'No text attribute')}")
            # logging.info(f"Shape has text: {hasattr(shape, 'text')}")

            # 1. Check text for placeholders
            if hasattr(shape, "text") and shape.text.strip():
                matches = re.findall(pattern, shape.text.strip())
                for match in matches:
                    metadata = extract_placeholder_metadata(match)
                    placeholder_name = metadata["name"]
                    paragraphs_count = metadata["paragraphs"]
                    placeholder_type = infer_placeholder_type(placeholder_name)
                    slide_info["placeholders"].append({
                        "placeholder": placeholder_name,
                        "slide_number": slide_index + 1,
                        "shape_index": shape_index,
                        "type": placeholder_type,
                        "max_chars": TYPE_MAX_CHARS.get(placeholder_type, 100),
                        "paragraphs": paragraphs_count
                    })

            # 2. Check Alt Text for placeholders (common for images)
            alt_text = get_shape_alt_text(shape)
            if alt_text:
                matches = re.findall(pattern, alt_text)
                for match in matches:
                    metadata = extract_placeholder_metadata(match)
                    placeholder_name = metadata["name"]
                    paragraphs_count = metadata["paragraphs"]

                    # Avoid duplicate detection if it was already in the text (rare)
                    if any(p["placeholder"] == placeholder_name and p["shape_index"] == shape_index for p in slide_info["placeholders"]):
                        continue

                    placeholder_type = infer_placeholder_type(placeholder_name)
                    slide_info["placeholders"].append({
                        "placeholder": placeholder_name,
                        "slide_number": slide_index + 1,
                        "shape_index": shape_index,
                        "type": placeholder_type,
                        "max_chars": TYPE_MAX_CHARS.get(placeholder_type, 100),
                        "paragraphs": paragraphs_count
                    })

            # 3. Check for Tables with placeholders in Alt Text
            if shape.has_table:
                alt_text = get_shape_alt_text(shape)
                if alt_text:
                    matches = re.findall(pattern, alt_text)
                    for match in matches:
                        metadata = extract_placeholder_metadata(match)
                        placeholder_name = metadata["name"]
                        placeholder_type = infer_placeholder_type(placeholder_name)
                        if placeholder_type == "table":
                            slide_info["placeholders"].append({
                                "placeholder": placeholder_name,
                                "slide_number": slide_index + 1,
                                "shape_index": shape_index,
                                "type": "table",
                                "columns": len(shape.table.columns),
                                "max_chars": 500,
                                "paragraphs": 1
                            })


        slides_data.append(slide_info)

    return slides_data

def copy_run_formatting(source_run, target_run):
    """
    Copies all font formatting from source_run to target_run.
    """
    source_font = source_run.font
    target_font = target_run.font

    target_font.name = source_font.name
    target_font.size = source_font.size
    target_font.bold = source_font.bold
    target_font.italic = source_font.italic
    target_font.underline = source_font.underline

    # Copy color
    if source_font.color:
        try:
            if hasattr(source_font.color, 'rgb'):
                target_font.color.rgb = source_font.color.rgb
            elif hasattr(source_font.color, 'type'):
                target_font.color.type = source_font.color.type
        except:
            pass


def replace_text_preserve_formatting(shape, placeholder: str, value):
    """
    Replaces placeholder text in a shape while preserving the original formatting.
    Handles both single text (str) and multiple paragraphs (list).
    """
    if not hasattr(shape, "text_frame"):
        return False

    text_frame = shape.text_frame

    # Handle list of paragraphs (multi-paragraph values)
    if isinstance(value, list) and len(text_frame.paragraphs) > 0:
        # Find which paragraph contains the placeholder
        placeholder_para_idx = None
        template_run = None

        for para_idx, paragraph in enumerate(text_frame.paragraphs):
            if placeholder in paragraph.text:
                placeholder_para_idx = para_idx
                # Get formatting from first run
                if paragraph.runs:
                    template_run = paragraph.runs[0]
                break

        if placeholder_para_idx is not None:
            template_paragraph = text_frame.paragraphs[placeholder_para_idx]

            # Clear the placeholder paragraph
            for run in list(template_paragraph.runs):
                run.text = ""

            # Add each paragraph from the list
            for i, para_text in enumerate(value):
                if i == 0:
                    # Use the existing paragraph with the placeholder
                    para = template_paragraph
                else:
                    # Add new paragraph after the current one
                    para = text_frame.add_paragraph()

                # Clear and add text
                for run in list(para.runs):
                    run.text = ""

                run = para.add_run()
                run.text = str(para_text)

                # Apply template formatting
                if template_run:
                    copy_run_formatting(template_run, run)

            return True

        return False

    # Handle single text value (original logic)
    replaced = False

    # Iterate through all paragraphs and runs
    for paragraph in text_frame.paragraphs:
        # Build a list of (run, start_index, end_index) for text search
        run_info = []
        cumulative_length = 0

        for run in paragraph.runs:
            start = cumulative_length
            end = start + len(run.text)
            run_info.append((run, start, end))
            cumulative_length = end

        # Get the full paragraph text
        full_text = paragraph.text

        # Find placeholder in full text
        placeholder_start = full_text.find(placeholder)
        if placeholder_start != -1:
            placeholder_end = placeholder_start + len(placeholder)

            # Find which runs this placeholder spans
            affected_runs = []
            for run, start, end in run_info:
                if not (end <= placeholder_start or start >= placeholder_end):
                    affected_runs.append((run, start, end))

            if affected_runs:
                # Get the first run's formatting as reference
                reference_run = affected_runs[0][0]
                replacement_str = str(value)

                # If placeholder is within a single run (most common case)
                if len(affected_runs) == 1:
                    run, run_start, run_end = affected_runs[0]
                    # Calculate position within the run
                    offset_start = placeholder_start - run_start
                    offset_end = offset_start + len(placeholder)
                    # Replace just the placeholder, keep rest of text
                    run.text = run.text[:offset_start] + replacement_str + run.text[offset_end:]
                    copy_run_formatting(reference_run, run)
                else:
                    # Placeholder spans multiple runs - clear all and put replacement in first
                    for run, _, _ in affected_runs:
                        run.text = ""
                    first_run = affected_runs[0][0]
                    first_run.text = replacement_str
                    copy_run_formatting(reference_run, first_run)

                replaced = True

    return replaced

def generate_presentation(
    template_path: str,
    output_path: str,
    replacements: dict
):

    presentation = Presentation(template_path)
    pattern = r"\{\{(.*?)\}\}"
    shapes_to_remove = []

    for slide in presentation.slides:
        for shape in slide.shapes:
            # 1. Check Alt Text for Image Placeholders
            alt_text = get_shape_alt_text(shape)
            if alt_text:
                matches = re.findall(pattern, alt_text)
                for match in matches:
                    if "image:logo" in match.lower():
                        domain = replacements.get(match)
                        if domain:
                            logo_path = get_company_logo_path(domain)
                            if logo_path:
                                # Add the picture at the same position and size
                                slide.shapes.add_picture(
                                    logo_path,
                                    shape.left,
                                    shape.top,
                                    width=shape.width,
                                    height=shape.height
                                )
                                shapes_to_remove.append((slide, shape))
                    elif "image:topic" in match.lower() or "image:bg" in match.lower():
                        query = replacements.get(match)
                        if query:
                            img_path = get_topic_image_path(query)
                            if img_path:
                                # Add the picture with shape width only (crops to shape height)
                                slide.shapes.add_picture(
                                    img_path,
                                    shape.left,
                                    shape.top,
                                    width=shape.width
                                )
                                shapes_to_remove.append((slide, shape))

            # 2. Check Text for Text Placeholders
            if hasattr(shape, "text"):
                for key, value in replacements.items():
                    # Look for placeholder with or without metadata
                    # e.g., {{key}} or {{key:paragraphs=2}}
                    placeholder_pattern = r"\{\{" + re.escape(key) + r"(?::paragraphs=\d+)?\}\}"
                    match = re.search(placeholder_pattern, shape.text)

                    if match:
                        actual_placeholder = match.group(0)
                        # Handle different value types
                        if isinstance(value, list):
                            # If it's a table (list of lists), skip - handled separately
                            if value and isinstance(value[0], list):
                                continue
                            # For paragraph arrays, pass the list directly
                            # For bullet lists (list of strings), join them
                            # The function will handle both cases
                            replace_text_preserve_formatting(shape, actual_placeholder, value)
                        else:
                            replace_text_preserve_formatting(shape, actual_placeholder, str(value))

            
            # 3. Check for Tables
            if shape.has_table:
                alt_text = get_shape_alt_text(shape)
                if alt_text:
                    matches = re.findall(pattern, alt_text)
                    for match in matches:
                        if "table:" in match.lower():
                            table_data = replacements.get(match)
                            if table_data and isinstance(table_data, list):
                                fill_table(shape.table, table_data)
        
        # Apply custom map highlighting and pointer logic
        apply_map_logic(slide, replacements)

    # Clean up: Remove original placeholder shapes that were replaced by images
    for slide, shape in shapes_to_remove:
        try:
            sp = shape._element
            sp.getparent().remove(sp)
        except Exception as e:
            logging.error(f"Error removing shape: {e}")

    presentation.save(output_path)
    cleanup_temp_images()
    return output_path

def fill_table(table, data):
    """
    Fills a PowerPoint table with data, adding rows as needed and preserving styles.
    Assumes row 1 is header and row 2 is template.
    """
    if not data:
        return

    # 1. Determine number of existing data rows (excluding header)
    # We assume the user has 1 header row and at least 1 template row.
    header_rows = 1
    
    # 2. Fill the first data row (Template row)
    first_row_data = data[0]
    for col_idx, cell_value in enumerate(first_row_data):
        if col_idx < len(table.columns):
            table.cell(header_rows, col_idx).text = str(cell_value)
            # You might want to re-apply style here if .text wipes it
            # But usually it's better to modify the run
    
    # 3. Add and fill additional rows
    for row_data in data[1:]:
        new_row = add_row_to_table(table)
        for col_idx, cell_value in enumerate(row_data):
            if col_idx < len(table.columns):
                new_cell = new_row.cells[col_idx]
                new_cell.text = str(cell_value)
                
                # Copy style from template row (row 1)
                try:
                    template_cell = table.cell(header_rows, col_idx)
                    copy_cell_style(template_cell, new_cell)
                except Exception as e:
                    logging.error(f"Error copying style: {e}")

def add_row_to_table(table):
    """
    Manually adds a row to a table by manipulating the underlying XML.
    python-pptx doesn't have a native table.rows.add() method.
    """
    tbl = table._tbl
    # Create a deep copy of the last row
    last_row_xml = tbl.tr_lst[-1]
    new_row_xml = copy.deepcopy(last_row_xml)
    
    # Clear text in the new row's cells
    for tc in new_row_xml.tc_lst:
        for t in tc.xpath('.//a:t'):
            t.text = ""
            
    # Append the new row XML to the table
    tbl.append(new_row_xml)
    
    # Return the newly created row object
    return table.rows[len(table.rows) - 1]

def copy_cell_style(source_cell, target_cell):
    """
    Copies font styling from one cell to another.
    """
    if not source_cell.text_frame.paragraphs:
        return
    
    source_para = source_cell.text_frame.paragraphs[0]
    target_para = target_cell.text_frame.paragraphs[0]
    
    # Copy paragraph alignment
    target_para.alignment = source_para.alignment
    
    if source_para.runs and target_para.runs:
        source_run = source_para.runs[0]
        target_run = target_para.runs[0]
        
        target_run.font.name = source_run.font.name
        target_run.font.size = source_run.font.size
        target_run.font.bold = source_run.font.bold
        target_run.font.italic = source_run.font.italic
        if source_run.font.color and source_run.font.color.type != 0: # 0 is None
            try:
                target_run.font.color.rgb = source_run.font.color.rgb
            except:
                pass

def attach_placeholder_values(metadata: list[dict], replacements: dict):

    return [
        {
            **slide,
            "placeholders": [
                {
                    **placeholder,
                    "value": replacements.get(placeholder["placeholder"]) or ""
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

def generate_template_thumbnail(template_path: str, output_dir: str = "public/thumbnails"):
    """
    Generates a PNG thumbnail of the first slide of a PPTX template.
    """
    soffice_path = _find_soffice_path()
    if not soffice_path:
        return None

    template_file = Path(template_path).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    
    thumb_path = out_dir / f"{template_file.stem}.png"
    
    # If thumbnail already exists, don't regenerate (unless we want to force)
    if thumb_path.is_file():
        return str(thumb_path)

    # LibreOffice conversion to PNG (exports slides as images)
    subprocess.run(
        [
            soffice_path,
            "--headless",
            "--convert-to",
            "png",
            "--outdir",
            str(out_dir),
            str(template_file),
        ],
        capture_output=True,
        timeout=30
    )
    
    # LibreOffice might name it template_name-0.png or template_name.png
    # Usually it's template_name.png for single slide or if it just does the first
    possible_names = [f"{template_file.stem}.png", f"{template_file.stem}-0.png"]
    for name in possible_names:
        found = out_dir / name
        if found.is_file():
            if name != f"{template_file.stem}.png":
                found.rename(thumb_path)
            return str(thumb_path)

    return None

