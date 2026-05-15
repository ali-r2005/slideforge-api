class AIResponseValidationError(ValueError):
    pass

def validate_ai_response(data: dict, fields: list[dict], trim_long_fields: bool = False):
    if not isinstance(data, dict):
        raise AIResponseValidationError("AI response must be a JSON object")

    required_fields = [field["placeholder"] for field in fields]
    required_field_set = set(required_fields)
    response_field_set = set(data.keys())
    errors = []

    missing_fields = required_field_set - response_field_set
    if missing_fields:
        errors.extend(
            f"Missing field: {field}"
            for field in sorted(missing_fields)
        )

    # Remove extra fields we didn't ask for
    for extra_field in response_field_set - required_field_set:
        data.pop(extra_field, None)

    for field in fields:
        name = field["placeholder"]
        if name not in data:
            continue

        field_type = field["type"]
        value = data[name]

        # 1. Validate Type
        if field_type in ["bullet_list", "table"]:
            if not isinstance(value, list):
                errors.append(f"{name} must be a list (current type: {type(value).__name__})")
                continue
            
            # Further validation for tables
            if field_type == "table":
                expected_cols = field.get("columns", 0)
                for row_idx, row in enumerate(value):
                    if not isinstance(row, list):
                        errors.append(f"Row {row_idx} of {name} must be a list")
                    elif expected_cols > 0 and len(row) != expected_cols:
                        errors.append(f"Row {row_idx} of {name} must have exactly {expected_cols} columns")

        else:
            # Everything else should be text
            if not isinstance(value, (str, int, float)):
                errors.append(f"{name} must be text (current type: {type(value).__name__})")
            else:
                # Convert numbers to string
                data[name] = str(value)

    if errors:
        raise AIResponseValidationError("; ".join(errors))

    return data
