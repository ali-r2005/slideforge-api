# Schema-Driven Form System - Implementation Guide

## What I've Created So Far

### **Backend Files (Phase 1: Infrastructure)**

#### **1. Schema Files** (`templates/schemas/`)
- `template3-schema.json` - Example schema for destination template
- `event_template-schema.json` - Example schema for event planning template

**What they contain:**
- Field definitions (name, type, label, required, constraints)
- Validation rules (min, max, max_length, enum values)
- Support for date ranges (start_date, end_date)
- Optional/required field configuration

#### **2. Schema Loader** (`app/utils/schema_loader.py`)
**Responsibilities:**
- Load JSON schemas from `templates/schemas/` folder
- Validate schema structure
- Cache schemas for performance
- Return None if schema doesn't exist (graceful fallback)

**Key functions:**
```python
load_schema(template_name)  # Load a schema
has_schema(template_name)   # Check if schema exists
get_field_by_name()         # Get specific field definition
```

#### **3. Schema Validator** (`app/utils/schema_validator.py`)
**Responsibilities:**
- Validate form_data against schema
- Type checking (text, number, email, date, enum, boolean)
- Constraint validation (min, max, max_length, required)
- Filter out optional empty fields before sending to AI

**Key functions:**
```python
SchemaValidator.validate()           # Validate and return errors
SchemaValidator.filter_optional_fields()  # Clean up optional empty fields
```

#### **4. Enhanced Prompt Builder** (`app/utils/enhanced_prompt_builder.py`)
**Responsibilities:**
- Combine user_prompt with form_data
- Format structured parameters as readable text
- Add AI instructions to respect parameters as constraints

**Example output:**
```
User request text here...

Structured Parameters:
- Destination: Marrakech
- Budget: $5000
- Event Date: 2026-06-15

IMPORTANT: Treat the above Structured Parameters as strict constraints...
```

---

## What Needs to Happen Next

### **Phase 2: API Endpoints (Backend)**

**Task 1: Add New Endpoint - GET /schema/{template_name}**
- Load schema using schema_loader
- Return schema JSON or empty object if not found
- Used by frontend to know what form to show

**Task 2: Modify POST /generate-ppt Endpoint**
- Accept new optional parameter: `form_data`
- Validate form_data using schema_validator (if schema exists)
- Return validation errors if data is invalid
- Build enhanced prompt using enhanced_prompt_builder
- Send enhanced prompt to AI instead of plain user_prompt

**Task 3: Update Request Schema**
```python
# Current
GeneratePresentationRequest:
  template_name: str
  prompt: str

# New
GeneratePresentationRequest:
  template_name: str
  prompt: str (optional if form_data provided)
  form_data: dict (optional)
```

---

### **Phase 3: Frontend Components (UI)**

**Task 1: Create Schema Hook**
- `hooks/useSchema.ts`
- Fetch schema for selected template
- Detect: has_schema vs no_schema mode
- Cache schema in state

**Task 2: Create Dynamic Form Component**
- `components/schema-form.tsx`
- Render form fields based on schema
- Support 7 field types: text, textarea, number, email, date, enum, boolean
- Client-side validation
- Date range handling (start_date, end_date paired)

**Task 3: Update Template Generator Form**
- `components/presentation/template-generator-form.tsx`
- Fetch schema when template is selected
- Show:
  - If has schema: Dynamic form + Optional user prompt area
  - If no schema: Current text area (backward compatible)
- Handle form submission with form_data

**Task 4: Update Types**
```typescript
GeneratePresentationPayload:
  template_name: string
  prompt?: string  // Optional if form_data exists
  form_data?: Record<string, string | number | boolean>
```

---

## Data Flow Diagram

```
Frontend:
┌─────────────────────────────────────┐
│ User selects template               │
│          ↓                           │
│ Fetch schema (GET /schema/{name})   │
│          ↓                           │
│ Has schema? YES / NO                │
│     ├─ YES → Show dynamic form      │
│     └─ NO  → Show text area         │
│          ↓                           │
│ User fills form + prompt (optional) │
│          ↓                           │
│ Submit: form_data + prompt          │
└─────────────────────────────────────┘
             ↓
Backend:
┌─────────────────────────────────────┐
│ POST /generate-ppt (form_data)      │
│          ↓                           │
│ Load schema                         │
│          ↓                           │
│ Validate form_data                  │
│  - Check required fields ✓          │
│  - Type validation ✓                │
│  - Constraint validation ✓          │
│          ↓                           │
│ If invalid: Return errors           │
│ If valid:                           │
│  ├─ Filter optional empty fields    │
│  ├─ Build enhanced prompt           │
│  └─ Send to AI                      │
│          ↓                           │
│ Generate presentation               │
└─────────────────────────────────────┘
             ↓
Frontend:
│ Show generated presentation         │
```

---

## Field Types Supported

| Type | Example | Validation | Notes |
|------|---------|-----------|-------|
| `text` | "Team Building" | max_length | Single line input |
| `textarea` | "Description..." | max_length | Multi-line input |
| `number` | 5000 | min, max | Integer or float |
| `email` | user@example.com | email format | Basic @ and . check |
| `date` | 2026-06-15 | date format | YYYY-MM-DD format |
| `enum` | "Marrakech" | values list | Dropdown options |
| `boolean` | true/false | - | Checkbox/toggle |

---

## How Date Ranges Work

**Schema Definition:**
```json
{
  "name": "event_date_range_start",
  "type": "date",
  "required": false
},
{
  "name": "event_date_range_end",
  "type": "date",
  "required": false
}
```

**Frontend:**
- Two separate date pickers
- Submitted as: `{ "event_date_range_start": "2026-06-15", "event_date_range_end": "2026-06-17" }`

**AI Prompt:**
```
Structured Parameters:
- Event Date Range: 2026-06-15 to 2026-06-17
```

---

## Error Handling Strategy

**Validation Errors (Frontend):**
- Show error messages under fields
- Prevent form submission if invalid
- Clear errors when user fixes field

**Validation Errors (Backend):**
- Return 400 Bad Request with error list
- Frontend displays: "Form validation failed: [errors]"
- User can fix and resubmit

**Example error response:**
```json
{
  "detail": "Form validation failed: Field 'destination_name' is required; Field 'event_budget' must be a number"
}
```

---

## Backward Compatibility

**Templates WITHOUT schema:**
- Frontend detects has_schema = false
- Shows text area (current UI)
- Submits as: `{ "prompt": "..." }`
- Backend treats as before (no validation)

**Mixed mode:**
- Some templates with schemas, some without
- System handles both seamlessly

---

## What's Ready

✅ Schema file format and examples
✅ Schema loader with caching
✅ Schema validator with all field types
✅ Enhanced prompt builder
✅ All utilities syntax-checked

## What's Next

1. **Backend Endpoints** - Add GET /schema and update POST /generate-ppt
2. **Frontend Hooks** - Create useSchema hook
3. **Frontend Components** - Create schema-form component
4. **Integration** - Wire everything together
5. **Testing** - Test both schema and no-schema modes

---

## Testing the Schema System

**To test locally:**
1. Create a schema file for your template
2. Request GET /schema/{template_name} → Should return schema
3. Submit form_data with POST /generate-ppt → Should validate and generate
4. Check AI response respects the Structured Parameters

**Test cases to cover:**
- Required field missing → Error
- Invalid enum value → Error
- Number out of range → Error
- Valid form_data → Generates presentation
- Template without schema → Falls back to text mode
