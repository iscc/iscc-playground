# -*- coding: utf-8 -*-
import base64
import io
import gradio as gr
import iscc_core as ic
import iscc_sdk as idk
import iscc_sci as sci
import iscc_schema as iss
from PIL import Image
import json

idk.sdk_opts.image_thumbnail_size = 240
idk.sdk_opts.image_thumbnail_quality = 80

custom_css = """
.fixed-height img {
    height: 240px;  /* Fixed height */
    object-fit: contain;  /* Scale the image to fit within the element */
}
"""


def generate_iscc(file):
    imeta = idk.code_iscc(file.name)
    thumbnail = None
    if imeta.thumbnail:
        header, encoded = imeta.thumbnail.split(",", 1)
        data = base64.b64decode(encoded)
        thumbnail = Image.open(io.BytesIO(data))
    metadata = imeta.dict(exclude_unset=False, by_alias=True)
    if metadata.get("thumbnail"):
        del metadata["thumbnail"]
    return (
        imeta.iscc,
        thumbnail,
        imeta.name,
        imeta.description,
        json.dumps(metadata, indent=2),
        None,
    )


with gr.Blocks(title="ISCC Generator", css=custom_css) as demo:
    gr.Markdown("## ⚙️ ISCC Generator")
    with gr.Row():
        in_file = gr.File(label="Media File")
    with gr.Row():
        out_iscc = gr.Text(
            label="ISCC",
            info="GENERATED FROM MEDIA FILE",
            show_copy_button=True,
            show_label=True,
        )
    with gr.Row(variant="panel", equal_height=False):
        with gr.Column():
            out_thumbnail = gr.Image(
                label="Extracted Thumbnail",
                elem_classes=["fixed-height"],
                height=240,
                show_download_button=False,
            )
        with gr.Column(scale=3):
            with gr.Group():
                out_name = gr.Text(label="Name", show_copy_button=True)
                out_description = gr.Textbox(
                    label="Description", lines=4, max_lines=4, show_copy_button=True
                )

    with gr.Row():
        with gr.Accordion(label="ISCC Metadata", open=False):
            out_meta = gr.Code(language="json", label="JSON-LD")
    in_file.upload(
        generate_iscc,
        inputs=[in_file],
        outputs=[out_iscc, out_thumbnail, out_name, out_description, out_meta, in_file],
    )

    # Custom footer
    footer = (
        "https://github.com/iscc"
        f" | iscc-core v{ic.__version__}"
        f" | iscc-sdk v{idk.__version__}"
        f" | iscc-sci v{sci.__version__}"
        f" | iscc-schema v{iss.__version__}"
    )
    gr.Markdown(
        footer,
    )


if __name__ == "__main__":
    demo.launch()
