# -*- coding: utf-8 -*-
from loguru import logger as log
import gradio as gr
import iscc_core as ic


def explain_iscc(code):
    result = [gr.Column(visible=True), None, None, None, None, None, None, None, None]
    if not code:
        return tuple(result)
    try:
        if not code.startswith("ISCC:"):
            code = ic.iscc_normalize(code)

        code_obj = ic.Code(code)
        if code_obj.length != len(code_obj.hash_bits):
            raise ValueError(f"Incorrect body length")

        ic.iscc_validate(code, strict=True)
        human = " - ".join(ic.iscc_explain(code).split("-"))

        decomposed = " - ".join(ic.iscc_decompose(code))
        base16 = code_obj.mf_base16
        base32 = code_obj.mf_base32
        base32hex = code_obj.mf_base32hex
        base58btc = code_obj.mf_base58btc
        base64url = code_obj.mf_base64url
    except Exception as e:
        log.error(e)
        result[1] = str(e)
        return tuple(result)
    return (
        gr.Column(visible=True),
        code,
        human,
        decomposed,
        base16,
        base32,
        base32hex,
        base58btc,
        base64url,
    )


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
                "ISCC:KED572P4AOF5K6QXQA4T6OJD5UGX7UBPFW2TVQNTHBCKFRFCANCZARQ4K6NSFZQSH4GQ",
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
            with gr.Row():
                with gr.Column():
                    gr.Markdown("## Multiformat Encodings")
                    out_base16 = gr.Text(
                        label="base16",
                        show_copy_button=True,
                    )

                    out_base32 = gr.Text(
                        label="base32",
                        show_copy_button=True,
                    )

                    out_base32_hex = gr.Text(
                        label="base32hex",
                        show_copy_button=True,
                    )

                    out_base58_btc = gr.Text(
                        label="base58btc",
                        show_copy_button=True,
                    )

                    out_base64_url = gr.Text(
                        label="base64url",
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
            out_base16,
            out_base32,
            out_base32_hex,
            out_base58_btc,
            out_base64_url,
        ],
        show_progress="hidden",
    )

if __name__ == "__main__":
    demo.launch()
