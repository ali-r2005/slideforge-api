from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from app.utils.placeholder import infer_placeholder_type, extract_placeholder_metadata
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
                            # Extract header names from the first row
                            table = shape.table
                            column_headers = extract_table_headers(table)

                            slide_info["placeholders"].append({
                                "placeholder": placeholder_name,
                                "slide_number": slide_index + 1,
                                "shape_index": shape_index,
                                "type": "table",
                                "columns": len(table.columns),
                                "column_headers": column_headers,
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


def apply_formatted_text(paragraph, text: str, parser, base_font_props: Optional[Dict[str, Any]] = None) -> None:
    """
    Apply text with parsed marker formatting to a PowerPoint paragraph.
    Preserves the placeholder's base font and applies marker-based formatting only to marked text.

    Args:
        paragraph: The paragraph to add formatted text to
        text: Text potentially containing markers like $$marker$$content$$marker$$
        parser: MarkerParser instance with field-specific conventions
        base_font_props: Optional base font properties to apply to all runs
    """
    # Extract base font properties from the first existing run if not provided
    if not base_font_props:
        base_font_props = {}
        if paragraph.runs:
            first_run = paragraph.runs[0]
            base_font_props = {
                "size": first_run.font.size,
                "bold": first_run.font.bold,
                "italic": first_run.font.italic,
                "color": first_run.font.color.rgb if hasattr(first_run.font.color, 'rgb') else None
            }

    runs_data = parser.get_pptx_runs(text)

    # Clear existing runs
    for run in list(paragraph.runs):
        run.text = ""

    for run_data in runs_data:
        run = paragraph.add_run()
        run.text = run_data["text"]

        # Start with base font properties (placeholder font)
        if base_font_props.get("size"):
            run.font.size = base_font_props["size"]
        if base_font_props.get("bold") is not None:
            run.font.bold = base_font_props["bold"]
        if base_font_props.get("italic") is not None:
            run.font.italic = base_font_props["italic"]
        if base_font_props.get("color"):
            run.font.color.rgb = base_font_props["color"]

        # Override with marker-specific formatting (only if marker style is defined)
        # Color from marker overrides placeholder color
        if run_data.get("color"):
            try:
                r = int(run_data["color"][0:2], 16)
                g = int(run_data["color"][2:4], 16)
                b = int(run_data["color"][4:6], 16)
                run.font.color.rgb = RGBColor(r, g, b)
            except (ValueError, TypeError):
                pass

        # Bold from marker overrides placeholder bold (only if marker specifies bold)
        if run_data.get("bold"):
            run.font.bold = True

        # Italic from marker overrides placeholder italic (only if marker specifies italic)
        if run_data.get("italic"):
            run.font.italic = True

        # Font size from marker overrides placeholder size (only if marker specifies size)
        if run_data.get("font_size"):
            try:
                run.font.size = Pt(int(run_data["font_size"]))
            except (ValueError, TypeError):
                pass


def replace_text_preserve_formatting(
    shape,
    placeholder: str,
    value,
    field_placeholder: Optional[str] = None,
    template_metadata: Optional[Dict[str, Any]] = None
):
    """
    Replaces placeholder text in a shape while preserving the original formatting.
    Optionally applies field-specific formatting conventions based on markers.

    Args:
        shape: The PowerPoint shape containing the placeholder
        placeholder: The placeholder text to find and replace
        value: The replacement value (str or list of str)
        field_placeholder: The field name for marker parsing (e.g., "program_schedule")
        template_metadata: Template metadata with formatting_conventions
    """
    if not hasattr(shape, "text_frame"):
        return False

    text_frame = shape.text_frame

    # If field context provided, use marker-based formatting
    if field_placeholder and template_metadata:
        from app.utils.marker_parser import MarkerParser

        parser = MarkerParser.for_field(template_metadata, field_placeholder)

        # Handle list of values
        if isinstance(value, list):
            # Find which paragraph contains the placeholder
            placeholder_para_idx = None

            for para_idx, paragraph in enumerate(text_frame.paragraphs):
                if placeholder in paragraph.text:
                    placeholder_para_idx = para_idx
                    break

            if placeholder_para_idx is not None:
                template_paragraph = text_frame.paragraphs[placeholder_para_idx]

                # Add each value with formatting
                for i, val in enumerate(value):
                    if i == 0:
                        para = template_paragraph
                    else:
                        para = text_frame.add_paragraph()

                    # Apply formatted text
                    apply_formatted_text(para, str(val), parser)

                return True
        else:
            # Handle single value with marker formatting - use same logic as regular path
            # but apply formatting from parser
            replaced = False

            for paragraph in text_frame.paragraphs:
                # Build list of (run, start_index, end_index) for text search
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
                        # Get formatting info from parser
                        parsed_runs_data = parser.get_pptx_runs(str(value))
                        replacement_str = str(value)

                        # If placeholder is within a single run (most common case)
                        if len(affected_runs) == 1:
                            run, run_start, run_end = affected_runs[0]
                            # Calculate position within the run
                            offset_start = placeholder_start - run_start
                            offset_end = offset_start + len(placeholder)
                            # Replace just the placeholder, keep rest of text
                            run.text = run.text[:offset_start] + replacement_str + run.text[offset_end:]

                            # Apply formatting from parsed runs if available
                            if len(parsed_runs_data) > 0:
                                run_data = parsed_runs_data[0]
                                if run_data.get("color"):
                                    try:
                                        r = int(run_data["color"][0:2], 16)
                                        g = int(run_data["color"][2:4], 16)
                                        b = int(run_data["color"][4:6], 16)
                                        run.font.color.rgb = RGBColor(r, g, b)
                                    except (ValueError, TypeError):
                                        pass
                                if run_data.get("bold"):
                                    run.font.bold = True
                                if run_data.get("italic"):
                                    run.font.italic = True
                        else:
                            # Placeholder spans multiple runs - clear all and put replacement in first
                            for run, _, _ in affected_runs:
                                run.text = ""
                            first_run = affected_runs[0][0]
                            first_run.text = replacement_str

                            # Apply formatting
                            if len(parsed_runs_data) > 0:
                                run_data = parsed_runs_data[0]
                                if run_data.get("color"):
                                    try:
                                        r = int(run_data["color"][0:2], 16)
                                        g = int(run_data["color"][2:4], 16)
                                        b = int(run_data["color"][4:6], 16)
                                        first_run.font.color.rgb = RGBColor(r, g, b)
                                    except (ValueError, TypeError):
                                        pass
                                if run_data.get("bold"):
                                    first_run.font.bold = True
                                if run_data.get("italic"):
                                    first_run.font.italic = True

                        replaced = True

            return replaced

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
    replacements: dict,
    template_metadata: Optional[Dict[str, Any]] = None
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
                        # Extract field placeholder name (without :metadata)
                        field_placeholder = key.split(":")[0]

                        # Handle different value types
                        if isinstance(value, list):
                            # If it's a table (list of lists), skip - handled separately
                            if value and isinstance(value[0], list):
                                continue
                            # For paragraph arrays, pass the list directly
                            # For bullet lists (list of strings), join them
                            # The function will handle both cases
                            replace_text_preserve_formatting(
                                shape,
                                actual_placeholder,
                                value,
                                field_placeholder=field_placeholder,
                                template_metadata=template_metadata
                            )
                        else:
                            replace_text_preserve_formatting(
                                shape,
                                actual_placeholder,
                                str(value),
                                field_placeholder=field_placeholder,
                                template_metadata=template_metadata
                            )

            
            # 3. Check for Tables
            if shape.has_table:
                alt_text = get_shape_alt_text(shape)
                if alt_text:
                    matches = re.findall(pattern, alt_text)
                    for match in matches:
                        if "table:" in match.lower():
                            # Extract just the table name (without metadata)
                            metadata = extract_placeholder_metadata(match)
                            table_name = metadata["name"]

                            table_data = replacements.get(table_name)
                            if table_data and isinstance(table_data, list):
                                # Extract column headers from the table
                                column_headers = extract_table_headers(shape.table)
                                fill_table(
                                    shape.table,
                                    table_data,
                                    column_headers=column_headers,
                                    field_placeholder=table_name,
                                    template_metadata=template_metadata
                                )
        
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

def extract_table_headers(table):
    """
    Extracts header names from the first row of a table.
    Returns a list of header names.
    """
    if len(table.rows) < 1:
        return []

    headers = []
    header_row = table.rows[0]

    for cell in header_row.cells:
        # Extract text from the cell
        cell_text = cell.text.strip()
        headers.append(cell_text)

    return headers


def extract_template_row_formatting(table):
    """
    Extracts formatting information from the template row (second row, index 1).
    Returns a list of formatting dicts for each column.
    """
    if len(table.rows) < 2:
        return {}

    template_row = table.rows[1]
    formatting = {}

    for col_idx, cell in enumerate(template_row.cells):
        if cell.text_frame.paragraphs:
            para = cell.text_frame.paragraphs[0]
            if para.runs:
                run = para.runs[0]
                formatting[col_idx] = {
                    "font_name": run.font.name,
                    "font_size": run.font.size,
                    "font_bold": run.font.bold,
                    "font_italic": run.font.italic,
                    "font_underline": run.font.underline,
                    "alignment": para.alignment
                }

    return formatting


def fill_table(table, data, column_headers=None, field_placeholder=None, template_metadata=None):
    """
    Fills a PowerPoint table with data, adding rows as needed and preserving styles.

    Supports two data formats:
    1. List of dicts: [{"Name": "John", "Email": "john@example.com"}, ...]
    2. List of lists: [["John", "john@example.com"], ...]

    Assumes row 0 is header and row 1 is template row.

    Args:
        table: The PowerPoint table to fill
        data: List of row data (dicts or lists)
        column_headers: Optional list of column header names
        field_placeholder: Optional field name for marker-based formatting
        template_metadata: Optional template metadata with formatting conventions
    """
    if not data:
        return

    header_rows = 1  # Header is at row 0, template is at row 1

    # Determine data format and convert if needed
    if data and isinstance(data[0], dict):
        # Data is list of objects
        rows_to_fill = data
        is_object_format = True
    elif data and isinstance(data[0], list):
        # Data is list of lists
        rows_to_fill = data
        is_object_format = False
    else:
        return

    # Fill each row
    for row_idx, row_data in enumerate(rows_to_fill):
        if row_idx == 0:
            # Use the template row (row 1) for first data
            current_row = table.rows[header_rows]
        else:
            # Add new row - automatically copies template formatting via XML
            current_row = add_row_to_table(table)

        # Fill cells in the row
        for col_idx in range(len(table.columns)):
            if col_idx >= len(table.columns):
                break

            cell = current_row.cells[col_idx]

            # Get the cell value based on data format
            if is_object_format:
                # Get value from dict using header name
                if column_headers and col_idx < len(column_headers):
                    header_name = column_headers[col_idx]
                    cell_value = row_data.get(header_name, "")
                else:
                    cell_value = ""
            else:
                # Get value from list
                if col_idx < len(row_data):
                    cell_value = row_data[col_idx]
                else:
                    cell_value = ""

            # IMPORTANT: Replace text in existing runs to preserve formatting
            # Do NOT use cell.text = ... as it clears all formatting
            # Pass cell_value directly (string or array) - function handles both
            set_cell_text_preserve_formatting(
                cell,
                cell_value,
                field_placeholder=field_placeholder,
                template_metadata=template_metadata
            )

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

def set_cell_text_preserve_formatting(
    cell,
    text,
    field_placeholder: Optional[str] = None,
    template_metadata: Optional[Dict[str, Any]] = None
):
    """
    Sets cell text while preserving all existing formatting.
    Handles both strings and arrays of strings (with line breaks between items).
    Applies marker-based formatting if template metadata is provided.

    Args:
        cell: The table cell to update
        text: Text or array of text to insert
        field_placeholder: Optional field name for marker-based formatting
        template_metadata: Optional template metadata with formatting conventions

    IMPORTANT: Do NOT use cell.text = ... because it clears formatting.
    Instead, replace text in the existing runs while keeping their properties.
    """
    if not cell.text_frame.paragraphs:
        return

    text_frame = cell.text_frame

    # Convert text to list if it's a string
    if isinstance(text, str):
        paragraphs_to_add = [text]
    elif isinstance(text, list):
        # Filter out empty strings from array
        paragraphs_to_add = [str(item) for item in text if item]
    else:
        paragraphs_to_add = [str(text)]

    if not paragraphs_to_add:
        # If no content, clear the cell
        for paragraph in text_frame.paragraphs:
            for run in paragraph.runs:
                run.text = ""
        return

    # Create parser for marker-based formatting if metadata provided
    parser = None
    if field_placeholder and template_metadata:
        from app.utils.marker_parser import MarkerParser
        parser = MarkerParser.for_field(template_metadata, field_placeholder)

    # Extract base font properties and paragraph formatting from the first paragraph once
    # This will be applied to all paragraphs in the array
    first_paragraph = text_frame.paragraphs[0]
    base_font_props = {}
    base_paragraph_props = {
        "alignment": first_paragraph.alignment,  # Center, left, right, justify
        "level": first_paragraph.level,           # Indentation level
        "space_before": first_paragraph.space_before,
        "space_after": first_paragraph.space_after,
        "line_spacing": first_paragraph.line_spacing
    }

    if first_paragraph.runs:
        first_run = first_paragraph.runs[0]
        base_font_props = {
            "size": first_run.font.size,
            "bold": first_run.font.bold,
            "italic": first_run.font.italic,
            "color": first_run.font.color.rgb if hasattr(first_run.font.color, 'rgb') else None
        }

    # Set text to the first paragraph with formatting
    if parser:
        # Clear existing runs first
        for run in first_paragraph.runs:
            run.text = ""
        # Apply formatted text with markers, passing base font to all paragraphs
        apply_formatted_text(first_paragraph, paragraphs_to_add[0], parser, base_font_props)
    else:
        # Plain text without marker formatting
        if first_paragraph.runs:
            first_paragraph.runs[0].text = paragraphs_to_add[0]
            for run in first_paragraph.runs[1:]:
                run.text = ""
        else:
            run = first_paragraph.add_run()
            run.text = paragraphs_to_add[0]

    # If we have multiple paragraphs (array), add spacing after first paragraph for visibility
    if len(paragraphs_to_add) > 1:
        if base_paragraph_props["space_after"] is not None and base_paragraph_props["space_after"] > Pt(0):
            first_paragraph.space_after = base_paragraph_props["space_after"]
        else:
            # Add visible spacing between array items in table cells
            first_paragraph.space_after = Pt(6)

    # Add remaining paragraphs for array items (creates line breaks)
    for idx, paragraph_text in enumerate(paragraphs_to_add[1:]):
        # Add a new paragraph
        new_paragraph = text_frame.add_paragraph()

        # Apply paragraph formatting (alignment, spacing, etc.)
        if base_paragraph_props["alignment"] is not None:
            new_paragraph.alignment = base_paragraph_props["alignment"]
        if base_paragraph_props["level"] is not None:
            new_paragraph.level = base_paragraph_props["level"]
        if base_paragraph_props["space_before"] is not None:
            new_paragraph.space_before = base_paragraph_props["space_before"]

        # Add explicit spacing after paragraphs for visibility in table cells
        # Use the template's space_after if set, otherwise add 6pt spacing
        if base_paragraph_props["space_after"] is not None and base_paragraph_props["space_after"] > Pt(0):
            new_paragraph.space_after = base_paragraph_props["space_after"]
        else:
            # Add visible spacing between array items in table cells
            new_paragraph.space_after = Pt(6)

        if base_paragraph_props["line_spacing"] is not None:
            new_paragraph.line_spacing = base_paragraph_props["line_spacing"]

        if parser:
            # Apply formatted text with marker parsing, using same base font for all paragraphs
            apply_formatted_text(new_paragraph, paragraph_text, parser, base_font_props)
        else:
            # Plain text
            new_paragraph.text = paragraph_text
            # Preserve formatting from the first paragraph if possible
            if first_paragraph.runs:
                for run in new_paragraph.runs:
                    first_run = first_paragraph.runs[0]
                    # Copy font properties
                    if first_run.font.size:
                        run.font.size = first_run.font.size
                    if first_run.font.bold is not None:
                        run.font.bold = first_run.font.bold
                    if first_run.font.italic is not None:
                        run.font.italic = first_run.font.italic


def apply_cell_formatting(cell, formatting):
    """
    Applies formatting to a cell based on a formatting dict.
    """
    if not cell.text_frame.paragraphs:
        return

    para = cell.text_frame.paragraphs[0]

    if para.runs:
        run = para.runs[0]
        font = run.font

        if formatting.get("font_name"):
            font.name = formatting["font_name"]
        if formatting.get("font_size"):
            font.size = formatting["font_size"]
        if formatting.get("font_bold") is not None:
            font.bold = formatting["font_bold"]
        if formatting.get("font_italic") is not None:
            font.italic = formatting["font_italic"]
        if formatting.get("font_underline") is not None:
            font.underline = formatting["font_underline"]

    if formatting.get("alignment") is not None:
        para.alignment = formatting["alignment"]


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

