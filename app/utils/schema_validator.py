from typing import Dict, Any, List, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SchemaValidationError(ValueError):
    """Raised when form data doesn't match schema."""
    pass


class SchemaValidator:
    """
    Validates form data against a schema.
    Ensures data types, required fields, and constraints are met.
    """

    @staticmethod
    def validate(form_data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate form data against a schema.

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # Check each field in schema
        for field in schema.get("fields", []):
            field_name = field.get("name")
            field_type = field.get("type")
            is_required = field.get("required", False)
            value = form_data.get(field_name)

            # Check if field is present and not empty
            if is_required and (value is None or value == "" or value == []):
                errors.append(f"Field '{field_name}' is required")
                continue

            # Skip validation if field is optional and not provided
            if not is_required and (value is None or value == ""):
                continue

            # Validate based on field type
            type_error = SchemaValidator._validate_field_type(field, value)
            if type_error:
                errors.append(type_error)

            # Validate constraints
            constraint_errors = SchemaValidator._validate_constraints(field, value)
            errors.extend(constraint_errors)

        # Check for extra fields not in schema
        schema_field_names = {f.get("name") for f in schema.get("fields", [])}
        for key in form_data.keys():
            if key not in schema_field_names:
                errors.append(f"Unknown field: '{key}'")

        return len(errors) == 0, errors

    @staticmethod
    def _validate_field_type(field: Dict[str, Any], value: Any) -> str | None:
        """
        Validate that the value matches the field type.
        Returns error message if invalid, None if valid.
        """
        field_type = field.get("type")
        field_name = field.get("name")

        try:
            if field_type == "text" or field_type == "textarea":
                if not isinstance(value, str):
                    return f"Field '{field_name}' must be text"

            elif field_type == "number":
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        return f"Field '{field_name}' must be a number"

            elif field_type == "email":
                if not isinstance(value, str):
                    return f"Field '{field_name}' must be text"
                # Simple email validation
                if "@" not in value or "." not in value.split("@")[-1]:
                    return f"Field '{field_name}' must be a valid email"

            elif field_type == "date":
                # Handle both string dates (YYYY-MM-DD) and date objects
                if isinstance(value, str):
                    try:
                        datetime.strptime(value, "%Y-%m-%d")
                    except ValueError:
                        return f"Field '{field_name}' must be a valid date (YYYY-MM-DD)"
                elif not isinstance(value, dict):  # dict for date range handling
                    return f"Field '{field_name}' must be a date"

            elif field_type == "enum":
                values = field.get("values", [])
                if value not in values:
                    return f"Field '{field_name}' must be one of: {', '.join(values)}"

            elif field_type == "boolean":
                if not isinstance(value, bool):
                    if isinstance(value, str):
                        if value.lower() not in ("true", "false", "yes", "no"):
                            return f"Field '{field_name}' must be true or false"
                    else:
                        return f"Field '{field_name}' must be a boolean"

            elif field_type == "program_table":
                if not isinstance(value, list):
                    return f"Field '{field_name}' must be an array"

                expected_columns = set(field.get("columns", []))
                has_cell_structure = "cell_structure" in field

                for idx, row in enumerate(value):
                    if not isinstance(row, dict):
                        return f"Field '{field_name}' row {idx} must be an object"

                    if "date" not in row:
                        return f"Field '{field_name}' row {idx} missing 'date' key"

                    # Validate date format
                    try:
                        datetime.strptime(row["date"], "%Y-%m-%d")
                    except (ValueError, TypeError):
                        return f"Field '{field_name}' row {idx} date must be valid ISO format (YYYY-MM-DD)"

                    # Check all columns exist
                    for col_key in expected_columns:
                        if col_key not in row:
                            return f"Field '{field_name}' row {idx} missing column '{col_key}'"

                        col_value = row[col_key]

                        # Handle new cell_structure format (nested object with context, team_building, agency_offer)
                        if has_cell_structure:
                            if isinstance(col_value, dict):
                                # Validate context if present - must be array of strings
                                if "context" in col_value:
                                    if not isinstance(col_value["context"], list):
                                        return f"Field '{field_name}' row {idx} column '{col_key}' context must be an array"
                                    if not all(isinstance(item, str) for item in col_value["context"]):
                                        return f"Field '{field_name}' row {idx} column '{col_key}' context items must be strings"

                                # Validate team_building if present - must be object or null
                                if "team_building" in col_value:
                                    tb = col_value["team_building"]
                                    if tb is not None and not isinstance(tb, dict):
                                        return f"Field '{field_name}' row {idx} column '{col_key}' team_building must be object or null"

                                # Validate agency_offer if present - must be array of strings
                                if "agency_offer" in col_value:
                                    if not isinstance(col_value["agency_offer"], list):
                                        return f"Field '{field_name}' row {idx} column '{col_key}' agency_offer must be an array"
                                    if not all(isinstance(item, str) for item in col_value["agency_offer"]):
                                        return f"Field '{field_name}' row {idx} column '{col_key}' agency_offer items must be strings"
                            elif isinstance(col_value, str):
                                # Support legacy simple string cells for backward compatibility
                                pass
                            else:
                                return f"Field '{field_name}' row {idx} column '{col_key}' must be object or string"
                        else:
                            # Legacy format - simple string values
                            if not isinstance(col_value, str):
                                return f"Field '{field_name}' row {idx} column '{col_key}' must be text"

        except Exception as e:
            logger.error(f"Error validating field {field_name}: {e}")
            return f"Error validating field '{field_name}': {str(e)}"

        return None

    @staticmethod
    def _validate_constraints(field: Dict[str, Any], value: Any) -> List[str]:
        """
        Validate constraints like min, max, max_length, enum values.
        Returns list of error messages.
        """
        errors = []
        field_name = field.get("name")
        field_type = field.get("type")

        try:
            # Number range validation
            if field_type == "number":
                num_value = float(value)
                min_val = field.get("min")
                max_val = field.get("max")

                if min_val is not None and num_value < min_val:
                    errors.append(f"Field '{field_name}' must be at least {min_val}")
                if max_val is not None and num_value > max_val:
                    errors.append(f"Field '{field_name}' cannot exceed {max_val}")

            # Date range validation (for start_date < end_date checks)
            # Note: This would need the full form_data to validate properly
            # For now, individual date validation is handled in _validate_field_type

        except Exception as e:
            logger.error(f"Error validating constraints for {field_name}: {e}")
            errors.append(f"Error validating field '{field_name}'")

        return errors

    @staticmethod
    def filter_optional_fields(form_data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove optional fields that are empty/None from form_data.
        Returns cleaned form_data.
        """
        schema_fields = {f.get("name"): f for f in schema.get("fields", [])}
        cleaned = {}

        for key, value in form_data.items():
            field = schema_fields.get(key)

            # Include if field is required OR has a value
            if field and field.get("required", False):
                cleaned[key] = value
            elif value not in (None, "", [], {}):
                cleaned[key] = value

        return cleaned
