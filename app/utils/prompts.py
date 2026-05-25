from typing import Optional, Dict, Any, List

SYSTEM_PROMPT = """
You are an AI assistant specialized in generating PowerPoint presentation content.

Your task is to generate concise, professional, and presentation-ready text.

RULES:
- Return ONLY valid JSON.
- Do not include markdown.
- Do not include explanations.
- Do not include comments.
- Do not add fields that were not requested.
- Keep content concise and presentation-friendly.
- Titles should be short.
- Paragraphs should not be too long.
- Bullet-style wording is preferred.
- For 'image_logo' types: return ONLY the primary domain name (e.g., tesla.com).
- For 'image_topic' types: return a 2-4 word search query for a high-quality stock photo (e.g., 'modern boardroom', 'team high five', 'tangier morocco').
- For 'table' types: return a LIST of OBJECTS where each object uses column names as keys.
  Example: [{"Name": "John", "Email": "john@example.com"}, {"Name": "Jane", "Email": "jane@example.com"}]
  Use the exact column names provided in the field description.
- For fields with 'Paragraphs: 2+': return a LIST of strings, one per paragraph. Example: ["First paragraph text.", "Second paragraph text."]
  Each paragraph should be 1-2 sentences maximum.
- When you see requests for arrays (marked with "Return as:" in the prompt), ALWAYS return the field as an array, even if there's only one item.

The JSON keys MUST exactly match the requested fields.
"""

def build_user_prompt(user_prompt: str, fields: List[Dict[str, Any]], template_metadata: Optional[Dict[str, Any]] = None) -> str:
    if template_metadata is None:
        template_metadata = {}

    # Build template-level instructions
    template_instructions = ""
    if template_metadata:
        system_instr = template_metadata.get("system_instructions", "")
        tone = template_metadata.get("tone", "")

        if system_instr or tone:
            template_instructions = "\n\nTemplate-specific guidelines:\n"
            if system_instr:
                template_instructions += f"- {system_instr}\n"
            if tone:
                template_instructions += f"- Tone: {tone}\n"

    # Build field requirements
    fields_text = "\n\n".join(
        [
            "\n".join(filter(None, [
                f"Field: {field['placeholder']}",
                f"- Slide: {field['slide_number']}",
                f"- Type: {field['type']}",
                f"- Max chars: {field['max_chars']}",
                f"- Paragraphs: {field.get('paragraphs', 1)}" if field.get('paragraphs', 1) > 1 else None,
                f"- Columns: {field.get('columns', 'N/A')}" if field['type'] == 'table' else None,
                f"- Column headers: {format_table_columns_for_prompt(field.get('column_headers', []))}" if field['type'] == 'table' and field.get('column_headers') else None,
                get_field_instruction_section(template_metadata, field['placeholder'])
            ]))
            for field in fields
        ]
    )

    return f"""
Generate presentation content.

Presentation topic:
{user_prompt}
{template_instructions}

Requirements:

{fields_text}
"""


def get_field_instruction_section(template_metadata: Dict[str, Any], field_name: str) -> Optional[str]:
    """Helper to get field-specific instructions from metadata, including formatting conventions."""
    if not template_metadata:
        return None

    field_instructions = template_metadata.get("field_instructions", {})
    field_meta = field_instructions.get(field_name, {})

    if not isinstance(field_meta, dict):
        if isinstance(field_meta, str):
            return f"- Special instructions: {field_meta}"
        return None

    sections = []

    # Handle table-specific properties
    if field_meta.get("type") == "table" or field_meta.get("rows") or field_meta.get("column_names"):
        rows = field_meta.get("rows")
        column_names = field_meta.get("column_names")

        if rows:
            sections.append(f"- Number of rows: {rows}")
        if column_names:
            formatted_cols = format_table_columns_for_prompt(column_names)
            sections.append(f"- Columns: {formatted_cols}")

    # Handle general instructions
    instructions = field_meta.get("instructions", "")
    if instructions:
        sections.append(f"- Special instructions: {instructions}")

    # Handle formatting conventions
    conventions = field_meta.get("formatting_conventions")
    if conventions:
        sections.append(f"- Formatting conventions for '{field_name}':")
        for convention in conventions:
            instruction = convention.get("instruction", "")
            if instruction:
                sections.append(f"  - {instruction}")

    return "\n".join(sections) if sections else None

def format_table_columns_for_prompt(column_headers: List[str]) -> str:
    """Formats column headers for AI prompt."""
    if not column_headers:
        return ""
    return ", ".join(f"'{h}'" for h in column_headers)

def build_correction_prompt(original_prompt: str, invalid_content: str, validation_error: str) -> str:
    return f"""
Your previous response was invalid.

Validation errors:
{validation_error}

Previous response:
{invalid_content}

Return corrected JSON only.

{original_prompt}
"""
