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
        schema: Dict[str, Any] | None = None,
        fields: list | None = None,
        template_metadata: Dict[str, Any] | None = None
    ) -> str:
        """
        Combines user prompt with structured form data into a single prompt.

        Args:
            user_prompt: Free-form user input
            form_data: Structured form data from the schema
            schema: Optional schema for context/labels
            fields: List of placeholder fields from template
            template_metadata: Optional template metadata with formatting conventions

        Returns:
            Enhanced prompt to send to AI
        """
        if not form_data:
            return user_prompt

        # Build the parameter section
        parameters_section = EnhancedPromptBuilder._build_parameters_section(
            form_data, schema
        )

        # Build field-specific formatting instructions
        formatting_section = EnhancedPromptBuilder._build_field_specific_formatting(
            fields, template_metadata
        )

        # Combine into final prompt
        enhanced_prompt = f"""{user_prompt}

Structured Parameters:
{parameters_section}
{formatting_section}

IMPORTANT: Treat the above Structured Parameters as strict constraints.
If the user request conflicts with any parameter, prioritize the parameter values.
Use these parameters to ensure consistency in the generated content."""

        return enhanced_prompt.strip()

    @staticmethod
    def _build_field_specific_formatting(
        fields: list | None = None,
        template_metadata: Dict[str, Any] | None = None
    ) -> str:
        """
        Builds formatting instructions only for fields that have conventions defined.

        Each field can have its own formatting_conventions that apply only to that field.
        """
        if not fields or not template_metadata:
            return ""

        field_instructions = template_metadata.get("field_instructions", {})
        formatting_lines = []

        for field in fields:
            placeholder = field.get("placeholder")
            if not placeholder:
                continue

            field_meta = field_instructions.get(placeholder, {})

            if isinstance(field_meta, dict):
                conventions = field_meta.get("formatting_conventions")
            else:
                conventions = None

            if conventions:
                if not formatting_lines:
                    formatting_lines.append("\nFormatting Instructions:")

                formatting_lines.append(f"\nFor '{placeholder}' field:")
                for convention in conventions:
                    instruction = convention.get("instruction", "")
                    if instruction:
                        formatting_lines.append(f"  - {instruction}")

        return "\n".join(formatting_lines) if formatting_lines else ""

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

                        # Flatten complex cell structures to simple text
                        if isinstance(col_value, dict):
                            # Extract text from complex structure if present
                            cell_text_parts = []
                            if col_value.get("context_prompt"):
                                cell_text_parts.append(col_value["context_prompt"])
                            if col_value.get("agency_offer_request"):
                                cell_text_parts.append(col_value["agency_offer_request"])
                            if col_value.get("team_building"):
                                tb = col_value["team_building"]
                                if isinstance(tb, dict):
                                    tb_name = tb.get("name", "")
                                    if tb_name:
                                        cell_text_parts.append(f"Team Building: {tb_name}")
                                elif isinstance(tb, str) and tb:
                                    cell_text_parts.append(f"Team Building: {tb}")

                            # Combine all parts into a single string
                            combined_text = " | ".join(cell_text_parts) if cell_text_parts else ""
                            lines.append(f"    {col_label}: {combined_text}")
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
    schema: Dict[str, Any] | None = None,
    fields: list | None = None,
    template_metadata: Dict[str, Any] | None = None
) -> str:
    """
    Convenience function to build an enhanced prompt.
    """
    if not form_data:
        return user_prompt

    return EnhancedPromptBuilder.build_prompt_with_form_data(
        user_prompt, form_data, schema, fields, template_metadata
    )
