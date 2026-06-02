# Agent Rules & Guidelines

## 📝 Documentation Maintenance
- **README Rule**: Every time a new endpoint is added, a new template convention is created, or a core logic (like image processing or table handling) is modified, you MUST update the `README.md` to reflect these changes.
- Ensure the `Template Conventions` section is always accurate as it is the primary guide for the user when designing PPTX files.

## 🛠 Coding Standards
- **Coordinate Geometry**: Always account for PowerPoint group scaling (`chOff`/`chExt`) when calculating absolute positions.
- **Image Handling**: Always clean up temporary image files after generation using the `cleanup_temp_images` utility.
- **Table Logic**: All table operations are handled in `app/services/table_service.py`. This includes:
  - `extract_table_headers()` — Extract column headers
  - `fill_table()` — Fill table with data (supports dict and list formats)
  - `set_cell_text_preserve_formatting()` — Set cell text while preserving formatting and applying marker-based conventions
  - `add_row_to_table()` — XML-based row addition to preserve template styling
  - Cell formatting utilities: `apply_cell_formatting()`, `copy_cell_style()`
- **Error Propagation**: Ensure detailed error messages (like `AIResponseValidationError`) are returned to the frontend via FastAPI's `HTTPException`.

## 📁 Service Architecture
- **`pptx_service.py`**: Handles presentation generation, text replacement, marker parsing, image insertion
- **`table_service.py`**: Handles all table operations (extraction, filling, cell formatting, row addition)
- **`image_service.py`**: Handles image processing (logo retrieval, topic image search)
- **`marker_parser.py`**: Parses field-specific formatting markers from AI output
- Maintain this separation: don't add table logic to pptx_service, don't add presentation logic to table_service
