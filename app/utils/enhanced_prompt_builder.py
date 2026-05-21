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

        # Check if form data contains program_table with cell_structure
        has_program_table_with_structure = False
        if schema:
            for field in schema.get("fields", []):
                if field.get("type") == "program_table" and "cell_structure" in field:
                    has_program_table_with_structure = True
                    break

        # Combine into final prompt
        enhanced_prompt = f"""{user_prompt}

Structured Parameters:
{parameters_section}

IMPORTANT: Treat the above Structured Parameters as strict constraints.
If the user request conflicts with any parameter, prioritize the parameter values.
Use these parameters to ensure consistency in the generated content."""

        # Add special instructions for program table with arrays
        if has_program_table_with_structure:
            enhanced_prompt += """\n
ARRAY RESPONSE FORMAT FOR PROGRAM TABLE:
- When you see "Context Request:" or "Agency Offers Request:", respond with an array format
- CONTEXT: Return as JSON array: ["paragraph 1", "paragraph 2", "paragraph 3"]
- AGENCY OFFERS: Return as JSON array: ["offer 1", "offer 2", "offer 3"]
- Each array item becomes a separate paragraph in the final document
- Make sure all arrays are properly formatted as valid JSON"""

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
                        if col_key == "date" or not col_value:
                            continue

                        col_label = col_key.replace("_", " ").title()

                        # Handle new cell_structure format (nested object)
                        if isinstance(col_value, dict):
                            lines.append(f"    {col_label}:")

                            # Context part - user prompt for AI
                            if col_value.get("context_prompt"):
                                context_prompt = col_value["context_prompt"]
                                lines.append(f"      Context Request: {context_prompt}")
                                lines.append(f"      → Return as: ['paragraph 1', 'paragraph 2', ...]")

                            # Team building part - selected activity
                            if col_value.get("team_building"):
                                tb = col_value["team_building"]
                                tb_name = tb.get("name", "Unknown")
                                tb_slogan = tb.get("slogan", "")
                                if tb_slogan:
                                    lines.append(f"      Team Building: {tb_name} - {tb_slogan}")
                                else:
                                    lines.append(f"      Team Building: {tb_name}")

                            # Agency offer part - user specified offers
                            if col_value.get("agency_offer_request"):
                                agency_request = col_value["agency_offer_request"]
                                lines.append(f"      Agency Offers Request: {agency_request}")
                                lines.append(f"      → Return as: ['offer 1', 'offer 2', ...]")
                        else:
                            # Legacy format - simple string value
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
