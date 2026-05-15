def get_shape_alt_text(shape):
    """
    Robustly retrieves Alt Text from any shape type by searching the underlying XML.
    PowerPoint stores Alt Text in the 'descr' attribute.
    """
    try:
        # Search for the 'descr' attribute in the shape's XML element
        return shape._element.xpath('.//@descr')[0].strip()
    except Exception:
        # Fallback: check if the shape name matches (Selection Pane name)
        return getattr(shape, "name", "").strip()
