import re


def extract_placeholder_metadata(placeholder_text: str):
    """
    Extracts placeholder name and metadata from strings like:
    - "summary_paragraph"
    - "summary_paragraph:paragraphs=2"
    - "table:users"
    - "image:logo"

    Returns dict with 'name' and optional 'paragraphs' key.
    """
    text = placeholder_text.strip()

    # Check if it has :paragraphs=N metadata
    paragraphs_match = re.search(r':paragraphs=(\d+)$', text)
    if paragraphs_match:
        # Extract the number and remove it from the text
        paragraphs_count = int(paragraphs_match.group(1))
        name = text[:paragraphs_match.start()]
    else:
        paragraphs_count = 1
        name = text

    return {"name": name, "paragraphs": paragraphs_count}


def infer_placeholder_type(field_name: str):
    field_name = field_name.lower()

    if "title" in field_name:
        return "title"

    if "summary" in field_name or "paragraph" in field_name or "description" in field_name:
        return "paragraph"

    if "bullet" in field_name or "list" in field_name:
        return "bullet_list"

    if "subtitle" in field_name:
        return "subtitle"

    if "image:logo" in field_name:
        return "image_logo"

    if "image:topic" in field_name or "image:bg" in field_name or "image:photo" in field_name:
        return "image_topic"

    if "table:" in field_name:
        return "table"

    return "text"

