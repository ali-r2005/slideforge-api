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
- For 'table' types: return a LIST of LISTS. Each inner list represents a row and must have exactly the number of columns requested. Do not include the header row.
- For fields with 'Paragraphs: 2+': return a LIST of strings, one per paragraph. Example: ["First paragraph text.", "Second paragraph text."]
  Each paragraph should be 1-2 sentences maximum.

The JSON keys MUST exactly match the requested fields.
"""

def build_user_prompt(user_prompt: str, fields: list[dict], template_metadata: dict = None):
    if template_metadata is None:
        template_metadata = {}

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
                get_field_instruction_section(template_metadata, field['placeholder'])
            ]))
            for field in fields
        ]
    )

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

    return f"""
Generate presentation content.

Presentation topic:
{user_prompt}

Requirements:

{fields_text}
{template_instructions}
"""


def get_field_instruction_section(template_metadata: dict, field_name: str) -> str:
    """Helper to get field-specific instructions from metadata."""
    if not template_metadata:
        return None

    field_instructions = template_metadata.get("field_instructions", {})
    field_meta = field_instructions.get(field_name, {})

    if isinstance(field_meta, dict):
        instructions = field_meta.get("instructions", "")
        if instructions:
            return f"- Special instructions: {instructions}"
    elif isinstance(field_meta, str):
        return f"- Special instructions: {field_meta}"

    return None

def build_correction_prompt(original_prompt: str, invalid_content: str, validation_error: str):
    return f"""
Your previous response was invalid.

Validation errors:
{validation_error}

Previous response:
{invalid_content}

Return corrected JSON only.

{original_prompt}
"""
