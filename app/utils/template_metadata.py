import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def load_template_metadata(template_name: str, templates_dir: str = "templates") -> dict:
    """
    Loads template metadata from a JSON file.
    Returns an empty dict if metadata file doesn't exist.

    Example:
    - template_name: "template3"
    - looks for: "templates/template3.json"
    """
    metadata_path = Path(templates_dir) / f"{template_name}.json"

    if not metadata_path.is_file():
        return {
            "name": template_name,
            "description": "No description provided",
            "system_instructions": "",
            "field_instructions": {},
            "tone": "professional",
            "constraints": {}
        }

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        logger.info(f"Loaded metadata for template: {template_name}")
        return metadata
    except Exception as e:
        logger.warning(f"Failed to load metadata for {template_name}: {e}")
        return {}


def get_field_instruction(metadata: dict, field_name: str) -> str:
    """
    Retrieves specific instructions for a field from template metadata.

    Args:
        metadata: Template metadata dict
        field_name: Placeholder field name (e.g., "destination_paragraph")

    Returns:
        Instruction string or empty string if not found
    """
    field_instructions = metadata.get("field_instructions", {})
    field_meta = field_instructions.get(field_name, {})

    if isinstance(field_meta, dict):
        return field_meta.get("instructions", "")
    elif isinstance(field_meta, str):
        return field_meta

    return ""


def get_table_row_count(metadata: dict, field_name: str) -> int:
    """
    Gets the expected number of rows for a table field.

    Args:
        metadata: Template metadata dict
        field_name: Table field name (e.g., "budget_table:budget")

    Returns:
        Number of rows or 0 if not specified
    """
    field_instructions = metadata.get("field_instructions", {})
    field_meta = field_instructions.get(field_name, {})

    if isinstance(field_meta, dict):
        return field_meta.get("rows", 0)

    return 0


def get_system_instructions(metadata: dict) -> str:
    """
    Gets template-level system instructions for the AI.
    """
    return metadata.get("system_instructions", "")


def get_tone(metadata: dict) -> str:
    """
    Gets the desired tone for content generation.
    """
    return metadata.get("tone", "professional")
