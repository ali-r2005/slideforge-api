# Schema and Metadata Guide

Complete guide to SlideForge's schema system and template metadata for form configuration, AI instructions, and template behavior customization.

---

## Architecture Overview

Templates consolidate all metadata, schema, and configuration in a single JSON file (`templates/{template_name}.json`):

```json
{
  "name": "template_name",
  "description": "User-facing description",
  "system_instructions": "AI generation instructions",
  "tone": "professional and clear",
  
  "schema": {
    "fields": [ ... ],    // Form field definitions
    "groups": [ ... ]     // Organized field groups
  },
  
  "field_instructions": { ... },  // Per-field AI instructions + pagination
  "constraints": { ... }          // Template constraints
}
```

---

## Schema: Form Field Definitions

The `schema` block defines the form that users fill out. Each field has a type, validation rules, and optionally a label/description.

### Supported Field Types

| Type | Validation | Use Case | Example |
|------|-----------|----------|---------|
| `text` | max_length | Single-line input | "Team name" |
| `textarea` | max_length | Multi-line input | "Event description" |
| `number` | min, max | Integer or float | Budget: 5000 |
| `email` | email format | Email input | "user@example.com" |
| `date` | date format YYYY-MM-DD | Date picker | "2026-06-15" |
| `enum` | values list | Dropdown | "Option 1", "Option 2" |
| `boolean` | - | Checkbox/toggle | true/false |
| `table` | row_source, cell_structure | Complex table | [see SCHEMA_DRIVEN_TABLE_SYSTEM.md] |

### Schema Field Definition

```json
{
  "name": "field_key",
  "type": "text",
  "required": true,
  "label": "Display name",
  "description": "Help text for user",
  "max_length": 100,           // For text/textarea
  "min": 0, "max": 10000,      // For number
  "values": ["A", "B", "C"],   // For enum
  "row_source": { ... },       // For table
  "cell_structure": { ... }    // For table
}
```

### Grouping Fields

Organize fields into logical groups:

```json
{
  "groups": [
    {
      "name": "Event Details",
      "description": "Basic event information",
      "fields": ["event_name", "event_date", "location"]
    },
    {
      "name": "Attendees",
      "fields": ["team_size", "attendee_list"]
    }
  ]
}
```

---

## Field Instructions: AI Guidance and Pagination

The `field_instructions` block provides **AI generation guidance** for each placeholder and **pagination configuration** for tables.

### Structure

```json
{
  "field_instructions": {
    "placeholder_name": {
      "label": "Human-readable name",
      "instructions": "Specific instructions for AI",
      "rows_per_slide": 3,  // For tables: rows per slide
      "formatting_conventions": [ ... ]  // For marker-based formatting
    }
  }
}
```

### Simple Field Instructions (String)

For straightforward guidance, use a string:

```json
{
  "field_instructions": {
    "title": "Keep titles concise and compelling",
    "location": "Just city and country, e.g., 'Tangier, Morocco'"
  }
}
```

### Complex Field Instructions (Object)

For detailed guidance, use an object:

```json
{
  "field_instructions": {
    "destination_description": {
      "instructions": "First paragraph: destination overview. Second paragraph: benefits for corporate groups.",
      "min_length": "2 sentences per paragraph"
    }
  }
}
```

### Table Pagination Configuration

Set `rows_per_slide` in a table's field_instructions entry (keyed by placeholder):

```json
{
  "field_instructions": {
    "table:programme": {
      "label": "Program Schedule",
      "rows_per_slide": 1,  // One day per slide
      "instructions": "Generate activity descriptions...",
      "formatting_conventions": [ ... ]
    }
  }
}
```

See [TABLE_PAGINATION.md](TABLE_PAGINATION.md) for details.

---

## Formatting Conventions: Marker-Based Styling

For field-specific text styling (colors, bold, italic), define formatting conventions:

```json
{
  "field_instructions": {
    "table:programme": {
      "formatting_conventions": [
        {
          "name": "activity_name",
          "marker": "$$activity$$",
          "pptx_style": {
            "color": "FF6B35",
            "bold": true
          },
          "instruction": "Wrap activity names with $$activity$$Activity Name$$activity$$"
        }
      ]
    }
  }
}
```

