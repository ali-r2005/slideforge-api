# Table System Guide

## Overview

The refactored table system extracts headers and formatting from template tables, then fills them with object-based data while preserving the original styling.

## How It Works

### 1. **Template Structure**

Your PowerPoint template should have a table with:
- **Row 0 (Header)**: Column names (Name, Email, Phone, etc.)
- **Row 1 (Template)**: Placeholder row with desired formatting (italic, bold, color, size)

```
┌─────────────┬──────────────┬───────────┐
│ Name        │ Email        │ Phone     │  ← Row 0: Header
├─────────────┼──────────────┼───────────┤
│ [template]  │ [template]   │ [template]│  ← Row 1: Template with formatting
└─────────────┴──────────────┴───────────┘
```

### 2. **Automatic Extraction**

When extracting template metadata, the system automatically:
- ✅ Extracts header names: `["Name", "Email", "Phone"]`
- ✅ Extracts template formatting (font, size, color, bold, italic)
- ✅ Passes headers to AI in the prompt

### 3. **AI Response Format**

The AI receives instructions to return a **list of objects** (not list of lists):

```json
{
  "table:employees": [
    {
      "Name": "Alice Johnson",
      "Email": "alice@company.com",
      "Phone": "555-1234"
    },
    {
      "Name": "Bob Smith",
      "Email": "bob@company.com",
      "Phone": "555-5678"
    }
  ]
}
```

### 4. **Automatic Filling**

The system:
- ✅ Reads the object keys (Name, Email, Phone)
- ✅ Maps them to the correct columns using header names
- ✅ Applies template row formatting to all new rows
- ✅ Adds new rows as needed for each object

## Example

### Template in PowerPoint

```
Alt Text: {{table:employees}}

Header Row:     [Name]              [Email]                [Phone]
Template Row:   [template text]     [template@email.com]   [555-1234]
                (Italic, 12pt)      (Italic, 12pt)         (Italic, 12pt)
```

### AI Prompt

```
Field: table:employees
- Type: table
- Columns: 3
- Column headers: 'Name', 'Email', 'Phone'
```

### AI Response

```json
{
  "table:employees": [
    {"Name": "Alice", "Email": "alice@company.com", "Phone": "555-1234"},
    {"Name": "Bob", "Email": "bob@company.com", "Phone": "555-5678"}
  ]
}
```

### Generated Table

```
┌─────────────┬──────────────────┬───────────┐
│ Name        │ Email            │ Phone     │  ← Header (unchanged)
├─────────────┼──────────────────┼───────────┤
│ Alice       │ alice@company.com│ 555-1234  │  ← Row with template formatting
├─────────────┼──────────────────┼───────────┤
│ Bob         │ bob@company.com  │ 555-5678  │  ← Row with template formatting
└─────────────┴──────────────────┴───────────┘
```

All rows have **italic, 12pt font** - inherited from the template row!

## Template Metadata Support

You can add special table instructions in your template metadata file:

**templates/event_template.json**
```json
{
  "field_instructions": {
    "table:attendees": {
      "instructions": "Create a list of attendees with their roles and contact info. Ensure realistic names and valid email formats.",
      "rows": 8
    }
  }
}
```

## Data Format Support

The system supports **both** formats for backward compatibility:

### Object Format (Recommended)
```json
[
  {"Name": "Alice", "Email": "alice@example.com"},
  {"Name": "Bob", "Email": "bob@example.com"}
]
```

### List Format (Legacy)
```json
[
  ["Alice", "alice@example.com"],
  ["Bob", "bob@example.com"]
]
```

## Extracted Formatting

The system extracts and applies these formatting properties:
- ✅ Font name
- ✅ Font size
- ✅ Bold
- ✅ Italic
- ✅ Underline
- ✅ Paragraph alignment

## Validation

The AI validation now:
- ✅ Accepts objects with column header keys
- ✅ Validates all required headers are present
- ✅ Still supports list format for compatibility
- ✅ Checks for correct column count

## Files Modified

1. **pptx_service.py**
   - `extract_table_headers()` - Extracts header row
   - `extract_template_row_formatting()` - Extracts template formatting
   - `apply_cell_formatting()` - Applies formatting to cells
   - `fill_table()` - Refactored to handle objects and apply formatting

2. **prompts.py**
   - Updated system prompt to expect object format
   - Added column headers to field descriptions
   - Added formatting helper functions

3. **ai_validation.py**
   - Validates object format for tables
   - Checks required headers match column names

4. **endpoints.py**
   - Passes column headers to fill_table()

## Best Practices

1. **Template Row Formatting**
   - Apply consistent formatting to the template row
   - It will be inherited by all generated rows
   - Test with different fonts/colors to ensure consistency

2. **Header Names**
   - Use clear, descriptive header names
   - Avoid special characters
   - Match these names in AI instructions

3. **Column Count**
   - Ensure the number of columns matches your data
   - Add extra columns if you might need them later

4. **AI Instructions**
   - Provide specific guidance on table content
   - Mention number of rows if important
   - Describe the type of data in each column

## Troubleshooting

**Problem**: Table headers not extracted
- Check that the table has at least 2 rows (header + template)
- Verify headers are text in the first row

**Problem**: Formatting not applied
- Ensure template row (row 1) has proper formatting
- Check that formatting properties are set on the run level, not paragraph

**Problem**: AI returning wrong format
- Verify the system prompt mentions object format
- Check column headers are listed in the prompt
- Review the field instructions for clarity

## Example: Budget Table

**Template Metadata**
```json
{
  "field_instructions": {
    "table:budget": {
      "instructions": "Create a realistic budget breakdown. Categories: Venue, Accommodation, Meals, Activities, Transport. Include realistic costs per person.",
      "rows": 5
    }
  }
}
```

**AI Response**
```json
{
  "table:budget": [
    {"Category": "Venue", "Cost": "$150"},
    {"Category": "Accommodation", "Cost": "$200"},
    {"Category": "Meals", "Cost": "$75"},
    {"Category": "Activities", "Cost": "$100"},
    {"Category": "Transport", "Cost": "$50"}
  ]
}
```

**Generated Table**
All rows inherit formatting from template row - consistent professional appearance!
