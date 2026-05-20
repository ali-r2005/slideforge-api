# Template Metadata System

Each PowerPoint template can have a corresponding JSON metadata file that provides custom instructions to the AI.

## File Location

For a template file `template3.pptx`, create a metadata file `template3.json` in the same `templates/` directory.

## Structure

```json
{
  "name": "template_name",
  "description": "Human-readable description of the template",
  "system_instructions": "Overall context and guidelines for AI content generation",
  "tone": "professional, engaging, formal, casual, etc.",
  "field_instructions": {
    "field_name": {
      "instructions": "Specific instructions for this field",
      "rows": 5,
      "column_names": ["Col1", "Col2"]
    }
  },
  "constraints": {
    "key": "value"
  }
}
```

## Examples

### Example 1: Destination Showcase Template

**File:** `template3.json`

```json
{
  "name": "template3",
  "description": "Destination showcase for corporate travel",
  "system_instructions": "Generate engaging travel destination content focused on corporate team-building experiences. Emphasize practical benefits for business groups.",
  "tone": "professional yet engaging",
  "field_instructions": {
    "title": "Keep titles concise and compelling, highlighting the destination's unique appeal",
    "destination_paragraph:paragraphs=2": {
      "instructions": "First paragraph: destination overview and appeal. Second paragraph: practical benefits for corporate groups (weather, activities, logistics).",
      "min_length": "2 sentences per paragraph"
    },
    "destination_name": "Just the city and country name, e.g., 'Tangier, Morocco'"
  },
  "constraints": {
    "focus_on": ["team-building opportunities", "accessibility", "cultural value"],
    "avoid": ["generic tourism clichés"]
  }
}
```

### Example 2: Event Planning Template with Tables

**File:** `event_template.json`

```json
{
  "name": "event_template",
  "description": "Corporate event planning and budget template",
  "system_instructions": "Generate realistic, detailed event planning information with practical details.",
  "tone": "professional and organized",
  "field_instructions": {
    "event_title": "Create an engaging event title that reflects the purpose",
    "event_overview:paragraphs=2": {
      "instructions": "Paragraph 1: Event purpose and target audience. Paragraph 2: Key outcomes and expected impact."
    },
    "budget_table:budget": {
      "instructions": "Create a realistic budget breakdown for a corporate event with these categories in order: Venue, Accommodation, Meals & Catering, Activities, Transport, Materials. Include estimated costs per person.",
      "rows": 6,
      "column_names": ["Category", "Estimated Cost"]
    },
    "schedule_table:timeline": {
      "instructions": "Create a 3-day event schedule with morning, afternoon, and evening activities. Each day should have a theme.",
      "rows": 9,
      "column_names": ["Day", "Time", "Activity", "Location"]
    }
  }
}
```

### Example 3: Training Course Template

**File:** `training_template.json`

```json
{
  "name": "training_template",
  "description": "Professional training course overview",
  "system_instructions": "Generate educational content that is clear, structured, and focused on practical skills and measurable outcomes.",
  "tone": "educational and professional",
  "field_instructions": {
    "course_title": "Make it specific and action-oriented, e.g., 'Advanced Project Management in Digital Transformation'",
    "course_description:paragraphs=3": {
      "instructions": "Paragraph 1: What the course covers. Paragraph 2: Who should take it and why. Paragraph 3: Expected outcomes and skills gained."
    },
    "learning_objectives": "Format as a numbered list of 4-5 specific, measurable objectives",
    "modules_table:modules": {
      "instructions": "List the course modules with descriptions. Include 4-5 core modules.",
      "rows": 5,
      "column_names": ["Module", "Duration", "Key Topics"]
    }
  }
}
```

## Field Instruction Types

### For Single Fields
```json
"field_name": "Simple instruction as string"
```

### For Multi-Value Fields (Tables)
```json
"table_name:key": {
  "instructions": "Detailed instructions for table content",
  "rows": 5,
  "column_names": ["Column 1", "Column 2", "Column 3"]
}
```

### For Multi-Paragraph Fields
```json
"paragraph_field:paragraphs=3": {
  "instructions": "Describe what each paragraph should contain",
  "min_length": "1-2 sentences per paragraph"
}
```

## How It Works

1. **Create the metadata file** alongside your template
2. **Add instructions** for fields that need special handling
3. **Include tone, constraints, and system instructions** for overall guidance
4. **The AI will automatically use these instructions** when generating content

## Tips

- Be specific about table rows, column order, and content expectations
- Describe the tone and style expectations clearly
- Use constraints to avoid unwanted content
- Field instructions override general system instructions
- Keep instructions concise but detailed enough to guide the AI

## Default Behavior

If no metadata file exists for a template:
- Default tone: "professional"
- Default system instructions: none (general instructions only)
- Fields will be generated based on field type alone
