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

The JSON keys MUST exactly match the requested fields.
"""

def build_user_prompt(user_prompt: str, fields: list[dict]):
    fields_text = "\n\n".join(
        [
            "\n".join([
                f"Field: {field['placeholder']}",
                f"- Slide: {field['slide_number']}",
                f"- Type: {field['type']}",
                f"- Max chars: {field['max_chars']}",
                f"- Columns: {field.get('columns', 'N/A')}" if field['type'] == 'table' else ""
            ])
            for field in fields
        ]
    )

    return f"""
Generate presentation content.

Presentation topic:
{user_prompt}

Requirements:

{fields_text}
"""

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
