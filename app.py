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
    font=gr.themes.GoogleFont("Readex Pro"),
    font_mono=gr.themes.GoogleFont("JetBrains Mono"),
    radius_size=gr.themes.sizes.radius_none,
)


demo = gr.TabbedInterface(
    title="▶️ ISCC Playground - The DNA of your digital content",
    interface_list=[demo_generate, demo_compare, demo_inspect, demo_chunker],
    tab_names=["GENERATE", "COMPARE", "INSPECT", "CHUNKER"],
    css=custom_css,
    theme=iscc_theme,
)


if __name__ == "__main__":
    demo.launch()
