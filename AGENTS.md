# Agent Rules & Guidelines

## 📝 Documentation Maintenance
- **README Rule**: Every time a new endpoint is added, a new template convention is created, or a core logic (like image processing or table handling) is modified, you MUST update the `README.md` to reflect these changes.
- Ensure the `Template Conventions` section is always accurate as it is the primary guide for the user when designing PPTX files.

## 🛠 Coding Standards
- **Coordinate Geometry**: Always account for PowerPoint group scaling (`chOff`/`chExt`) when calculating absolute positions.
- **Image Handling**: Always clean up temporary image files after generation using the `cleanup_temp_images` utility.
- **Table Logic**: Since `python-pptx` lacks a native `add_row` method, always use the XML-based `add_row_to_table` workaround to preserve styling.
- **Error Propagation**: Ensure detailed error messages (like `AIResponseValidationError`) are returned to the frontend via FastAPI's `HTTPException`.
