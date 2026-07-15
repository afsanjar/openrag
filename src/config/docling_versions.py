"""Pinned version constants for the docling-serve toolchain."""

import os

#: ``docling-serve[ui]`` package version installed via ``uvx --from``.
DOCLING_SERVE_VERSION: str = os.getenv("DOCLING_SERVE_VERSION", "1.20.0")

#: ``docling-core`` pinned version installed alongside docling-serve.
DOCLING_CORE_VERSION: str = os.getenv("DOCLING_CORE_VERSION", "2.77.1")

#: ``transformers`` version specifier.
DOCLING_TRANSFORMERS_SPEC: str = os.getenv("DOCLING_TRANSFORMERS_SPEC", ">=5.8.1,<5.9.0")

#: Extra sets passed to ``docling[...]`` on macOS (includes ocrmac).
DOCLING_EXTRAS_MACOS: str = os.getenv("DOCLING_EXTRAS_MACOS", "ocrmac,easyocr,rapidocr,vlm")

#: Extra sets passed to ``docling[...]`` on non-macOS platforms.
DOCLING_EXTRAS_LINUX: str = os.getenv("DOCLING_EXTRAS_LINUX", "easyocr,rapidocr,vlm")
