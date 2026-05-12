def infer_placeholder_type(field_name: str):
    field_name = field_name.lower()

    if "title" in field_name:
        return "title"

    if "summary" in field_name or "paragraph" in field_name or "description" in field_name:
        return "paragraph"
    
    if "bullet" in field_name or "list" in field_name:
        return "bullet_list"
    
    if "subtitle" in field_name:
        return "subtitle"

    return "text"

TYPE_MAX_CHARS = {
    "title": 40,
    "subtitle": 60,
    "paragraph": 150,
    "bullet_list": 80,
    "text": 100
}
