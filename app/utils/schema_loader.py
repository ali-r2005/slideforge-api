import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SchemaLoader:
    """
    Loads and manages JSON schemas for templates.
    Schemas are defined within template metadata files under the "schema" property.
    """

    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self._cache: Dict[str, Dict[str, Any]] = {}

    def load_schema(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Load a schema for a given template from its metadata file.

        The schema is embedded in the template metadata file under the "schema" property.

        Args:
            template_name: Name of the template (without .json extension)

        Returns:
            Schema dict if found, None otherwise
        """
        # Check cache first
        if template_name in self._cache:
            return self._cache[template_name]

        template_path = self.templates_dir / f"{template_name}.json"

        if not template_path.is_file():
            logger.info(f"Template not found for: {template_name}")
            return None

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_data = json.load(f)

            # Extract schema from template metadata
            if "schema" not in template_data:
                logger.info(f"No schema defined in template: {template_name}")
                return None

            schema = template_data["schema"]

            # Validate schema structure
            if not self._validate_schema_structure(schema):
                logger.error(f"Invalid schema structure for {template_name}")
                return None

            # Ensure template_name is set for consistency
            if "template_name" not in schema:
                schema["template_name"] = template_name

            # Cache it
            self._cache[template_name] = schema
            logger.info(f"Loaded schema for template: {template_name}")
            return schema

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse template for {template_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading schema for {template_name}: {e}")
            return None

    def _validate_schema_structure(self, schema: Dict[str, Any]) -> bool:
        """
        Validates that schema has the required structure.
        Supports optional groups for organizing fields.
        """
        if not isinstance(schema, dict):
            return False

        # Must have fields array
        if "fields" not in schema:
            return False

        if not isinstance(schema["fields"], list):
            return False

        # Each field must have required properties
        for field in schema["fields"]:
            if not isinstance(field, dict):
                return False

            required_keys = {"name", "type", "required"}
            if not required_keys.issubset(field.keys()):
                return False

            # Validate field type
            valid_types = {"text", "textarea", "number", "email", "date", "enum", "boolean", "table"}
            if field["type"] not in valid_types:
                return False

        # Validate table specific requirements
        all_field_names = {f["name"] for f in schema["fields"]}
        for field in schema["fields"]:
            if field["type"] == "table":
                # table type requires date_range fields and columns
                if "date_range_start_field" not in field or "date_range_end_field" not in field:
                    return False
                if "columns" not in field or not isinstance(field["columns"], list):
                    return False
                if len(field["columns"]) == 0:
                    return False

                # Validate columns are strings
                for col in field["columns"]:
                    if not isinstance(col, str):
                        return False

                # Validate referenced date fields exist
                if field["date_range_start_field"] not in all_field_names:
                    return False
                if field["date_range_end_field"] not in all_field_names:
                    return False

                # Validate optional cell_structure if present
                if "cell_structure" in field:
                    if not self._validate_cell_structure(field["cell_structure"]):
                        return False

        # Validate optional groups if present
        if "groups" in schema:
            if not isinstance(schema["groups"], list):
                return False

            for group in schema["groups"]:
                if not isinstance(group, dict):
                    return False

                if "name" not in group or not isinstance(group["name"], str):
                    return False

                if "fields" not in group or not isinstance(group["fields"], list):
                    return False

                for field_name in group["fields"]:
                    if not isinstance(field_name, str):
                        return False

        return True

    def _validate_cell_structure(self, cell_struct: Dict[str, Any]) -> bool:
        """
        Validates cell_structure format (both old and new formats).

        Supports:
        - Old format: parts as array of strings ["context", "team_building", "agency_offer"]
        - New format: parts as array of objects with name, type, label, etc.
        """
        if not isinstance(cell_struct, dict):
            return False

        if "parts" not in cell_struct or not isinstance(cell_struct["parts"], list):
            return False

        if len(cell_struct["parts"]) == 0:
            return False

        parts = cell_struct["parts"]

        # Check if old format (array of strings)
        if isinstance(parts[0], str):
            valid_parts = {"context", "team_building", "agency_offer"}
            for part in parts:
                if not isinstance(part, str) or part not in valid_parts:
                    return False

            # Validate optional ai_generates and user_provides arrays
            for key in ["ai_generates", "user_provides"]:
                if key in cell_struct:
                    if not isinstance(cell_struct[key], list):
                        return False
                    for item in cell_struct[key]:
                        if not isinstance(item, str) or item not in valid_parts:
                            return False

            # Validate optional team_building_db flag
            if "team_building_db" in cell_struct:
                if not isinstance(cell_struct["team_building_db"], bool):
                    return False

        # Check if new format (array of objects)
        elif isinstance(parts[0], dict):
            # Validate draggable flag if present (default is false)
            if "draggable" in cell_struct:
                if not isinstance(cell_struct["draggable"], bool):
                    return False

            # Validate each part object
            part_names = set()
            for part in parts:
                if not isinstance(part, dict):
                    return False

                # Required fields for each part
                required_keys = {"name", "type", "label"}
                if not required_keys.issubset(part.keys()):
                    return False

                # Validate name is string and unique
                if not isinstance(part["name"], str):
                    return False
                if part["name"] in part_names:
                    return False  # Duplicate part names not allowed
                part_names.add(part["name"])

                # Validate type is valid
                valid_types = {"array-textarea", "select", "textarea", "text", "dropdown"}
                if part["type"] not in valid_types:
                    return False

                # Validate label is string
                if not isinstance(part["label"], str):
                    return False

                # Validate optional required field
                if "required" in part:
                    if not isinstance(part["required"], bool):
                        return False

                # Validate optional ai_generates field
                if "ai_generates" in part:
                    if not isinstance(part["ai_generates"], bool):
                        return False

                # Validate optional user_provides field
                if "user_provides" in part:
                    if not isinstance(part["user_provides"], bool):
                        return False

                # For select type parts, validate database field exists
                if part["type"] == "select":
                    if "database" not in part or not isinstance(part["database"], str):
                        return False

        else:
            return False

        return True

    def get_field_by_name(self, schema: Dict[str, Any], field_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific field definition from a schema.
        """
        for field in schema.get("fields", []):
            if field.get("name") == field_name:
                return field
        return None

    def get_all_field_names(self, schema: Dict[str, Any]) -> list:
        """
        Get all field names from a schema in order.
        """
        return [field.get("name") for field in schema.get("fields", [])]

    def clear_cache(self):
        """Clear the schema cache."""
        self._cache.clear()


# Global instance
_loader = SchemaLoader()


def load_schema(template_name: str) -> Optional[Dict[str, Any]]:
    """Convenience function to load a schema."""
    return _loader.load_schema(template_name)


def has_schema(template_name: str) -> bool:
    """Check if a template has a schema."""
    return load_schema(template_name) is not None
