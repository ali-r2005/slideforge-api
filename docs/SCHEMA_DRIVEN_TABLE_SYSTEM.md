# Schema-Driven Table System — Complete Architecture

SlideForge uses a fully schema-driven approach for table design, covering **two independent
systems** that work together: row generation strategies and cell structure parts.

---

## System Overview

### The Two Systems

| System | Purpose | Configured In | Examples |
|--------|---------|----------------|----------|
| **Row Source** | How rows are generated/managed | `row_source` in schema | date_range, user_provided, fixed |
| **Cell Structure** | What goes inside each cell | `cell_structure` in schema | array-textarea, select, text, textarea |

Both are **optional and independent**:
- A table can use `row_source` without `cell_structure` (simple text cells)
- A table can use `cell_structure` without `row_source` (static rows with complex parts)
- Both together create a fully dynamic table

---

## System 1: Row Source — How Rows Are Generated

### Overview

Tables no longer force a single row-generation strategy. Instead, the schema
declaratively specifies **how rows should be created and managed**.

| Row Source Type | Behavior | Use Case |
|---|---|---|
| **date_range** | Frontend auto-generates one row per day between two dates | Event schedules, multi-day agendas |
| **user_provided** | User controls row count via "Add Row" / "Delete Row" buttons | Team lists, attendance, budgets |
| **fixed** | Fixed number of pre-defined rows | Department summaries, scoring sheets |

### Schema Definition

```json
{
  "name": "program_schedule",
  "type": "table",
  "row_source": {
    "type": "date_range",
    "config": {
      "start_field": "event_start_date",
      "end_field": "event_end_date"
    }
  },
  "columns": ["Matinée", "Midi", "Après-midi", "Soir"]
}
```

### Row Generation Flow

```
Schema defines row_source type + config
  ↓
Frontend reads schema
  ↓
Frontend renders appropriate table UI component
  ↓
For date_range: calculates dates, generates rows
For user_provided: shows Add/Delete buttons
For fixed: shows N pre-filled rows
  ↓
User fills cells
  ↓
Frontend sends array of row objects to backend
  ↓
Backend generates PPTX, paginating to extra slides if needed
```

### Row Source Types — Detailed

#### 1. Date Range (`type: "date_range"`)

**Backend Config:**
```json
{
  "row_source": {
    "type": "date_range",
    "config": {
      "start_field": "event_start_date",
      "end_field": "event_end_date"
    }
  }
}
```

**Frontend Behavior:**
- Reads `event_start_date` and `event_end_date` from form data
- Calculates all days between (inclusive)
- Generates one row per day with `date: "YYYY-MM-DD"` key
- Preserves user data if date range shifts
- Supports row-height resizing via mouse drag

**Generated Data:**
```json
[
  { "date": "2025-06-01", "Matinée": "...", "Midi": "...", ... },
  { "date": "2025-06-02", "Matinée": "...", "Midi": "...", ... },
  { "date": "2025-06-03", "Matinée": "...", "Midi": "...", ... }
]
```

#### 2. User Provided (`type: "user_provided"`)

**Schema:**
```json
{
  "row_source": { "type": "user_provided" }
}
```

**Frontend Behavior:**
- Shows "Add Row" button to create new rows
- Each row has a trash icon for deletion
- User controls row count entirely
- Clean, minimal interface

**Generated Data:**
```json
[
  { "Name": "John", "Email": "john@example.com", "Role": "Lead" },
  { "Name": "Jane", "Email": "jane@example.com", "Role": "Support" }
]
```

#### 3. Fixed (`type: "fixed"`)

**Schema:**
```json
{
  "row_source": {
    "type": "fixed",
    "config": { "count": 5 }
  }
}
```

**Frontend Behavior:**
- Shows exactly `count` rows
- Rows pre-numbered in first column
- No add/delete buttons
- Count is immutable

**Generated Data:**
```json
[
  { "row_number": 1, "Department": "Sales", "Budget": "50K" },
  { "row_number": 2, "Department": "Marketing", "Budget": "30K" },
  { ... 3 more rows ... }
]
```

