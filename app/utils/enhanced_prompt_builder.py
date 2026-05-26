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

        # Combine into final prompt
        enhanced_prompt = f"""{user_prompt}

Structured Parameters:
{parameters_section}

IMPORTANT: Treat the above Structured Parameters as strict constraints.
If the user request conflicts with any parameter, prioritize the parameter values.
Use these parameters to ensure consistency in the generated content."""

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

            # Special handling for program_table type
            field_type = field_types.get(key)
            if field_type == "program_table" and isinstance(value, list):
                lines.append(f"- {label}:")
                for row in value:
                    date = row.get("date", "Unknown Date")
                    lines.append(f"  Date: {date}")

                    # Iterate through columns (all keys except 'date')
                    for col_key, col_value in row.items():
                        if col_key == "date" or not col_value:
                            continue

                        col_label = col_key.replace("_", " ").title()

                        # Flatten complex cell structures to array of paragraphs
                        # IMPORTANT: Preserve the order of keys as they come from the frontend
                        if isinstance(col_value, dict):
                            # Extract text from complex structure into paragraph array
                            # Iterate in the order keys appear in the dict (frontend drag-drop order)
                            paragraphs = []

                            # Process keys in their original order (as sent by frontend)
                            for cell_key in col_value.keys():
                                if cell_key == "context_prompt" and col_value.get("context_prompt"):
                                    paragraphs.append(f"Context: {col_value['context_prompt']}")

                                elif cell_key == "team_building" and col_value.get("team_building"):
                                    tb_enriched = EnhancedPromptBuilder._enrich_team_building_data(
                                        col_value["team_building"]
                                    )
                                    if tb_enriched:
                                        paragraphs.append(f"Team Building: {tb_enriched}")

                                elif cell_key == "agency_offer_request" and col_value.get("agency_offer_request"):
                                    offers = col_value["agency_offer_request"]
                                    if isinstance(offers, list):
                                        for offer in offers:
                                            if offer:
                                                paragraphs.append(f"Offer: {offer}")
                                    elif offers:
                                        paragraphs.append(f"Offer: {offers}")

                            # Build array format for AI
                            if paragraphs:
                                paragraphs_str = ", ".join([f'"{p}"' for p in paragraphs])
                                lines.append(f"    {col_label}: [{paragraphs_str}]")
                            else:
                                lines.append(f"    {col_label}: []")
                        else:
                            # Simple string value
                            lines.append(f"    {col_label}: {col_value}")
            else:
                # Format value based on type
                formatted_value = EnhancedPromptBuilder._format_value(value)
                lines.append(f"- {label}: {formatted_value}")

        return "\n".join(lines) if lines else "(No parameters provided)"

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
