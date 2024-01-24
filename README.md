---
title: ISCC - Playground
emoji: ▶️
colorFrom: red
colorTo: blue
sdk: gradio
app_file: app.py
pinned: true
---
# ISCC - Gradio Playground

`iscc-playgound` is explorative gradio based user interface for the [ISCC](https://iscc.codes)
(*International Standard Content Code*)

## What is the ISCC

The ISCC is a similarity preserving fingerprint and identifier for digital media assets.

ISCCs are generated algorithmically from digital content, just like cryptographic hashes. However,
instead of using a single cryptographic hash function to identify data only, the ISCC uses various
algorithms to create a composite identifier that exhibits similarity-preserving properties (soft
hash).

The component-based structure of the ISCC identifies content at multiple levels of abstraction. Each
component is self-describing, modular, and can be used separately or with others to aid in various
content identification tasks. The algorithmic design supports content deduplication, database
synchronization, indexing, integrity verification, timestamping, versioning, data provenance,
similarity clustering, anomaly detection, usage tracking, allocation of royalties, fact-checking and
general digital asset management use-cases.


## Project Status

The ISCC is under development as [ISO/DIS 24138](https://www.iso.org/standard/77899.html) -
International Standard Content Code within
[ISO/TC 46/SC 9/WG 18](https://www.iso.org/committee/48836.html).
