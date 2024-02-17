# -*- coding: utf-8 -*-
from loguru import logger as log
import pandas as pd
import gradio as gr
import plotly.graph_objects as go
import iscc_core as ic
import iscc_sdk as idk
import iscc_sci as sci
import pathlib


idk.sdk_opts.image_thumbnail_size = 265
idk.sdk_opts.image_thumbnail_quality = 80


HERE = pathlib.Path(__file__).parent.absolute()
IMAGES1 = HERE / "images1"
IMAGES2 = HERE / "images2"


def generate_iscc_semantic(filepath):
    """Generate an ISCC Semantic Image-Code"""
    # Standard ISCC-CODE
    iscc_obj = idk.code_iscc(filepath)
    iscc_code = iscc_obj.iscc

    # Semantic Image-Code
    sci_code = sci.code_image_semantic(filepath, bits=64)["iscc"]

    # Combine
    units = ic.iscc_decompose(iscc_code)
    units.append(sci_code)
    iscc_code = ic.gen_iscc_code(units)["iscc"]
    iscc_obj.iscc = iscc_code
    details = iscc_obj.dict(exclude_unset=False, by_alias=True)

    # Remove Thumbnail - Too much noise for UI
    try:
        del details["thumbnail"]
    except KeyError:
        pass

    return iscc_code, details


def compare(iscc_a, iscc_b):
    # type: (str, str) -> dict
    """Compare two ISCCs"""
    dist_data = ic.iscc_compare(iscc_a, iscc_b)
    sim_data = dist_to_sim(dist_data, dim=64)
    sim_plot = similarity_plot(sim_data)
    return sim_plot


def hamming_to_cosine(hamming_distance: int, dim: int) -> float:
    """Aproximate the cosine similarity for a given hamming distance and dimension"""
    result = 1 - (2 * hamming_distance) / dim
    log.debug(f"Hamming distance: {hamming_distance} - Dim: {dim} - Result: {result}")
    return 1 - (2 * hamming_distance) / dim


def dist_to_sim(data, dim=64):
    result = {}
    for k, v in data.items():
        if k == "instance_match":
            result[k.split("_")[0].title()] = 1.0 if v is True else -1.0
        else:
            result[k.split("_")[0].title()] = hamming_to_cosine(v, dim)
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


custom_css = """
.json-holder {
    word-wrap: break-word;
    white-space: pre-wrap;
}
"""


with gr.Blocks(css=custom_css) as demo:
    gr.Markdown(
        """
    ## 🖼️ ISCC Image-Code-Semantic Comparison
    Compare two images using ISCC Semantic Image Codes
    """
    )
    with gr.Row(variant="default", equal_height=True):
        with gr.Column(variant="compact"):
            img1 = gr.Image(
                label="Upload Image 1",
                # sources=["upload"],
                type="filepath",
                height=320,
            )
            gr.Examples(
                examples=IMAGES1.as_posix(),
                cache_examples=False,
                inputs=[img1],
            )

        with gr.Column(variant="compact"):
            img2 = gr.Image(
                label="Upload Image 2",
                # sources=["upload"],
                type="filepath",
                height=320,
            )
            gr.Examples(
                examples=IMAGES2.as_posix(),
                cache_examples=False,
                inputs=[img2],
            )
    with gr.Row(variant="default"):
        gr.ClearButton(components=[img1, img2])

    with gr.Row():
        with gr.Column(variant="panel"):
            out_iscc1 = gr.Text(
                label="ISCC-CODE",
                container=True,
                show_copy_button=True,
            )
            with gr.Accordion("Details", open=False):
                out_detail1 = gr.Json(label="ISCC METADATA")
        with gr.Column(variant="panel"):
            out_iscc2 = gr.Text(
                label="ISCC-CODE",
                container=True,
                show_copy_button=True,
            )
            with gr.Accordion("Details", open=False):
                out_detail2 = gr.Json(label="ISCC METADATA")

    with gr.Row(variant="panel"):
        out_compare = gr.Plot(
            label="Approximate ISCC-UNIT Similarities", container=False
        )

    def process_and_compare_images(file1, file2):
        # Initialize default responses for when one or both images are not uploaded
        iscc_code1 = ""
        iscc_code2 = ""
        detail1 = None
        detail2 = None

        comparison_result = None

        # Check if both images are uploaded
        if file1 and file2:
            # Generate ISCC codes for both images
            iscc_code1, detail1 = generate_iscc_semantic(file1)
            iscc_code2, detail2 = generate_iscc_semantic(file2)
            comparison_result = compare(iscc_code1, iscc_code2)

        # Return the ISCC codes and the comparison result as separate outputs
        return iscc_code1, detail1, iscc_code2, detail2, comparison_result

    # Update the change method calls to handle the corrected output format
    img1.change(
        process_and_compare_images,
        inputs=[img1, img2],
        outputs=[out_iscc1, out_detail1, out_iscc2, out_detail2, out_compare],
    )
    img2.change(
        process_and_compare_images,
        inputs=[img1, img2],
        outputs=[out_iscc1, out_detail1, out_iscc2, out_detail2, out_compare],
    )

if __name__ == "__main__":
    demo.launch(debug=True)
