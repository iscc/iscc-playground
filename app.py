import io
import base64
import gradio as gr
import iscc_core as ic
import iscc_sdk as idk
from PIL import Image

idk.sdk_opts.image_thumbnail_size = 265
idk.sdk_opts.image_thumbnail_quality = 80


custom_css = """
.fixed-height img {
    height: 265px;  /* Fixed height */
    object-fit: contain;  /* Scale the image to fit within the element */
}
#chunked-text span.label {
    text-transform: none !important;
}
"""

newline_symbols = {
    "\u000a": "⏎",  # Line Feed - Represented by the 'Return' symbol
    "\u000b": "↨",  # Vertical Tab - Represented by the 'Up Down Arrow' symbol
    "\u000c": "␌",  # Form Feed - Unicode Control Pictures representation
    "\u000d": "↵",  # Carriage Return - 'Downwards Arrow with Corner Leftwards' symbol
    "\u0085": "⤓",  # Next Line - 'Downwards Arrow with Double Stroke' symbol
    "\u2028": "↲",  # Line Separator - 'Downwards Arrow with Tip Leftwards' symbol
    "\u2029": "¶",  # Paragraph Separator - Represented by the 'Pilcrow' symbol
}


def no_nl(text):
    for char, symbol in newline_symbols.items():
        text = text.replace(char, symbol)
    return text


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
    return imeta.iscc, thumbnail, metadata


def explain_iscc(code):
    canonical = ic.iscc_normalize(code)
    human = " - ".join(ic.iscc_explain(code).split("-"))
    code_obj = ic.Code(canonical)
    decomposed = " - ".join(ic.iscc_decompose(canonical))
    multiformat = code_obj.mf_base58btc
    return canonical, human, decomposed, multiformat


def chunk_text(text, chunk_size):
    original_chunk_size = idk.sdk_opts.text_avg_chunk_size
    idk.sdk_opts.text_avg_chunk_size = chunk_size
    cleaned = ic.text_clean(text)
    processed = idk.text_features(cleaned)
    features = processed["features"]
    sizes = processed["sizes"]
    start = 0
    chunks = []
    for size in sizes:
        end = start + size
        chunks.append(no_nl(cleaned[start:end]))
        start = end
    result = [
        (chunk, f"{size}:{feat}") for chunk, size, feat in zip(chunks, sizes, features)
    ]
    idk.sdk_opts.text_avg_chunk_size = original_chunk_size
    return result


####################################################################################################
# TAB ISCC-CODE                                                                                    #
####################################################################################################

with gr.Blocks() as demo_generate:
    gr.Markdown(
        """
    ## 🌟 ISCC-CODE Generator - The DNA of Digital Content
    """
    )
    with gr.Row():
        with gr.Column(scale=2):
            in_file = gr.File(label="Media File")
        with gr.Column(scale=1):
            out_thumbnail = gr.Image(
                label="Extracted Thumbnail", elem_classes=["fixed-height"]
            )
    with gr.Row():
        out_iscc = gr.Text(label="ISCC-CODE", show_copy_button=True)
    with gr.Row():
        out_meta = gr.Json(label="Metadata")
    in_file.change(
        generate_iscc, inputs=[in_file], outputs=[out_iscc, out_thumbnail, out_meta]
    )

####################################################################################################
# TAB ENCODING                                                                                     #
####################################################################################################

with gr.Blocks() as demo_decode:
    gr.Markdown(
        """
    ## 🌟 A Codec for Self-Describing Compact Binary Codes
    """
    )
    with gr.Row():
        with gr.Column():
            in_iscc = gr.Text(
                label="ISCC",
                info="INPUT ANY VALID ISCC-CODE OR ISCC-UNIT",
                autofocus=True,
            )
            examples = [
                "ISCC:AAAWN77F727NXSUS",  # Meta-Code
                "bzqaqaal5rvp72lx2thvq",  # Multiformat
                "ISCC:EAASKDNZNYGUUF5A",  # Text-Code
                "ISCC:GABW5LUBVP23N3DOD7PPINHT5JKBI",  # Data-Code 128 bits
                "ISCC:KUAG5LUBVP23N3DOHCHWIYGXVN7ZS",  # ISCC-SUM
                "ISCC:KAA2Y5NUST7BFD5NN2XIDK7VW3WG4OEPMRQNPK37TE",  # ISCC-CDI
                "z36hVxiqoF8AAmDpZV958hn3tsv2i7v1NfCrSzpq",  # ISCC-CDI multiformats
                "ISCC:KACT4EBWK27737D2AYCJRAL5Z36G76RFRMO4554RU26HZ4ORJGIVHDI",
            ]
            gr.Examples(label="Example ISCCs", examples=examples, inputs=[in_iscc])

    gr.Markdown("## Different Encodings:")
    with gr.Row():
        with gr.Column():
            out_canonical = gr.Text(
                label="Canonical",
                info="NORMALIZED STANDARD REPRESENTATION",
                show_copy_button=True,
            )
            out_human = gr.Text(
                label="Human Readable",
                info="MAINTYPE - SUBTYPE - VERSION - LENGTH - BODY",
                show_copy_button=True,
            )
            out_decomposed = gr.Text(
                label="Decomposed",
                info="ISCC-UNITS",
                show_copy_button=True,
            )
            out_multiformat = gr.Text(
                label="Multiformat",
                info="BASE58-BTC",
                show_copy_button=True,
            )
    in_iscc.change(
        explain_iscc,
        inputs=[in_iscc],
        outputs=[
            out_canonical,
            out_human,
            out_decomposed,
            out_multiformat,
        ],
    )

####################################################################################################
# CHUNKING                                                                                         #
####################################################################################################

with gr.Blocks() as demo_chunking:
    gr.Markdown(
        """
    ## 🌟 Content Defined Chunking for Shift-Resistant Text and Data Segmentation
    """
    )
    with gr.Row():
        with gr.Column():
            in_text = gr.Textbox(label="Text Input", lines=8, autofocus=True)
            in_chunksize = gr.Slider(
                label="Chunk Size",
                info="AVERAGE NUMBER OF CHARACTERS PER CHUNK",
                minimum=32,
                maximum=2048,
                step=32,
                value=64,
            )

        out_text = gr.HighlightedText(
            label="Chunked Text Output",
            interactive=False,
            elem_id="chunked-text",
        )
    in_text.change(chunk_text, inputs=[in_text, in_chunksize], outputs=[out_text])
    in_chunksize.change(chunk_text, inputs=[in_text, in_chunksize], outputs=[out_text])

demo = gr.TabbedInterface(
    title="▶️ ISCC Playground",
    interface_list=[demo_generate, demo_decode, demo_chunking],
    tab_names=["ISCC-CODE", "ENCODING", "CHUNKING"],
    css=custom_css,
)

if __name__ == "__main__":
    demo.launch()
