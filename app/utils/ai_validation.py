class AIResponseValidationError(ValueError):
    pass


def _field_value_text(value):
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)

    return str(value)


def _trim_value(value, max_chars: int):
    if isinstance(value, list):
        trimmed_items = []
        remaining_chars = max_chars

        for item in value:
            item_text = str(item)
            if remaining_chars <= 0:
                break

            trimmed_item = item_text[:remaining_chars].rstrip()
            if trimmed_item:
                trimmed_items.append(trimmed_item)
                remaining_chars -= len(trimmed_item) + 1

        return trimmed_items

    return str(value)[:max_chars].rstrip()


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

    for extra_field in response_field_set - required_field_set:
        data.pop(extra_field, None)

    for field in fields:
        name = field["placeholder"]

        if name not in data:
            continue

        field_type = field["type"]
        value = data[name]

        if field_type == "bullet_list" and not isinstance(value, list):
            errors.append(f"{name} must be a list")
            continue

        if field_type != "bullet_list" and not isinstance(value, str):
            errors.append(f"{name} must be text")
            continue

        # value_text = _field_value_text(value)
        # max_chars = field["max_chars"]

        # if len(value_text) > max_chars:
        #     if trim_long_fields:
        #         data[name] = _trim_value(value, max_chars)
        #     else:
        #         errors.append(f"{name} is longer than {max_chars} characters")

    if errors:
        raise AIResponseValidationError("; ".join(errors))

    return data