AI reads the instruction and wraps content with markers. The backend parses markers and applies styling.

---

## Template Metadata Examples

### Example 1: Destination Showcase

**File:** `template3.json`

```json
{
  "name": "template3",
  "description": "Destination showcase for corporate travel",
  "system_instructions": "Generate engaging travel content focused on team-building. Emphasize practical benefits for corporate groups.",
  "tone": "professional yet engaging",

  "schema": {
    "fields": [
      {
        "name": "destination_name",
        "type": "text",
        "required": true,
        "label": "Destination",
        "max_length": 50
      },
      {
        "name": "description",
        "type": "textarea",
        "required": true,
        "label": "Why visit here?",
        "max_length": 500
      }
    ]
  },

  "field_instructions": {
    "destination_name": "City and country, e.g., 'Tangier, Morocco'",
    "destination_paragraph": {
      "instructions": "Paragraph 1: destination overview. Paragraph 2: benefits for corporate groups."
    }
  },

  "constraints": {
    "focus_on": ["team-building opportunities", "accessibility"],
    "avoid": ["generic tourism clichés"]
  }
}
```

### Example 2: Event Program with Tables and Sections

**File:** `template7.json` (real example)

```json
{
  "name": "template7",
  "description": "Event program schedule with dynamic sections",
  "system_instructions": "Generate practical event content highlighting activities, timing, and team engagement.",
  "tone": "professional and clear",

  "schema": {
    "fields": [
      {
        "name": "event_name",
        "type": "text",
        "required": true,
        "label": "Event Name"
      },
      {
        "name": "event_start_date",
        "type": "date",
        "required": true,
        "label": "Start Date"
      },
      {
        "name": "event_end_date",
        "type": "date",
        "required": false,
        "label": "End Date"
      },
      {
        "name": "program_schedule",
        "type": "table",
        "required": true,
        "row_source": {
          "type": "date_range",
          "config": {
            "start_field": "event_start_date",
            "end_field": "event_end_date"
          }
        },
        "columns": ["Matinée", "Midi", "Après-midi", "Soir"],
        "cell_structure": {
          "draggable": true,
          "parts": [
            {
              "name": "context",
              "type": "array-textarea",
              "label": "Context/Setup",
              "ai_generates": true,
              "user_provides": true
            },
            {
              "name": "team_building",
              "type": "select",
              "label": "Team Building",
              "database": "tb",
              "user_provides": true
            }
          ]
        }
      }
    ]
  },

  "field_instructions": {
    "table:programme": {
      "label": "Program Schedule",
      "rows_per_slide": 1,
      "instructions": "For each time slot, generate: 1) context items elaborated into paragraphs. 2) team_building activity. Generate all in marked-up format.",
      "formatting_conventions": [
        {
          "name": "activity_name",
          "marker": "$$activity$$",
          "pptx_style": { "color": "FF6B35", "bold": true },
          "instruction": "Wrap activity names with $$activity$$Activity Name$$activity$$"
        }
      ]
    }
  }
}
```

### Example 3: Training Course

**File:** `training_template.json`

```json
{
  "name": "training_template",
  "description": "Professional training course overview",
  "system_instructions": "Generate clear, structured educational content with practical outcomes.",
  "tone": "educational and professional",

  "schema": {
    "fields": [
      {
        "name": "course_title",
        "type": "text",
        "required": true,
        "label": "Course Title",
        "max_length": 100
      },
      {
        "name": "course_description",
        "type": "textarea",
        "required": true,
        "label": "Course Overview"
      },
      {
        "name": "modules",
        "type": "table",
        "row_source": { "type": "fixed", "config": { "count": 5 } },
        "columns": ["Module", "Duration", "Key Topics"],
        "cell_structure": {
          "parts": [
            { "name": "title", "type": "text", "label": "Module Title" },
            { "name": "duration", "type": "text", "label": "Hours" }
          ]
        }
      }
    ]
  },

  "field_instructions": {
    "course_title": "Make it specific and action-oriented",
    "course_description": {
      "instructions": "Paragraph 1: What course covers. Paragraph 2: Who should take it. Paragraph 3: Expected outcomes."
    },
    "table:modules": {
      "instructions": "List 5 core modules with descriptions and durations.",
      "rows_per_slide": 2
    }
  }
}
```

