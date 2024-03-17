import base64
import io
from loguru import logger as log
from pathlib import Path
import gradio as gr
from PIL import Image
import iscc_core as ic
import iscc_sdk as idk
import iscc_schema as iss
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

.small-height {
    display: flex;        /* Use flexbox layout */
    flex-direction: column; /* Arrange children vertically */
    justify-content: flex-end; /* Align children to the end (bottom) */
    height: 85px;        /* Fixed height */
    object-fit: contain;  /* Scale the content to fit within the element */
}

.bit-matrix-big {
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    height: 120px;        /* Fixed height */
    object-fit: contain;  /* Scale the content to fit within the element */
}

.iscc-unit-sim {
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    height: 120px;        /* Fixed height */
    object-fit: contain;  /* Scale the content to fit within the element */
}

.modebar-btn {
    display: none !important;
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
    data_df["Color"] = ["#f56169" if x < 0 else "#a6db50" for x in data_df["Value"]]

    # Create Plotly Figure
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=data_df["Value"],
            y=data_df["Category"],
            orientation="h",
            marker_color=data_df["Color"],
            marker_line={"width": 0},
            text=data_df["Percentage"].apply(lambda x: f"{x:.2f}%"),
            textposition="inside",
            textfont={
                "size": 14,
                "family": "JetBrains Mono",
                "color": "white",
            },
            hoverinfo=None,
            hovertemplate="ISCC-UNIT: %{y}<br>SIMILARITY: %{x}<extra></extra>",
            hoverlabel={
                "font": {"family": "JetBrains Mono", "color": "#FFFFFF"},
                "bgcolor": "#444444",
            },
        )
    )

    # Update layout for aesthetics
    fig.update_layout(
        height=len(sim_data) * 40,
        autosize=True,
        xaxis=dict(
            title="",
            tickformat=",.0%",
            showticklabels=False,
        ),
        yaxis=dict(
            title="",
            showticklabels=False,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        modebar_remove=[
            "toImage",
            "zoom",
            "pan",
            "zoomIn",
            "zoomOut",
            "autoScale",
            "resetScale",
        ],
    )

    # Adjust the x-axis to accommodate percentage labels
    fig.update_xaxes(
        range=[-1.1, 1.1],
        fixedrange=False,
        showline=False,
        zeroline=False,
        showgrid=False,
        gridcolor="rgba(0,0,0,0)",
    )

    return fig


def bit_matrix_plot(iscc_code):
    # type: (ic.Code) -> go.Figure
    """
    Create a bit matrix plot for an ISCC-CODE
    """

    # Decode ISCC-CODE
    data = {}
    for unit in ic.iscc_decompose(iscc_code.code):
        unit = ic.Code(unit)
        data[unit.type_id.split("-")[0]] = unit.hash_bits

    # Prepare data for heatmap
    z = []
    for key, value in data.items():
        z.append([int(bit) for bit in value])

    # Define colors for 0 and 1 bits
    colorscale = [[0, "#7ac2f7"], [1, "#0054b2"]]

    # Build Plotly Visualization
    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            xgap=2,
            ygap=2,
            showscale=False,
            colorscale=colorscale,
            hoverinfo="x+y",
            hovertemplate="ISCC-UNIT: %{y}<br>BIT-NUMBR: %{x}<br>BIT-VALUE: %{z}<extra></extra>",
            hoverlabel={
                "font": {"family": "JetBrains Mono"},
            },
        )
    )

    fig.update_layout(
        height=60,
        autosize=True,
        xaxis=dict(
            ticks="",
            side="top",
            scaleanchor="y",
            constrain="domain",
            showticklabels=False,
        ),
        yaxis=dict(
            ticks="",
            tickvals=list(range(len(data))),
            ticktext=list(data.keys()),
            side="left",
            autorange="reversed",
            showticklabels=False,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=0, b=10),
        modebar_remove=[
            "toImage",
            "zoom",
            "pan",
            "zoomIn",
            "zoomOut",
            "autoScale",
            "resetScale",
        ],
    )

    fig.update_xaxes(
        fixedrange=False,
        showline=False,
        zeroline=False,
        showgrid=False,
        gridcolor="rgba(0,0,0,0)",
    )
    fig.update_yaxes(
        fixedrange=False,
        showline=False,
        zeroline=False,
        showgrid=False,
        gridcolor="rgba(0,0,0,0)",
    )

    return fig


