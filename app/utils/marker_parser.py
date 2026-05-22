import re
from typing import Dict, Any, List, Optional


class MarkerParser:
    """Parses text with markers based on field-specific formatting conventions."""

    def __init__(self, field_conventions: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize with conventions from field_instructions[field_name].

        Args:
            field_conventions: List of convention dicts from template metadata
        """
        self.conventions = {}
        if field_conventions:
            for convention in field_conventions:
                marker = convention.get("marker")
                if marker:
                    self.conventions[marker] = convention

    @staticmethod
    def for_field(template_metadata: Dict[str, Any], field_placeholder: str):
        """
        Create a MarkerParser instance for a specific field placeholder.

        Args:
            template_metadata: The template metadata with field_instructions
            field_placeholder: The field placeholder name (e.g., "program_schedule")

        Returns:
            MarkerParser instance with conventions for that field only
        """
        field_instructions = template_metadata.get("field_instructions", {})
        field_meta = field_instructions.get(field_placeholder, {})

        conventions = None
        if isinstance(field_meta, dict):
            conventions = field_meta.get("formatting_conventions")

        return MarkerParser(conventions)

    def parse_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse marked text into segments with formatting info.

        Only recognizes markers defined for this field. Unknown markers are ignored.

        Args:
            text: Text potentially containing markers like $$marker$$content$$marker$$

        Returns:
            List of segments with type, content, marker, and style information:
            [{type: "text"|"marked", content: str, marker: str|None, style: dict|None}, ...]
        """
        if not text:
            return []

        segments = []
        current_pos = 0
        # Pattern matches $$marker$$content$$marker$$
        pattern = r'\$\$(\w+)\$\$(.*?)\$\$\1\$\$'

        for match in re.finditer(pattern, text):
            marker = f"$${match.group(1)}$$"
            content = match.group(2)
            start = match.start()
            end = match.end()

            # Only process markers recognized for this field
            if marker not in self.conventions:
                continue

            # Add text before marker
            if start > current_pos:
                segments.append({
                    "type": "text",
                    "content": text[current_pos:start],
                    "marker": None,
                    "style": None
                })

            # Add marked content
            convention = self.conventions[marker]
            segments.append({
                "type": "marked",
                "content": content,
                "marker": marker,
                "convention_name": convention.get("name"),
                "style": convention.get("pptx_style", {})
            })

            current_pos = end

        # Add remaining text
        if current_pos < len(text):
            segments.append({
                "type": "text",
                "content": text[current_pos:],
                "marker": None,
                "style": None
            })

        # If no markers found, return original text as single segment
        if not segments:
            segments.append({
                "type": "text",
                "content": text,
                "marker": None,
                "style": None
            })

        return segments

    def get_pptx_runs(self, text: str) -> List[Dict[str, Any]]:
        """
        Get text runs formatted for PowerPoint insertion.

        Converts parsed segments into a format suitable for python-pptx:
        Each segment becomes a run with text and formatting properties.

        Args:
            text: Text to parse and format

        Returns:
            List of run dicts for PowerPoint insertion:
            [{text: str, color: hex|None, bold: bool, italic: bool, font_size: int|None}, ...]
        """
        segments = self.parse_text(text)
        runs = []

        for segment in segments:
            style = segment.get("style") or {}
            run = {
                "text": segment["content"],
                "color": style.get("color"),
                "bold": style.get("bold", False),
                "italic": style.get("italic", False),
                "font_size": style.get("font_size")
            }
            runs.append(run)

        return runs