---

## Backend Infrastructure

### Schema Loader (`app/utils/schema_loader.py`)

Loads and validates schemas from template metadata files.

**Responsibilities:**
- Load JSON from `templates/{template_name}.json`
- Extract the `schema` property
- Validate schema structure
- Cache for performance
- Return None if schema doesn't exist

**Key functions:**
```python
load_schema(template_name)  # Load + validate schema
has_schema(template_name)   # Check if schema exists
get_field_by_name()         # Get specific field definition
```

### Schema Validator (`app/utils/schema_validator.py`)

Validates form_data against the schema at submission time.

**Responsibilities:**
- Type checking (text, number, date, enum, etc.)
- Constraint validation (min, max, max_length, required)
- Filter optional empty fields
- Return detailed validation errors

**Key functions:**
```python
SchemaValidator.validate(form_data, schema)     # Validate + return errors
SchemaValidator.filter_optional_fields(data, schema)  # Clean up
```

### Template Metadata Loader (`app/utils/template_metadata.py`)

Loads the complete metadata file (including schema, field_instructions, constraints).

**Key functions:**
```python
load_template_metadata(template_name)  # Load full metadata
get_field_instruction(metadata, field_name)  # Get AI instruction
get_table_row_count(metadata, table_name)    # Get rows_per_slide
```

### Database Loader (`app/utils/database_loader.py`)

For select-type cell parts, loads database files from `DB/{name}.json`.

**Validates:**
- File exists
- Valid JSON
- Every item has `id` and `name` fields

**Returns:**
- Formatted options for frontend or error message

---

## Frontend Data Flow

```
1. User selects template
   ↓
2. Frontend fetches schema (GET /schema/{template_name})
   ↓
3. Has schema?
   YES → Render dynamic form based on fields
   NO  → Show text area (backward compatible)
   ↓
4. User fills form fields
   ↓
5. Submit: POST /generate-ppt with form_data
   ↓
6. Backend validates form_data against schema
   ↓
7. Invalid? Return errors to frontend
   Valid? Build enhanced prompt + send to AI
   ↓
8. AI generates content respecting form parameters
   ↓
9. Generate PPTX + return to user
```

---

## Backward Compatibility

**Templates without schema:**
- Frontend detects `has_schema = false`
- Shows text area (current UI)
- Submits as `{ "prompt": "..." }`
- Backend treats as before

**Mixed mode:**
- Some templates with schemas, some without
- System handles both seamlessly

---

## Field Instruction Patterns

### For Single Text Fields
```json
"field_name": "Simple instruction as string"
```

### For Multi-Paragraph Fields
```json
"paragraph_field": {
  "instructions": "Paragraph 1: X. Paragraph 2: Y."
}
```

### For Table Fields (with Pagination)
```json
"table:schedule": {
  "instructions": "Table generation instructions...",
  "rows_per_slide": 2
}
```

### For Select Fields (Database-Driven)
No special instruction needed — database loads automatically if `database` field is present in cell_structure part.

---

## Testing

**To verify schema system:**

1. Select a template with schema
2. Request `GET /schema/{template_name}` → Should return schema
3. Submit form with `POST /generate-ppt` + form_data → Should validate
4. Check backend logs show "Form data validated successfully"
5. AI response respects form constraints

**Test cases:**
- Required field missing → Error
- Invalid enum value → Error
- Number out of range → Error
- Valid form_data → Generates presentation
- Template without schema → Falls back to text mode

---

## Tips for Creating Templates

1. **Be specific** — Clear constraints guide better AI output
2. **Use examples** — Show what you want in instructions
3. **Group related fields** — Organize schema into logical groups
4. **Include constraints** — Specify what to avoid
5. **Set table pagination** — Configure `rows_per_slide` based on slide design
6. **Use markers for styling** — Wrap important text with formatting conventions
7. **Test without schema first** — Then add schema features incrementally

---

## Related Documentation

- [SCHEMA_DRIVEN_TABLE_SYSTEM.md](SCHEMA_DRIVEN_TABLE_SYSTEM.md) — Complete guide to tables, rows, cells, and pagination
- [TABLE_PAGINATION.md](TABLE_PAGINATION.md) — Deep-dive into pagination logic and `rows_per_slide` configuration
