import gradio as gr
from demos.generate import demo as demo_generate
from demos.compare import demo as demo_compare
from demos.inspect_ import demo as demo_inspect
from demos.chunker import demo as demo_chunker

custom_css = """
.fixed-height {
    height: 240px;  /* Fixed height */
    object-fit: contain;  /* Scale the image to fit within the element */
}

.fixed-height img {
    height: 240px;  /* Fixed height */
    object-fit: contain;  /* Scale the image to fit within the element */
}

.modebar-btn {
    display: none !important;
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
    height: 150px;        /* Fixed height */
    object-fit: contain;  /* Scale the content to fit within the element */
}

.iscc-unit-sim {
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    height: 300px !important;        /* Fixed height for proper bar display */
    object-fit: contain;  /* Scale the content to fit within the element */
}

.iscc-unit-sim > div {
    height: 100% !important;
    display: flex;
    flex-direction: column;
}

.iscc-unit-sim .plotly {
    height: 100% !important;
    flex: 1;
}

.iscc-unit-sim .plotly > div {
    height: 100% !important;
}

#chunked-text span.label {
    text-transform: none !important;
}
.json-holder {
    word-wrap: break-word;
    white-space: pre-wrap;
}

#examples-a, #examples-b {
    height: 140px;  /* Fixed height */
    object-fit: contain;  /* Scale the image to fit within the element */
}

textarea {
    font-family: JetBrains Mono;
}
"""


iscc_theme = gr.themes.Default(
    font=[gr.themes.GoogleFont("Readex Pro"), "Arial", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "Courier", "monospace"],
    radius_size=gr.themes.sizes.radius_none,
)


demo = gr.TabbedInterface(
    title="▶️ ISCC Playground - The DNA of your digital content",
    interface_list=[demo_compare, demo_generate, demo_inspect, demo_chunker],
    tab_names=["COMPARE", "GENERATE", "INSPECT", "CHUNKER"],
    css=custom_css,
    # theme=iscc_theme,
)


if __name__ == "__main__":
    demo.launch()
