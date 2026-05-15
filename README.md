# SlideForge API

SlideForge is a high-performance PowerPoint generation service that combines AI-driven content generation with advanced visual automation.

## 🚀 Core Features

- **AI-Powered Content**: Generates professional text using OpenRouter (Qwen/GPT models).
- **Dynamic Map Pointers**: Automatically highlights regions on a map and places pointers using absolute coordinate translation (supports nested group scaling).
- **Branding Automation**: Fetches company logos via [logo.dev](https://logo.dev/) based on the presentation topic.
- **Visual Excellence**: Integrated with [Pexels API](https://www.pexels.com/) to find and insert relevant stock photography.
- **Dynamic Tables**: Automatically expands table rows based on AI data while preserving original PowerPoint styling.
- **PDF Export**: Instant conversion of generated presentations to PDF using LibreOffice.

---

## 🛠 Endpoints

### 1. `GET /templates`
Returns a list of available `.pptx` templates in the `templates/` directory.

### 2. `POST /generate-ppt`
The main endpoint for creating a new presentation.
- **Payload**: `{ "prompt": "Topic string", "template": "filename.pptx" }`
- **Logic**: Extracts placeholders, generates content via AI, performs image/logo/table/map injections, and returns a unique ID.

### 3. `POST /update-ppt`
Updates or regenerates an existing presentation.
- **Payload**: `{ "presentation_id": "uuid", "template": "filename.pptx", "replacements": { ... } }`

### 4. `GET /generated/{filename}`
Serves the generated `.pptx` or `.pdf` files.

---

## 🎨 Template Conventions

To enable automation, use the following tags in your PowerPoint templates:

### Text Placeholders
Use double curly braces anywhere in text boxes:
- `{{title}}`, `{{summary}}`, `{{date}}`, etc.

### Image & Logo Placeholders
Set these in the **Alt Text** of any shape:
- `{{image:logo}}`: AI provides a company domain; code fetches the logo.
- `{{image:topic}}` or `{{image:bg}}`: AI provides a search query; code fetches a Pexels photo.

### Dynamic Tables
Set this in the **Alt Text** of a table:
- `{{table:your_name}}`: 
    - The table should have 2 rows (Header + 1 Style Template row).
    - The code will automatically add rows and copy the styling from the 2nd row.

### Interactive Maps
Use these specific **Alt Text** labels for shapes in a map group:
- `Map_Pointer`: The main pointer shape (will be moved to the region).
- `point_Pointer`: A small circle/dot (will be centered on the region).
- `region_name`: Any shape with Alt Text matching a location (e.g., "Paris" or "Morocco") will be highlighted yellow.

---

## ⚙️ Environment Variables
Create a `.env` file in the root:
```bash
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=qwen/qwen-2.5-72b-instruct
PEXELS_API_KEY=your_key
LOGO_DEV_PUBLIC_KEY=your_key
```

## 📦 Requirements
- Python 3.10+
- `python-pptx`
- `FastAPI` / `Uvicorn`
- `LibreOffice` (for PDF conversion)
