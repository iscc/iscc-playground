# -*- coding: utf-8 -*-
import base64
import io
from loguru import logger as log
from pathlib import Path
import gradio as gr
from PIL import Image
import iscc_core as ic
import iscc_sdk as idk
import iscc_sci as sci
import plotly.graph_objects as go
import pandas as pd


idk.sdk_opts.image_thumbnail_size = 265
idk.sdk_opts.image_thumbnail_quality = 80


HERE = Path(__file__).parent.absolute()
IMAGES1 = HERE / "images1"
IMAGES2 = HERE / "images2"


custom_css = """
.fixed-height {
    height: 240px;  /* Fixed height */
    object-fit: contain;  /* Scale the image to fit within the element */
}

#examples-a, #examples-b {
    height: 140px;  /* Fixed height */
    object-fit: contain;  /* Scale the image to fit within the element */
}
"""


def iscc_semantic(filepath: str) -> idk.IsccMeta:
    """Generate ISCC-CODE extended with Semantic-Code for supported modalities (Image)"""
    imeta = idk.code_iscc(filepath)
    if imeta.mode == "image":
        # Inject Semantic-Code
        sci_code = sci.code_image_semantic(filepath, bits=64)["iscc"]
        units = ic.iscc_decompose(imeta.iscc)
        units.append(sci_code)
        iscc_code_s = ic.gen_iscc_code(units)["iscc"]
        imeta.iscc = iscc_code_s
    return imeta


def dist_to_sim(data, dim=64):
    result = {}
    for k, v in data.items():
        if k == "instance_match":
            result[k.split("_")[0].title()] = 1.0 if v is True else -1.0
        else:
            result[k.split("_")[0].title()] = hamming_to_cosine(v, dim)
    return result


def hamming_to_cosine(hamming_distance: int, dim: int) -> float:
    """Aproximate the cosine similarity for a given hamming distance and dimension"""
    result = 1 - (2 * hamming_distance) / dim
    log.debug(f"Hamming distance: {hamming_distance} - Dim: {dim} - Result: {result}")
    return result


def similarity_plot(sim_data):
    # type: (dict) -> go.Figure
    # Convert input dictionary to DataFrame, sort by value for visual consistency
    data_df = pd.DataFrame(reversed(sim_data.items()), columns=["Category", "Value"])
    data_df["Percentage"] = data_df["Value"] * 100  # Convert to percentage

    # Define color for bars based on value
    # data_df["Color"] = ["red" if x < 0 else "green" for x in data_df["Value"]]
    data_df["Color"] = [
        f"rgba(224,122,95,{abs(x)})" if x < 0 else f"rgba(118,185,71,{x})"
        for x in data_df["Value"]
    ]

    # Create Plotly Figure
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=data_df["Value"],
            y=data_df["Category"],
            orientation="h",
            marker_color=data_df["Color"],
            text=data_df["Percentage"].apply(lambda x: f"{x:.2f}%"),
            textposition="inside",
        )
    )  # Change made here

    # Update layout for aesthetics
    fig.update_layout(
        title={"text": "Approximate ISCC-UNIT Similarities", "x": 0.5},
        xaxis=dict(title="Similarity", tickformat=",.0%"),
        yaxis=dict(title=""),
        plot_bgcolor="rgba(0,0,0,0)",
        height=len(sim_data) * 70,
        showlegend=False,
        autosize=True,
        margin=dict(l=50, r=50, t=50, b=50),
    )

    # Adjust the x-axis to accommodate percentage labels
    fig.update_xaxes(range=[-1.1, 1.1])

    return fig