---

## System 2: Cell Structure — What's Inside Each Cell

### Overview

By default, cells are **plain text** (a simple textarea). `cell_structure` allows
cells to contain **multiple named parts**, each with its own type and behavior:
- **array-textarea** — Multiple items in a list
- **select** — Dropdown with database options
- **text** — Single-line input
- **textarea** — Multi-line text

### Schema Definition

```json
{
  "name": "program_schedule",
  "type": "table",
  "columns": ["Matinée", "Midi", "Après-midi", "Soir"],
  "cell_structure": {
    "draggable": true,
    "parts": [
      {
        "name": "context",
        "type": "array-textarea",
        "label": "Context/Setup",
        "required": true,
        "ai_generates": true,
        "user_provides": true
      },
      {
        "name": "team_building",
        "type": "select",
        "label": "Team Building",
        "database": "tb",
        "required": false,
        "ai_generates": false,
        "user_provides": true
      },
      {
        "name": "agency_offer",
        "type": "textarea",
        "label": "Agency Offers",
        "required": false,
        "ai_generates": true,
        "user_provides": true
      }
    ]
  }
}
```

### Cell Part Types

#### Array Textarea
Multiple text items (one per line). Each item becomes a separate paragraph in the cell.

```json
{
  "name": "context",
  "type": "array-textarea",
  "label": "Context",
  "ai_generates": true,
  "user_provides": true
}
```

Data: `["Setup item 1", "Setup item 2", "Setup item 3"]`

#### Select
Dropdown populated from a database file. Displays human-readable name, stores ID.

```json
{
  "name": "team_building",
  "type": "select",
  "label": "Activity",
  "database": "tb",
  "ai_generates": false,
  "user_provides": true
}
```

Database file: `DB/tb.json`
```json
[
  { "id": 1, "name": "Escape the Maze" },
  { "id": 2, "name": "Team Challenge" }
]
```

Data: `1` (the selected ID)

#### Text
Single-line text input.

```json
{
  "name": "title",
  "type": "text",
  "label": "Activity Name"
}
```

#### Textarea
Multi-line text (single field).

```json
{
  "name": "description",
  "type": "textarea",
  "label": "Notes"
}
```

### Part Metadata

Each part has optional metadata that guides form validation and AI generation:

```json
{
  "name": "context",
  "type": "array-textarea",
  "label": "Context/Setup",
  "required": true,              // User must fill this
  "ai_generates": true,          // AI can generate this part
  "user_provides": true          // User can provide this part
}
```

### Backend: Database Loading

For select parts with a `database` field, the backend:
1. Loads the database file from `DB/{name}.json`
2. Validates that every item has `id` and `name`
3. Pre-loads options into the schema response so the frontend doesn't need extra API calls
4. Returns clear error messages if the database is missing or invalid

Database must be valid JSON with this structure:
```json
[
  { "id": 1, "name": "Option 1" },
  { "id": 2, "name": "Option 2" }
]
```

### Frontend: Rendering Parts

The `TableCellHandler` component dynamically renders each part based on its `type`:
- **array-textarea** → Multiple textareas with add/remove buttons
- **select** → Dropdown using pre-loaded options from the schema
- **text** / **textarea** → Input fields

All parts use the template's font, color, and paragraph formatting.

### Data Structure

When `cell_structure` is present, each cell contains a **record of parts**:

```json
{
  "context": ["item 1", "item 2"],        // array-textarea → array
  "team_building": 2,                      // select → ID value
  "agency_offer": "Some description"       // textarea → string
}
```

Without `cell_structure`, cells are just **strings**:

```json
"This is plain text"
```

---

## How They Work Together: End-to-End Example

### Setup: Event Program with Dynamic Parts

**Schema:**
```json
{
  "name": "program_schedule",
  "type": "table",
  "row_source": {
    "type": "date_range",
    "config": { "start_field": "event_start_date", "end_field": "event_end_date" }
  },
  "columns": ["Matinée", "Midi", "Après-midi", "Soir"],
  "cell_structure": {
    "parts": [
      { "name": "context", "type": "array-textarea", ... },
      { "name": "team_building", "type": "select", "database": "tb", ... },
      { "name": "agency_offer", "type": "textarea", ... }
    ]
  }
}
```

