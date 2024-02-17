# -*- coding: utf-8 -*-
from loguru import logger as log
import gradio as gr
import iscc_core as ic


def explain_iscc(code):
    result = [gr.Column(visible=False), None, None, None, None]
    if not code:
        return tuple(result)
    try:
        canonical = ic.iscc_normalize(code)
        # TODO Update iscc-core validation for MSCDI
        # ic.iscc_validate(canonical, strict=True)
        human = " - ".join(ic.iscc_explain(code).split("-"))
        code_obj = ic.Code(canonical)
        decomposed = " - ".join(ic.iscc_decompose(canonical))
        multiformat = code_obj.mf_base58btc
    except Exception as e:
        log.error(e)
        result[1] = str(e)
        return tuple(result)
    return gr.Column(visible=True), canonical, human, decomposed, multiformat


with gr.Blocks() as demo:
    gr.Markdown(
        """
    ## 🕵️‍♂️ ISCC Inspector
    """
    )
    with gr.Row():
        with gr.Column():
            in_iscc = gr.Text(
                label="ISCC Inspector",
                info="DECODE & EXPLAIN ISCC STRUCTURE",
                placeholder="Paste an ISCC here to break it down",
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

    with gr.Row():
        with gr.Column(visible=False) as out_column:
            out_canonical = gr.Text(
                label="Canonical",
                info="NORMALIZED STANDARD REPRESENTATION",
                show_copy_button=True,
                value=None,
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
            out_column,
            out_canonical,
            out_human,
            out_decomposed,
            out_multiformat,
        ],
        show_progress="hidden",
    )

if __name__ == "__main__":
    demo.launch()
