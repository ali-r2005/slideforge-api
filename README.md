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

## 📋 Schema-Driven Forms

Templates can define a JSON schema to collect structured form data from users instead of (or in addition to) a text prompt.

### Schema Structure

Schemas are **embedded within template metadata files**. Each template file (`templates/{template_name}.json`) can include a `schema` property with field definitions:

```json
{
  "name": "template_name",
  "description": "Template description",
  "system_instructions": "AI generation instructions",
  "tone": "professional and clear",
  
  "schema": {
    "fields": [
      {
        "name": "field_name",
        "type": "text|textarea|number|email|date|enum|boolean|program_table",
        "required": true,
        "label": "Field Label",
        "description": "Help text shown to users",
        "values": ["option1", "option2"],  // For enum type
        "min": 0,                          // For number type
        "max": 100,                        // For number type
        "max_length": 200,                 // For text/textarea
        "default": "value"                 // Optional default value
      }
    ],
    "groups": [                            // Optional: organize fields visually
      {
        "name": "Group Name",
        "description": "Group description",
        "fields": ["field_name1", "field_name2"]
      }
    ]
  },
  
  "field_instructions": {
    "placeholder_name": "Special instructions for AI"
  },
  
  "constraints": {
    "focus_on": ["theme1", "theme2"],
    "keep_professional": true
  }
}
```

### Field Types

- **text**: Single-line text input (supports max_length)
- **textarea**: Multi-line text input (supports max_length)
- **number**: Numeric input (supports min/max)
- **email**: Email validation required
- **date**: Date picker (YYYY-MM-DD format)
- **enum**: Dropdown select (requires values array)
- **boolean**: Checkbox
- **program_table**: Complex table with draggable sections for event scheduling

### Form Groups

Groups organize related fields into visually separated sections. For example:

```json
"groups": [
  {
    "name": "Contact Information",
    "description": "Primary contact details",
    "fields": ["first_name", "last_name", "email", "phone"]
  },
  {
    "name": "Company Details",
    "description": "Business information",
    "fields": ["company_name", "industry", "employee_count"]
  }
]
```

Groups are optional. If not specified, all fields display in a flat list. Fields not referenced in any group appear at the top.

### Example Templates

See `templates/` directory for examples:
- `template3.json` - Destination showcase with event planning
- `template7.json` - Event program schedule with draggable sections
- `event_template.json` - Full event planning form
- `corporate_pitch.json` - Corporate pitch with company information

## 📦 Requirements
- Python 3.10+
- `python-pptx`
- `FastAPI` / `Uvicorn`
- `LibreOffice` (for PDF conversion)
