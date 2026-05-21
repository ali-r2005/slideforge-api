import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SchemaLoader:
    """
    Loads and manages JSON schemas for templates.
    Schemas define the form structure and validation rules.
    """

    def __init__(self, schemas_dir: str = "templates/schemas"):
        self.schemas_dir = Path(schemas_dir)
        self._cache: Dict[str, Dict[str, Any]] = {}

    def load_schema(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Load a schema for a given template.

        Args:
            template_name: Name of the template (without .json extension)

        Returns:
            Schema dict if found, None otherwise
        """
        # Check cache first
        if template_name in self._cache:
            return self._cache[template_name]

        schema_path = self.schemas_dir / f"{template_name}-schema.json"

        if not schema_path.is_file():
            logger.info(f"Schema not found for template: {template_name}")
            return None

        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)

            # Validate schema structure
            if not self._validate_schema_structure(schema):
                logger.error(f"Invalid schema structure for {template_name}")
                return None

            # Cache it
            self._cache[template_name] = schema
            logger.info(f"Loaded schema for template: {template_name}")
            return schema

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse schema for {template_name}: {e}")
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
            valid_types = {"text", "textarea", "number", "email", "date", "enum", "boolean", "program_table"}
            if field["type"] not in valid_types:
                return False

        # Validate program_table specific requirements
        all_field_names = {f["name"] for f in schema["fields"]}
        for field in schema["fields"]:
            if field["type"] == "program_table":
                # program_table requires date_range fields and columns
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