with gr.Blocks(css=custom_css) as demo:
    gr.Markdown("## 🖼️ ISCC Similarity Comparison")

    with gr.Row(variant="default", equal_height=True):
        with gr.Column(variant="compact"):
            in_file_a = gr.File(
                label="Media File A", type="filepath", elem_classes=["fixed-height"]
            )
            out_thumb_a = gr.Image(
                label="Extracted Thumbnail",
                visible=False,
                height=240,
                elem_classes=["fixed-height"],
                interactive=True,
                show_download_button=False,
                sources=["upload"],
            )

            # Proxy component to patch image example selection -> gr.File
            dumy_image_a = gr.Image(visible=False, type="filepath", height=240)

            gr.Examples(
                examples=IMAGES1.as_posix(),
                cache_examples=False,
                inputs=[dumy_image_a],
                elem_id="examples-a",
            )

            out_iscc_a = gr.Text(label="ISCC")
            with gr.Accordion(label="ISCC Metadata", open=False):
                out_meta_a = gr.Code(language="json", label="JSON-LD")

        with gr.Column(variant="compact"):
            in_file_b = gr.File(
                label="Media File B", type="filepath", elem_classes=["fixed-height"]
            )

            out_thumb_b = gr.Image(
                label="Extracted Thumbnail",
                visible=False,
                height=240,
                elem_classes=["fixed-height"],
                interactive=True,
                show_download_button=False,
                sources=["upload"],
            )

            # Proxy component to patch image example selection -> gr.File
            dumy_image_b = gr.Image(visible=False, type="filepath", height=240)

            gr.Examples(
                examples=IMAGES2.as_posix(),
                cache_examples=False,
                inputs=[dumy_image_b],
                elem_id="examples-b",
            )

            out_iscc_b = gr.Text(label="ISCC")
            with gr.Accordion(label="ISCC Metadata", open=False):
                out_meta_b = gr.Code(language="json", label="JSON-LD")

    with gr.Row(variant="panel"):
        out_compare = gr.Plot(
            label="Approximate ISCC-UNIT Similarities", container=False
        )

    def rewrite_uri(filepath, sample_set):
        # type: (str, str) -> str
        """Rewrites temporary image URI to original sample URI"""
        if filepath:
            inpath = Path(filepath)
            outpath = HERE / f"{sample_set}/{inpath.name.replace('jpeg', 'jpg')}"

            log.info(filepath)
            return outpath.as_posix()

    def process_upload(filepath, suffix):
        # type: (str, str) -> dict
        """Generate extended ISCC with experimental Semantic Code (for images)"""

        # Map to active component group
        in_file_func = globals().get(f"in_file_{suffix}")
        out_thumb_func = globals().get(f"out_thumb_{suffix}")
        out_iscc_func = globals().get(f"out_iscc_{suffix}")
        out_meta_func = globals().get(f"out_meta_{suffix}")

        # Handle emtpy filepath
        if not filepath:
            return {
                in_file_func: None,
            }

        imeta = iscc_semantic(filepath)

        # Pop Thumbnail for Preview
        thumbnail = None
        if imeta.thumbnail:
            header, encoded = imeta.thumbnail.split(",", 1)
            data = base64.b64decode(encoded)
            thumbnail = Image.open(io.BytesIO(data))
            imeta.thumbnail = None

        result = {
            in_file_func: gr.File(visible=False, value=None),
            out_thumb_func: gr.Image(visible=True, value=thumbnail),
            out_iscc_func: imeta.iscc,
            out_meta_func: imeta.json(exclude_unset=False, by_alias=True, indent=2),
        }

        return result

    def iscc_compare(iscc_a, iscc_b):
        # type: (str, str) -> dict | None
        """Compare two ISCCs"""
        if not all([iscc_a, iscc_b]):
            return None
        dist_data = ic.iscc_compare(iscc_a, iscc_b)
        sim_data = dist_to_sim(dist_data, dim=64)
        sim_plot = similarity_plot(sim_data)
        return sim_plot

    # Events
    in_file_a.change(
        lambda file: process_upload(file, "a"),
        inputs=[in_file_a],
        outputs=[in_file_a, out_thumb_a, out_iscc_a, out_meta_a],
        show_progress="full",
    )
    in_file_b.change(
        lambda file: process_upload(file, "b"),
        inputs=[in_file_b],
        outputs=[in_file_b, out_thumb_b, out_iscc_b, out_meta_b],
        show_progress="full",
    )
    out_thumb_a.clear(
        lambda: (gr.File(visible=True), gr.Image(visible=False), "", ""),
        inputs=[],
        outputs=[in_file_a, out_thumb_a, out_iscc_a, out_meta_a],
        show_progress="hidden",
    )

    out_thumb_b.clear(
        lambda: (gr.File(visible=True), gr.Image(visible=False), "", ""),
        inputs=[],
        outputs=[in_file_b, out_thumb_b, out_iscc_b, out_meta_b],
        show_progress="hidden",
    )

    out_iscc_a.change(
        iscc_compare,
        inputs=[out_iscc_a, out_iscc_b],
        outputs=[out_compare],
        show_progress="hidden",
    )

    out_iscc_b.change(
        iscc_compare,
        inputs=[out_iscc_a, out_iscc_b],
        outputs=[out_compare],
        show_progress="hidden",
    )

    dumy_image_a.change(
        lambda file: rewrite_uri(file, "images1"),
        inputs=[dumy_image_a],
        outputs=[in_file_a],
        show_progress="hidden",
    )
    dumy_image_b.change(
        lambda file: rewrite_uri(file, "images2"),
        inputs=[dumy_image_b],
        outputs=[in_file_b],
        show_progress="hidden",
    )


if __name__ == "__main__":
    demo.launch(debug=True)
