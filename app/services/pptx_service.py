from pptx import Presentation

# metadata extraction and presentation generation logic will be use by an ai agent to create pptx files based on user input and a template file. The pptx template will have placeholders like {{title}}, {{summary}}, etc. which will be replaced by the ai agent with actual content before generating the final presentation.
def extract_ppt_metadata(template_path: str):
    presentation = Presentation(template_path)

    slides_data = []

    for slide_index, slide in enumerate(presentation.slides):
        slide_info = {
            "slide_number": slide_index + 1,
            "shapes": []
        }

        for shape_index, shape in enumerate(slide.shapes):

            if hasattr(shape, "text"):
                slide_info["shapes"].append({
                    "shape_index": shape_index,
                    "text": shape.text
                })

        slides_data.append(slide_info)

    return slides_data

def generate_presentation(
    template_path: str,
    output_path: str,
    replacements: dict
):

    presentation = Presentation(template_path)

    for slide in presentation.slides:
        for shape in slide.shapes:

            if hasattr(shape, "text"):

                for key, value in replacements.items():

                    placeholder = f"{{{{{key}}}}}"

                    if placeholder in shape.text:
                        shape.text = shape.text.replace(
                            placeholder,
                            value
                        )

    presentation.save(output_path)

    return output_path