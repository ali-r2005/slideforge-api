# Table Pagination (`rows_per_slide`)

This document explains how SlideForge handles tables whose rows don't all fit on
one slide, and **where to configure** the per-slide row capacity.

## The Problem

A PowerPoint table does **not** automatically flow onto a second slide. If a
table is filled with more rows than fit in the slide area, the extra rows spill
past the bottom edge and are effectively lost.

SlideForge solves this by **splitting the rows into chunks and duplicating the
table slide** for each chunk — preserving the original styling, fonts, colors,
images, and any other content on that slide.

## How It Works (High Level)

```
1. Fill normal placeholders (titles, images, text) on every slide.
2. When a table is found, it is NOT filled immediately — it is recorded as a job.
3. Original placeholder shapes are cleaned up.
4. Pagination pass (per table job):
     a. Decide rows_per_slide  (see "Where to Configure" below)
     b. Split rows into chunks of that size
     c. Chunk 1  -> fill the original slide's table
     d. Chunk 2+ -> duplicate the slide, reset its table, fill with the chunk
```

Tables are filled **last** (after every other placeholder is rendered) so that
each duplicated slide is an exact copy of a fully-rendered slide — shared
content (title, picture, group shapes) carries over identically with no
re-processing.

### Slide Duplication

`python-pptx` has no native slide-copy, so duplication (`app/services/slide_service.py`):

- Deep-copies every shape element from the source slide.
- **Remaps relationship IDs** so copied pictures/media keep pointing at valid
  image parts (a copied picture references `rId3`, but the new slide needs its
  own `rId3` — these are renumbered automatically).
- Inserts each copy immediately after the previous one, preserving order.

### Table Reset

Before filling, each table (original and continuation) is reset to its template
shape — the header row plus a single empty template row
(`table_service.reset_table_to_template`). Rows are then grown to match the chunk
exactly, so there are never leftover empty template rows, and all rows inherit
the template row's styling.

---

## Where to Configure `rows_per_slide` — The Convention

> **Convention: set `rows_per_slide` inside the table's `field_instructions`
> entry, keyed by the placeholder name (e.g. `"table:programme"`).**

```json
{
  "field_instructions": {
    "table:programme": {
      "label": "Program Schedule",
      "rows_per_slide": 1,
      "instructions": "...",
      "formatting_conventions": [ ... ]
    }
  }
}
```

### Why `field_instructions`

- It is keyed by the **exact placeholder name** (`table:programme`), so it
  unambiguously targets one specific table — this works even for templates
  that contain **multiple tables**.
- It keeps every per-table setting (label, instructions, formatting
  conventions, and now pagination) in **one block per placeholder**.
- The value is available at fill time directly from the placeholder name, with
  no schema-field lookup needed.

The `schema` block is **not** used for `rows_per_slide`. Keep the schema focused
on the data/form definition (`columns`, `row_source`, `cell_structure`).

---

## Resolution Order

When deciding how many rows fit per slide, the backend checks, in order:

1. **`field_instructions["table:<name>"].rows_per_slide`** — the convention.
   Used when present.
2. **Inferred** — the number of body rows the designer drew in the template
   table (header excluded). The template declares its own capacity. Falls back
   to `1`.

Implemented in `app/services/pptx_service.py::_determine_rows_per_slide`.

### Two Cases in Practice

**Case A — User set it (explicit).** A number exists in the table's
`field_instructions` entry. It is used as-is.

```
"rows_per_slide": 3   ->   always 3 rows per slide
```

**Case B — Nobody set it (inferred).** No number anywhere. The backend counts
the template table's existing body rows and uses that — the designer laid the
table out to fit the slide, so the table tells us its own capacity.

```
template7 table has 1 body row   ->   inferred = 1 row per slide
```

---

## Example: `template7`

`template7` has one table (`table:programme`) whose rows are generated per day
from a date range. Its `.pptx` table has a header row + 1 template row, and the
metadata sets `"rows_per_slide": 1` in `field_instructions["table:programme"]`.

- **`"rows_per_slide": 1`** → one day per slide (matches the dense layout).
- **`"rows_per_slide": 3`** → 7 days produce chunks `[3, 3, 1]` → 3 table
  slides, each a styled copy of the original with its picture intact.
- **Field removed entirely** → inferred = **1 row/slide** (the template's body
  row count), same result.

---

## Limitations

- **Fixed count, not measured.** `python-pptx` has no rendering engine, so true
  row-height measurement is impossible. A row whose cells hold unusually long
  content can still overflow even within the configured count. Choose
  `rows_per_slide` conservatively for content-heavy tables.
- **One paginated table per slide.** Duplicating a slide copies everything on
  it; templates are expected to have a single paginated table per slide.

## Related Files

| File | Role |
|------|------|
| `app/services/pptx_service.py` | Pagination pass + `rows_per_slide` resolution |
| `app/services/slide_service.py` | Slide duplication with relationship remapping |
| `app/services/table_service.py` | `reset_table_to_template`, `count_template_body_rows` |
| `templates/template7.json` | Example table field |

## Related Docs

- `TABLE_ROW_SOURCE_ARCHITECTURE.md` — how table rows are generated
- `TABLE_SYSTEM_GUIDE.md` — overall table system
- `TEMPLATE_METADATA_EXAMPLE.md` — metadata file structure