### Flow

```
1. User selects:
   - event_start_date: "2025-06-01"
   - event_end_date: "2025-06-03"

2. Frontend generates 3 rows (one per day):
   [
     { "date": "2025-06-01", "Matinée": {...}, "Midi": {...}, ... },
     { "date": "2025-06-02", "Matinée": {...}, "Midi": {...}, ... },
     { "date": "2025-06-03", "Matinée": {...}, "Midi": {...}, ... }
   ]

3. User fills cells:
   program_schedule = [
     {
       "date": "2025-06-01",
       "Matinée": {
         "context": ["Opening remarks", "Team introduction"],
         "team_building": 1,
         "agency_offer": "Offered by Tendencia"
       },
       "Midi": { ... },
       ...
     },
     { ... day 2 ... },
     { ... day 3 ... }
   ]

4. User submits form

5. Backend receives the form_data:
   - Validates schema + cell_structure
   - Validates each part (required, type, etc.)
   - Builds enhanced prompt with part order from schema
   - Tells AI: "Generate in order: context → team_building → agency_offer"
   - AI returns flat array: ["context 1", "context 2", "team desc", "offers"]
   - Table service inserts as multiple paragraphs with template formatting

6. PPTX generated:
   - Each cell has its parts rendered in schema order
   - Fonts, colors, spacing preserved
   - If 3 rows fit per slide, pagination creates extra slides
   - Each slide is a styled duplicate preserving images, title, etc.
```

---

## Pagination: When Rows Overflow a Single Slide

### The Problem

A PowerPoint table doesn't auto-flow to a second slide. If too many rows are
generated, they spill off the bottom.

### The Solution

SlideForge automatically **splits rows into chunks and duplicates the table
slide** for each chunk, preserving all styling, images, and shared content.

### Configuration: `rows_per_slide`

Set in the table's `field_instructions` entry:

```json
{
  "field_instructions": {
    "table:programme": {
      "rows_per_slide": 1,
      "instructions": "...",
      "formatting_conventions": [ ... ]
    }
  }
}
```

**Resolution order:**
1. Explicit `rows_per_slide` in `field_instructions` → use it
2. Otherwise infer from the template table's body-row count → use that
3. Fallback: 1 row per slide

See [TABLE_PAGINATION.md](TABLE_PAGINATION.md) for detailed pagination logic.

---

## Backend Implementation

### Key Files

| File | Purpose |
|------|---------|
| `app/utils/schema_loader.py` | Validate schema + row_source + cell_structure |
| `app/utils/schema_validator.py` | Validate form data against schema |
| `app/utils/database_loader.py` | Load + validate database files for select parts |
| `app/utils/marker_parser.py` | Parse field-specific formatting markers from AI output |
| `app/services/pptx_service.py` | Generate PPTX, coordinate text/image/table filling, pagination |
| `app/services/table_service.py` | Table operations: fill, row addition, cell formatting |
| `app/services/slide_service.py` | Slide duplication with relationship remapping (for pagination) |
| `app/services/enhanced_prompt_builder.py` | Build AI prompt, respecting part order from `cell_structure.parts` |

### Validation Flow

```
Form submission (form_data)
  ↓
SchemaValidator.validate(form_data, schema)
  ↓
For each field:
  - Type check (text, number, date, enum, table, ...)
  - Length check (if text/textarea)
  - Range check (if number)
  - Required check (if marked required)
  - For table fields:
    - Row count check
    - If cell_structure: validate each part against its type
  ↓
✅ Valid → proceed to AI / PPTX generation
❌ Invalid → return detailed error to frontend
```

### AI Output Processing

The enhanced prompt builder **respects cell_structure part order**:

1. Reads `schema["fields"][table_field]["cell_structure"]["parts"]`
2. Builds prompt: "Return output as ordered array: [part1 items, part2 item, part3 items, ...]"
3. AI returns flat array respecting the order
4. Table service inserts as consecutive paragraphs with consistent spacing

