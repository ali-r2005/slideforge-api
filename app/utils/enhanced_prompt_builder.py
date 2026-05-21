from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class EnhancedPromptBuilder:
    """
    Builds enhanced prompts that combine user input with structured form data.
    Ensures AI respects the structured parameters as constraints.
    """

    @staticmethod
    def build_prompt_with_form_data(
        user_prompt: str,
        form_data: Dict[str, Any],
        schema: Optional[Dict[str, Any]] = None,
        fields: Optional[list] = None
    ) -> str:
        """
        Combines user prompt with structured form data into a single prompt.

        Args:
            user_prompt: Free-form user input
            form_data: Structured form data from the schema
            schema: Optional schema for context/labels
            fields: List of placeholder fields from template

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
        schema: Optional[Dict[str, Any]] = None
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
                        if col_key != "date" and col_value:
                            # Format column key as label: "morning" → "Morning"
                            col_label = col_key.replace("_", " ").title()
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
    form_data: Optional[Dict[str, Any]] = None,
    schema: Optional[Dict[str, Any]] = None
) -> str:
    """
    Convenience function to build an enhanced prompt.
    """
    if not form_data:
        return user_prompt

    return EnhancedPromptBuilder.build_prompt_with_form_data(
        user_prompt, form_data, schema
    )
