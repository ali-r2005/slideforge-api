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

    if "image:logo" in field_name:
        return "image_logo"
    
    if "image:topic" in field_name or "image:bg" in field_name or "image:photo" in field_name:
        return "image_topic"

    return "text"

TYPE_MAX_CHARS = {
    "title": 40,
    "subtitle": 60,
    "paragraph": 150,
    "bullet_list": 80,
    "text": 100,
    "image_logo": 50,
    "image_topic": 50
}
