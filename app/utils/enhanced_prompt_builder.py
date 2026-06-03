from typing import Dict, Any, Optional
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class EnhancedPromptBuilder:
    """
    Builds enhanced prompts that combine user input with structured form data.
    Ensures AI respects the structured parameters as constraints.
    """

    @staticmethod
    def _enrich_team_building_data(team_building_value: Any) -> Optional[str]:
        """
        Fetch team building activity details from DB and format for prompt.

        Args:
            team_building_value: Team building name/ID or dict from form

        Returns:
            Formatted team building description with action, objectives, experience, les_plus
        """
        if not team_building_value:
            return None

        # Extract team building name if it's a dict
        tb_name = team_building_value
        if isinstance(team_building_value, dict):
            tb_name = team_building_value.get("name")

        if not tb_name:
            return None

        try:
            # Load team building database
            db_path = Path("DB/tb.json")
            if not db_path.exists():
                return None

            with open(db_path, "r", encoding="utf-8") as f:
                activities = json.load(f)

            # Find matching activity (case-insensitive)
            activity = None
            for act in activities:
                if act.get("name", "").lower() == str(tb_name).lower():
                    activity = act
                    break

            if not activity:
                return None

            # Format enriched data
            parts = [f"Team Building: {activity.get('name', tb_name)}"]

            if activity.get("objectives"):
                objs = ", ".join(activity["objectives"])
                parts.append(f"Objectives: {objs}")

            if activity.get("experience"):
                exp = ", ".join(activity["experience"])
                parts.append(f"Experience: {exp}")

            if activity.get("les_plus"):
                benefits = ", ".join(activity["les_plus"])
                parts.append(f"Benefits: {benefits}")

            return " | ".join(parts)

        except Exception as e:
            logger.warning(f"Failed to enrich team building data: {e}")
            return None

    @staticmethod
    def build_prompt_with_form_data(
        user_prompt: str,
        form_data: Dict[str, Any],
        schema: Dict[str, Any] | None = None
    ) -> str:
        """
        Combines user prompt with structured form data into a single prompt.

        Args:
            user_prompt: Free-form user input
            form_data: Structured form data from the schema
            schema: Optional schema for context/labels

        Returns:
            Enhanced prompt to send to AI
        """
        if not form_data:
            return user_prompt

        # Build the parameter section
        parameters_section = EnhancedPromptBuilder._build_parameters_section(
            form_data, schema
        )

        # Build output format instructions for table parts
        output_instructions = EnhancedPromptBuilder._build_table_output_instructions(schema)

        # Combine into final prompt
        enhanced_prompt = f"""{user_prompt}

Structured Parameters:
{parameters_section}

IMPORTANT: Treat the above Structured Parameters as strict constraints.
If the user request conflicts with any parameter, prioritize the parameter values.
Use these parameters to ensure consistency in the generated content.{output_instructions}"""

        return enhanced_prompt.strip()

    @staticmethod
    def _build_parameters_section(
        form_data: Dict[str, Any],
        schema: Dict[str, Any] | None = None
    ) -> str:
        """
        Builds the structured parameters section of the prompt.
        """
        lines = []

        # Create a mapping of field names to labels and types for better readability
        field_labels = {}
        field_types = {}
        if schema:
            for field in schema.get("fields", []):
                field_name = field.get("name")
                label = field.get("label", field_name)
                field_labels[field_name] = label
                field_types[field_name] = field.get("type")

        # Build parameter lines
        for key, value in sorted(form_data.items()):
            if value is None or value == "" or value == []:
                continue

            # Get label if available
            label = field_labels.get(key, EnhancedPromptBuilder._format_label(key))

            # Special handling for table type
            field_type = field_types.get(key)
            if (field_type == "table" or (field_type and value)) and isinstance(value, list):
                lines.append(f"- {label}:")
                for row in value:
                    date = row.get("date", "Unknown Date")
                    lines.append(f"  Date: {date}")

                    # Iterate through columns (all keys except 'date')
                    for col_key, col_value in row.items():
                        if col_key == "date" or not col_value:
                            continue

                        col_label = col_key.replace("_", " ").title()

                        # Format cell data for AI - pass actual arrays/values as-is
                        if isinstance(col_value, dict):
                            cell_parts = []

                            # Get the field definition to find cell_structure
                            field_def = None
                            if schema:
                                for f in schema.get("fields", []):
                                    if f.get("name") == key:
                                        field_def = f
                                        break

                            # Get cell_structure to determine dynamic parts
                            cell_struct = field_def.get("cell_structure", {}) if field_def else {}
                            parts_config = cell_struct.get("parts", [])

                            # Process dynamic parts in the order they appear in col_value (respects user's drag-and-drop reordering)
                            # The frontend sends parts in the order the user set via drag-and-drop, so we iterate through col_value.keys()
                            part_order = list(col_value.keys()) if isinstance(col_value, dict) else []
                            for part_name in part_order:
                                part = next((p for p in parts_config if p.get("name") == part_name), None)
                                if not part:
                                    continue

                                part_type = part.get("type")
                                part_value = col_value.get(part_name)

                                if not part_value:
                                    continue

                                if part_type in ("array-textarea", "text", "textarea"):
                                    # Array-like parts
                                    if part_type == "array-textarea" and isinstance(part_value, list):
                                        clean_items = [str(p).strip() for p in part_value if p and str(p).strip()]
                                        if clean_items:
                                            items_str = ", ".join([f'"{item}"' for item in clean_items])
                                            cell_parts.append(f'"{part_name}": [{items_str}]')
                                    else:
                                        # Single text value
                                        cell_parts.append(f'"{part_name}": "{str(part_value).strip()}"')

                                elif part_type == "select":
                                    # Select parts - enrich from database if available
                                    if isinstance(part_value, dict):
                                        # it shuld be change it should handele to retrive the data that from the file that the user select it
                                        enriched = EnhancedPromptBuilder._enrich_team_building_data(part_value)
                                        if enriched:
                                            cell_parts.append(f'"{part_name}": "{enriched}"')

                            if cell_parts:
                                cell_str = ", ".join(cell_parts)
                                lines.append(f"    {col_label}: {{{cell_str}}}")
                            else:
                                lines.append(f"    {col_label}: {{}}")
                        else:
                            # Simple string value
                            lines.append(f"    {col_label}: {col_value}")
            else:
                # Format value based on type
                formatted_value = EnhancedPromptBuilder._format_value(value)
                lines.append(f"- {label}: {formatted_value}")

        return "\n".join(lines) if lines else "(No parameters provided)"

    @staticmethod
    def _build_table_output_instructions(schema: Dict[str, Any] | None = None) -> str:
        """
        Build instructions for AI about table cell output format and order.
        Tells AI to respect the order of properties from input in the output array.
        """
        if not schema:
            return ""

        instructions = []

        # Find table fields with cell_structure
        for field in schema.get("fields", []):
            if field.get("type") != "table" and not field.get("cell_structure"):
                continue

            cell_struct = field.get("cell_structure", {})
            if not cell_struct.get("parts"):
                continue

            field_label = field.get("label", field.get("name"))
            instructions.append(
                f"\nFor {field_label}: Return cell content as a flat JSON array of strings. "
                f"IMPORTANT: Respect the property order from the input - return output array in the same property order."
            )

        return "".join(instructions) if instructions else ""

    @staticmethod
    def _format_label(field_name: str) -> str:
        """Convert field name to readable label."""
        return field_name.replace("_", " ").title()

    @staticmethod
    def _format_value(value: Any) -> str:
        """Format a value for display in the prompt."""
        if isinstance(value, bool):
            return "Yes" if value else "No"
        elif isinstance(value, list):
            return ", ".join(str(v) for v in value)
        elif isinstance(value, dict):
            # Handle date ranges
            if "start" in value and "end" in value:
                return f"{value['start']} to {value['end']}"
            return str(value)
        else:
            return str(value)

    @staticmethod
    def merge_with_existing_prompt(
        enhanced_prompt: str,
        current_prompt: Optional[str] = None
    ) -> str:
        """
        Merges enhanced prompt with any existing prompt text.
        Useful for combining with template-level instructions.
        """
        if not current_prompt:
            return enhanced_prompt

        return f"{current_prompt}\n\n{enhanced_prompt}"


def build_enhanced_prompt(
    user_prompt: str,
    form_data: Dict[str, Any] | None = None,
    schema: Dict[str, Any] | None = None
) -> str:
    """
    Convenience function to build an enhanced prompt.
    """
    if not form_data:
        return user_prompt

    return EnhancedPromptBuilder.build_prompt_with_form_data(
        user_prompt, form_data, schema
    )
