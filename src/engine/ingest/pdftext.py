"""PDF -> per-page text, with page numbers that match the printed document.

Conventions
-----------
- Pages are returned as a ``list[str]``; **page numbers are 1-based**: ``pages[n - 1]`` is
  page ``n``. Use :func:`get_page` for bounds-checked access by page number.
- The primary backend is the poppler command-line tool ``pdftotext -layout`` (run with
  :mod:`subprocess`; availability checked with :func:`shutil.which`). It keeps the visual
  column layout, which the rule-based extractors in :mod:`engine.ingest.renovabio` rely on.
- Fallback backend: :mod:`pypdf` (``extract_text(extraction_mode="layout")``). Its layout
  differs from poppler's, so regex-based extractors tuned on ``pdftotext -layout`` output may
  find fewer values; the verifier (:func:`engine.ingest.renovabio.verify_record`) still works
  because it compares whitespace-normalised text.
- ``pdftotext`` separates pages with a form feed (``\\f``) and also writes one after the last
  page; :func:`split_pages` drops that trailing empty piece so ``len(pages)`` equals the PDF
  page count.

No network access; the module only reads local files.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

__all__ = [
    "PdfTextError",
    "pdftotext_available",
    "split_pages",
    "pdf_to_pages",
    "read_txt_pages",
    "load_pages",
    "get_page",
]

#: Page separator written by ``pdftotext`` between pages.
FORM_FEED = "\f"

#: Wall-clock limit for one ``pdftotext`` call, in seconds (a software guard, not a model value).
PDFTOTEXT_TIMEOUT_S = 120


class PdfTextError(RuntimeError):
    """Raised when no backend can extract text from a PDF."""


def pdftotext_available() -> bool:
    """Return True when the poppler ``pdftotext`` executable is on ``PATH``."""
    return shutil.which("pdftotext") is not None


def split_pages(text: str) -> list[str]:
    """Split ``pdftotext`` output into pages on form feeds (``\\f``).

    Args:
        text: full text as written by ``pdftotext`` (pages separated by ``\\f``).

    Returns:
        List of page texts; element ``i`` is page ``i + 1``. A single trailing piece that is
        empty or whitespace-only (produced by the form feed ``pdftotext`` writes after the last
        page) is dropped. Empty pages *inside* the document are kept so numbering is preserved.
    """
    if not text:
        return []
    pages = text.split(FORM_FEED)
    if len(pages) > 1 and not pages[-1].strip():
        pages = pages[:-1]
    return pages


def _pdftotext_pages(pdf_path: Path, layout: bool) -> list[str]:
    exe = shutil.which("pdftotext")
    if exe is None:  # pragma: no cover - guarded by caller
        raise PdfTextError("pdftotext is not on PATH")
    cmd = [exe]
    if layout:
        cmd.append("-layout")
    cmd += ["-enc", "UTF-8", str(pdf_path), "-"]
    proc = subprocess.run(  # noqa: S603 - fixed executable, no shell
        cmd, capture_output=True, check=False, timeout=PDFTOTEXT_TIMEOUT_S
    )
    if proc.returncode != 0:
        raise PdfTextError(
            f"pdftotext failed (exit {proc.returncode}) on {pdf_path}: "
            f"{proc.stderr.decode('utf-8', 'replace').strip()}"
        )
    return split_pages(proc.stdout.decode("utf-8", errors="replace"))


def _pypdf_pages(pdf_path: Path, layout: bool) -> list[str]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - pypdf is a declared dependency
        raise PdfTextError("pypdf is not installed and pdftotext is unavailable") from exc
    reader = PdfReader(str(pdf_path))
    pages: list[str] = []
    for page in reader.pages:
        if layout:
            try:
                text = page.extract_text(extraction_mode="layout")
            except TypeError:  # pragma: no cover - very old pypdf without layout mode
                text = page.extract_text()
        else:
            text = page.extract_text()
        pages.append(text or "")
    return pages


def pdf_to_pages(pdf_path: str | Path, *, layout: bool = True, backend: str = "auto") -> list[str]:
    """Extract per-page text from a PDF.

    Args:
        pdf_path: path to a local PDF file.
        layout: keep the visual layout (``pdftotext -layout`` / pypdf layout mode).
        backend: ``"auto"`` (pdftotext if available, else pypdf), ``"pdftotext"`` or
            ``"pypdf"``.

    Returns:
        List of page texts, 1-based numbering (``pages[0]`` is page 1).

    Raises:
        FileNotFoundError: if ``pdf_path`` does not exist.
        ValueError: for an unknown ``backend``.
        PdfTextError: if the requested backend is unavailable or fails.
    """
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    if backend not in {"auto", "pdftotext", "pypdf"}:
        raise ValueError(f"unknown backend {backend!r}; use 'auto', 'pdftotext' or 'pypdf'")
    if backend == "pdftotext" or (backend == "auto" and pdftotext_available()):
        if not pdftotext_available():
            raise PdfTextError("backend='pdftotext' requested but pdftotext is not on PATH")
        try:
            return _pdftotext_pages(path, layout)
        except (PdfTextError, subprocess.TimeoutExpired):
            if backend == "pdftotext":
                raise
            # auto: fall through to pypdf
    return _pypdf_pages(path, layout)


def read_txt_pages(txt_path: str | Path, *, encoding: str = "utf-8") -> list[str]:
    """Read a text file previously produced by ``pdftotext`` and split it into pages.

    Args:
        txt_path: path to the ``.txt`` file (pages separated by form feeds).
        encoding: file encoding (``pdftotext -enc UTF-8`` output is UTF-8).

    Returns:
        List of page texts, 1-based numbering (``pages[0]`` is page 1).
    """
    return split_pages(Path(txt_path).read_text(encoding=encoding))


def load_pages(path: str | Path, **kwargs: object) -> list[str]:
    """Read pages from a ``.pdf`` (:func:`pdf_to_pages`) or a ``.txt`` (:func:`read_txt_pages`)."""
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        return pdf_to_pages(p, **kwargs)  # type: ignore[arg-type]
    return read_txt_pages(p, **kwargs)  # type: ignore[arg-type]


def get_page(pages: list[str], page_no: int) -> str:
    """Return the text of 1-based page ``page_no``; raise ``IndexError`` if out of range."""
    if not 1 <= page_no <= len(pages):
        raise IndexError(f"page {page_no} out of range 1..{len(pages)}")
    return pages[page_no - 1]