def bit_comparison(iscc_code1, iscc_code2):
    """
    Create a comparison bit matrix plot for two ISCC-CODES
    """

    # Decode ISCC-CODEs
    data1, data2 = {}, {}
    for unit in ic.iscc_decompose(iscc_code1):
        unit = ic.Code(unit)
        data1[unit.type_id.split("-")[0]] = unit.hash_bits
    for unit in ic.iscc_decompose(iscc_code2):
        unit = ic.Code(unit)
        data2[unit.type_id.split("-")[0]] = unit.hash_bits

    # Prepare data for heatmap comparison
    z = []
    text = []
    for key in data1.keys():
        z_row = []
        text_row = []
        for bit1, bit2 in zip(data1[key], data2.get(key, "")):
            if bit1 == bit2:
                z_row.append(int(bit1))
                text_row.append(bit1)
            else:
                z_row.append(2)
                text_row.append("x")
        z.append(z_row)
        text.append(text_row)

    # Define colors for 0, 1, and non-matching bits
    colorscale = [[0, "#a6db50"], [0.5, "#a6db50"], [1, "#f56169"]]

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            text=text,
            xgap=2,
            ygap=2,
            showscale=False,
            colorscale=colorscale,
            hoverinfo="text",
            hovertemplate="ISCC-UNIT: %{y}<br>BIT-NUMBR: %{x}<br>BIT-VALUE: %{z}<extra></extra>",
            hoverlabel={
                "font": {"family": "JetBrains Mono"},
            },
            texttemplate="%{text}",  # Use "%{text}" for showing bits
            textfont={
                "size": 14,
                "color": "#FFFFFF",
                "family": "JetBrains Mono",
            },
        )
    )

    fig.update_layout(
        height=120,
        autosize=True,
        xaxis=dict(
            ticks="",
            side="top",
            scaleanchor="y",
            constrain="domain",
            showticklabels=False,
        ),
        yaxis=dict(
            ticks="",
            tickvals=list(range(len(data1))),
            ticktext=list(data1.keys()),
            side="left",
            autorange="reversed",
            showticklabels=False,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        modebar_remove=[
            "toImage",
            "zoom",
            "pan",
            "zoomIn",
            "zoomOut",
            "autoScale",
            "resetScale",
        ],
    )

    fig.update_xaxes(
        fixedrange=False,
        showline=False,
        zeroline=False,
        showgrid=False,
        gridcolor="rgba(0,0,0,0)",
    )
    fig.update_yaxes(
        fixedrange=False,
        showline=False,
        zeroline=False,
        showgrid=False,
        gridcolor="rgba(0,0,0,0)",
    )

    return fig


with gr.Blocks(css=custom_css) as demo:
    gr.Markdown("## ⚙️ ISCC Similarity Comparison")

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

            out_iscc_a = gr.Text(label="ISCC", show_copy_button=True)

            with gr.Accordion(label="Details", open=False):
                out_dna_a = gr.Plot(
                    label="BIT-MATRIX",
                    container=True,
                    elem_classes=["small-height"],
                )
                out_meta_a = gr.Code(language="json", label="ISCC Metadata")

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

            out_iscc_b = gr.Text(label="ISCC", show_copy_button=True)

            with gr.Accordion(
                label="Details",
                open=False,
            ):
                out_dna_b = gr.Plot(
                    label="BIT-MATRIX",
                    container=True,
                    elem_classes=["small-height"],
                )
                out_meta_b = gr.Code(language="json", label="ISCC Metadata")

    with gr.Row(variant="default", equal_height=True):
        with gr.Column(variant="compact"):
            out_bitcompare = gr.Plot(
                label="BIT-MATRIX Comparison",
                container=True,
                elem_classes=["bit-matrix-big"],
            )

    with gr.Row(variant="default", equal_height=True):
        with gr.Column(variant="compact"):
            out_compare = gr.Plot(
                label="ISCC-UNIT Similarities",
                container=True,
                elem_classes=["iscc-unit-sim"],
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
        out_dna_func = globals().get(f"out_dna_{suffix}")
        out_meta_func = globals().get(f"out_meta_{suffix}")

        # Handle emtpy filepath
        if not filepath:
            return {
                in_file_func: None,
            }

        imeta: idk.IsccMeta = iscc_semantic(filepath)

        # Create Bit-Matrix Plot
        matrix_plot = bit_matrix_plot(imeta.iscc_obj)

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
            out_dna_func: matrix_plot,
            out_meta_func: imeta.json(exclude_unset=False, by_alias=True, indent=2),
        }

        return result

    def iscc_compare(iscc_a, iscc_b):
        # type: (str, str) -> dict | None
        """Compare two ISCCs"""
        if not all([iscc_a, iscc_b]):
            return None, None
        dist_data = ic.iscc_compare(iscc_a, iscc_b)
        sim_data = dist_to_sim(dist_data, dim=64)
        sim_plot = similarity_plot(sim_data)
        bit_plot = bit_comparison(iscc_a, iscc_b)
        return sim_plot, bit_plot

    # Events
    in_file_a.change(
        lambda file: process_upload(file, "a"),
        inputs=[in_file_a],
        outputs=[in_file_a, out_thumb_a, out_iscc_a, out_dna_a, out_meta_a],
        show_progress="full",
    )
    in_file_b.change(
        lambda file: process_upload(file, "b"),
        inputs=[in_file_b],
        outputs=[in_file_b, out_thumb_b, out_iscc_b, out_dna_b, out_meta_b],
        show_progress="full",
    )
    out_thumb_a.clear(
        lambda: (
            gr.File(visible=True),
            gr.Image(visible=False),
            "",
            gr.Plot(value=None),
            "",
        ),
        inputs=[],
        outputs=[in_file_a, out_thumb_a, out_iscc_a, out_dna_a, out_meta_a],
        show_progress="hidden",
    )

    out_thumb_b.clear(
        lambda: (
            gr.File(visible=True),
            gr.Image(visible=False),
            "",
            gr.Plot(value=None),
            "",
        ),
        inputs=[],
        outputs=[in_file_b, out_thumb_b, out_iscc_b, out_dna_b, out_meta_b],
        show_progress="hidden",
    )

    out_iscc_a.change(
        iscc_compare,
        inputs=[out_iscc_a, out_iscc_b],
        outputs=[out_compare, out_bitcompare],
        show_progress="hidden",
    )

    out_iscc_b.change(
        iscc_compare,
        inputs=[out_iscc_a, out_iscc_b],
        outputs=[out_compare, out_bitcompare],
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
