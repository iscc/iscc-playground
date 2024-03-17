import gradio as gr

css = """
    #stats_box {font-family: monospace; font-size: 65%; height: 162px;}
    footer {visibility: hidden}
    body {overflow: hidden;}
    * {scrollbar-color: rebeccapurple green; scrollbar-width: thin;}
"""


iscc_theme = gr.themes.Default(
    font=gr.themes.GoogleFont("Readex Pro"),
    font_mono=gr.themes.GoogleFont("JetBrains Mono"),
    radius_size=gr.themes.sizes.radius_none,
)


with gr.Blocks(css=css, theme=iscc_theme) as demo:
    gr.HTML('<h1 style="color: #6aa84f; font-size: 250%;">ISCC SEARCH DEMO</h1>')

    with gr.Row(equal_height=True):
        with gr.Column():
            in_image = gr.Image(type="pil")

    gallery = gr.Gallery(
        value=None,
        columns=8,
        height=750,
        object_fit="scale-down",
        preview=False,
    )

if __name__ == "__main__":
    demo.launch()