This ensures multi-part cells always render in the intended sequence.

---

## Frontend Implementation

### Key Files

| File | Purpose |
|------|---------|
| `hooks/useSchema.ts` | Load schema, define RowSource + CellStructure types |
| `components/presentation/schema-form.tsx` | Render form fields, coordinate table filling |
| `components/presentation/DynamicTableField.tsx` | Route to DateRangeTable, UserProvidedTable, or FixedTable |
| `components/presentation/TableCellHandler.tsx` | Render cell parts (array-textarea, select, text, textarea) |

### Form Data Structure

Tables in the form use this shape:

```typescript
{
  program_schedule: [
    {
      date: "2025-06-01",                           // date_range only
      "Matinée": { ... },                           // if cell_structure
      "Midi": "plain text",                         // if no cell_structure
      ...
    },
    { ... }
  ]
}
```

---

## Migration from Hardcoded Approach

### Before

```javascript
// Cell structure was hardcoded in ProgramTableCell.tsx
const sections = ["context", "team_building", "agency_offer"];
```

```python
# Row source was hardcoded to date-range only
date_range_start_field = "event_start_date"
date_range_end_field = "event_end_date"
```

### After

Everything is in the **schema**. No code changes needed to reconfigure.

```json
{
  "row_source": { "type": "date_range", ... },
  "cell_structure": { "parts": [ ... ] }
}
```

---

## Backward Compatibility

✅ Legacy fields still supported:
- Old `date_range_start_field` / `date_range_end_field` in schema work if `row_source` is absent
- Old `cell_structure.parts` as string array (e.g., `["context", "team_building"]`) works with fallback

---

## Documentation

| Document | Covers |
|----------|--------|
| [TABLE_PAGINATION.md](TABLE_PAGINATION.md) | How rows paginate across slides, `rows_per_slide` configuration |
| [TABLE_ROW_SOURCE_ARCHITECTURE.md](TABLE_ROW_SOURCE_ARCHITECTURE.md) | Detailed row generation strategies |
| [DYNAMIC_TABLE_IMPLEMENTATION.md](../slideforge-web/docs/DYNAMIC_TABLE_IMPLEMENTATION.md) | Frontend table components |
| [TEMPLATE_METADATA_EXAMPLE.md](TEMPLATE_METADATA_EXAMPLE.md) | Example metadata file structure |

---

## Verification Checklist

- [x] Backend validates row_source + cell_structure
- [x] Frontend DynamicTableField routes by row_source.type
- [x] DateRangeTable generates rows, preserves data on date shifts
- [x] UserProvidedTable adds/deletes rows
- [x] FixedTable shows N fixed rows
- [x] TableCellHandler renders all part types
- [x] Select parts load database options
- [x] AI respects part order from schema
- [x] Table pagination duplicates slides correctly
- [x] Images, titles, shared content preserved on paginated slides
- [x] Form validation enforces schema constraints

---

## Quick Reference: Configuring a New Table

### Minimal: Plain Text Table

```json
{
  "name": "my_table",
  "type": "table",
  "row_source": { "type": "user_provided" },
  "columns": ["Name", "Email"]
}
```

### Complete: Dynamic Parts + Date Range + Pagination

```json
{
  "name": "schedule",
  "type": "table",
  "row_source": {
    "type": "date_range",
    "config": { "start_field": "start_date", "end_field": "end_date" }
  },
  "columns": ["Morning", "Afternoon", "Evening"],
  "cell_structure": {
    "draggable": true,
    "parts": [
      { "name": "activity", "type": "text", "label": "Activity", "required": true },
      { "name": "notes", "type": "textarea", "label": "Notes", "required": false }
    ]
  }
}
```

And in `field_instructions`:

```json
{
  "field_instructions": {
    "table:schedule": {
      "rows_per_slide": 2,
      "instructions": "Generate activity descriptions.",
      "formatting_conventions": [ ... ]
    }
  }
}
```

---

## Questions?

See the specific architecture documents linked above, or check `template7.json` for a
real example.
