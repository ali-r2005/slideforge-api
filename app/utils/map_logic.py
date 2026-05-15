from pptx.dml.color import RGBColor
import logging

from app.utils.pptx_utils import get_shape_alt_text


def apply_map_logic(slide, replacements):
    """
    Applies custom map highlighting and pointer logic to a slide.
    """
    destination = replacements.get("destination_name", "").lower().strip()
    if not destination:
        return

    all_shapes = []
    shape_id_to_parent = {}

    def collect_shapes(shapes_list, parent_group=None):
        for s in shapes_list:
            all_shapes.append(s)
            shape_id_to_parent[id(s)] = parent_group
            if getattr(s, "shape_type", None) == 6: # Group Shape
                try:
                    collect_shapes(s.shapes, parent_group=s)
                except Exception:
                    pass
    
    collect_shapes(slide.shapes)

    def get_abs_pos(shape):
        """
        Calculates absolute slide position by accounting for group offsets AND scaling.
        PowerPoint groups have internal coordinate systems (chOff/chExt) that can be scaled.
        """
        curr_x, curr_y = float(shape.left), float(shape.top)
        p = shape_id_to_parent.get(id(shape))
        
        while p:
            try:
                # Access the underlying XML for coordinate system info
                xfrm = p._element.grpSpPr.xfrm
                ch_off_x = float(xfrm.chOff.x)
                ch_off_y = float(xfrm.chOff.y)
                ch_ext_cx = float(xfrm.chExt.cx)
                ch_ext_cy = float(xfrm.chExt.cy)
                
                # Calculate scaling ratios (Group size vs Internal coordinate size)
                scale_x = p.width / ch_ext_cx if ch_ext_cx != 0 else 1.0
                scale_y = p.height / ch_ext_cy if ch_ext_cy != 0 else 1.0
                
                # Transform local coordinates to parent coordinates
                curr_x = p.left + (curr_x - ch_off_x) * scale_x
                curr_y = p.top + (curr_y - ch_off_y) * scale_y
            except (AttributeError, ZeroDivisionError):
                # Fallback if XML structure differs
                curr_x += p.left
                curr_y += p.top
                
            p = shape_id_to_parent.get(id(p))
            
        return int(curr_x), int(curr_y)

    target_map_pointer = None
    point_pointer = None
    target_region = None

    for shape in all_shapes:
        alt = get_shape_alt_text(shape).lower()
        if not alt:
            continue

        if alt == "map_pointer":
            target_map_pointer = shape
        elif alt == "point_pointer":
            point_pointer = shape
        else:
            cities = [c.strip().lower() for c in alt.split(",")]
            if destination in cities:
                target_region = shape

    if not target_map_pointer:
        return

    if target_region:
        # 1. Highlight region Yellow
        try:
            target_region.fill.solid()
            target_region.fill.fore_color.rgb = RGBColor(255, 255, 0)
        except Exception as e:
            logging.warning(f"Could not color region: {e}")

        # 2. Get Absolute Target Coordinates
        reg_x, reg_y = get_abs_pos(target_region)
        center_x = reg_x + (target_region.width // 2)
        center_y = reg_y + (target_region.height // 2)

        # 3. Position point_Pointer
        if point_pointer:
            cur_x, cur_y = get_abs_pos(point_pointer)
            target_x = center_x - (point_pointer.width // 2)
            target_y = center_y - (point_pointer.height // 2)
            
            # We calculate the delta in absolute space and apply it to relative space
            point_pointer.left += (target_x - cur_x)
            point_pointer.top += (target_y - cur_y)

        # 4. Position Map_Pointer so its "head" (right edge) is at the center
        cur_x, cur_y = get_abs_pos(target_map_pointer)
        
        # ADJUST THIS: Vertical offset for Map_Pointer. 
        # Negative = move UP, Positive = move DOWN.
        MAP_POINTER_Y_OFFSET = 300999

        # target_x = center_x - width aligns the right edge of the shape to the center
        target_x = center_x - target_map_pointer.width
        target_y = center_y - (target_map_pointer.height // 2) + MAP_POINTER_Y_OFFSET
        
        target_map_pointer.left += (target_x - cur_x)
        target_map_pointer.top += (target_y - cur_y)


