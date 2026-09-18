"""
pdf_editor.core.engine
=======================

`PDFEngine` is the single object that performs every PDF operation the
application offers. It is completely independent of the GUI layer (no
Tkinter imports here) so it can be unit tested and reused (e.g. from a
CLI or a script) on its own.

Design notes
------------
* Built on PyMuPDF (`fitz`) because one library cleanly covers merging,
  splitting, rotation, page deletion/reordering, text extraction,
  rendering-to-image, watermarking and encryption -- avoiding the need
  to juggle several PDF libraries with subtly different page-indexing
  conventions.
* Every public method validates its inputs and translates low-level
  library exceptions into the application's own `PDFEditorError`
  subclasses (see `core.exceptions`), so the GUI never has to know
  about `fitz`-specific errors.
* All page numbers in the *public* API are 0-indexed unless a method
  name/docstring explicitly says otherwise. The GUI layer is
  responsible for converting the human-facing 1-indexed page numbers
  the user types into 0-indexed values before calling into the engine.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import pymupdf as fitz  # PyMuPDF (import name `pymupdf` since v1.24; `fitz` alias is deprecated)
from PIL import Image

from pdf_editor.core.exceptions import (
    CorruptedPDFError,
    EmptyInputError,
    EncryptedPDFError,
    InvalidPasswordError,
    PageRangeError,
    UnsupportedFileError,
)
from pdf_editor.utils.file_utils import ensure_dir, is_image, unique_path
from pdf_editor.utils.logger import get_logger

logger = get_logger("core.engine")


@dataclass
class PDFInfo:
    """Lightweight summary of a PDF, used to populate the UI."""

    path: str
    page_count: int
    is_encrypted: bool
    title: str = ""
    file_size: int = 0


class PDFEngine:
    """Stateless façade over PyMuPDF for every supported PDF operation."""

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _open(path: str, password: str | None = None) -> fitz.Document:
        """
        Open a PDF safely, raising application-specific exceptions instead
        of letting raw `fitz`/`RuntimeError` exceptions leak upward.
        """
        p = Path(path)
        if not p.exists():
            raise CorruptedPDFError(f"File not found: {path}")
        if p.suffix.lower() != ".pdf":
            raise UnsupportedFileError(f"Not a PDF file: {path}")

        try:
            doc = fitz.open(path)
        except Exception as exc:  # pragma: no cover - fitz raises plain Exception
            logger.error("Failed to open '%s': %s", path, exc)
            raise CorruptedPDFError(
                f"'{p.name}' could not be opened. It may be corrupted or "
                f"not a valid PDF file."
            ) from exc

        if doc.is_encrypted:
            if password is None:
                doc.close()
                raise EncryptedPDFError(
                    f"'{p.name}' is password-protected. Please supply the password."
                )
            if not doc.authenticate(password):
                doc.close()
                raise InvalidPasswordError(f"Incorrect password for '{p.name}'.")

        if doc.page_count == 0:
            doc.close()
            raise CorruptedPDFError(f"'{p.name}' contains no readable pages.")

        return doc

    @staticmethod
    def validate_pdf(path: str, password: str | None = None) -> PDFInfo:
        """Open + immediately close a PDF purely to validate/inspect it."""
        doc = PDFEngine._open(path, password)
        try:
            info = PDFInfo(
                path=path,
                page_count=doc.page_count,
                is_encrypted=doc.is_encrypted,
                title=(doc.metadata or {}).get("title") or Path(path).stem,
                file_size=os.path.getsize(path),
            )
            return info
        finally:
            doc.close()

    # ------------------------------------------------------------------ #
    # Merge
    # ------------------------------------------------------------------ #

    @staticmethod
    def merge(
        files: Sequence[str],
        output_path: str,
        passwords: dict[str, str] | None = None,
    ) -> str:
        """Merge `files` (in given order) into a single PDF at `output_path`."""
        if not files:
            raise EmptyInputError("No files were provided to merge.")
        passwords = passwords or {}

        merged = fitz.open()
        try:
            for f in files:
                src = PDFEngine._open(f, passwords.get(f))
                try:
                    page_count = src.page_count
                    merged.insert_pdf(src)
                finally:
                    src.close()
                logger.info("Merged '%s' (%d pages)", f, page_count)

            output_path = str(unique_path(output_path))
            merged.save(output_path)
            logger.info("Merge complete -> '%s' (%d pages)", output_path, merged.page_count)
            return output_path
        finally:
            merged.close()

    # ------------------------------------------------------------------ #
    # Split
    # ------------------------------------------------------------------ #

    @staticmethod
    def split(
        file: str,
        output_dir: str,
        mode: str = "every_page",
        ranges: Sequence[tuple[int, int]] | None = None,
        password: str | None = None,
    ) -> list[str]:
        """
        Split a PDF.

        mode="every_page": one output file per page.
        mode="ranges": `ranges` is a list of 0-indexed (start, end_inclusive)
                       tuples, each producing one output file.
        """
        doc = PDFEngine._open(file, password)
        try:
            ensure_dir(output_dir)
            stem = Path(file).stem
            outputs: list[str] = []

            if mode == "every_page":
                for i in range(doc.page_count):
                    out = fitz.open()
                    out.insert_pdf(doc, from_page=i, to_page=i)
                    out_path = str(unique_path(Path(output_dir) / f"{stem}_page{i + 1}.pdf"))
                    out.save(out_path)
                    out.close()
                    outputs.append(out_path)

            elif mode == "ranges":
                if not ranges:
                    raise PageRangeError("No page ranges supplied for split.")
                for idx, (start, end) in enumerate(ranges, start=1):
                    if start < 0 or end >= doc.page_count or start > end:
                        raise PageRangeError(
                            f"Invalid range ({start + 1}-{end + 1}) for a "
                            f"{doc.page_count}-page document."
                        )
                    out = fitz.open()
                    out.insert_pdf(doc, from_page=start, to_page=end)
                    out_path = str(
                        unique_path(
                            Path(output_dir) / f"{stem}_part{idx}_p{start + 1}-{end + 1}.pdf"
                        )
                    )
                    out.save(out_path)
                    out.close()
                    outputs.append(out_path)
            else:
                raise ValueError(f"Unknown split mode: {mode}")

            logger.info("Split '%s' into %d file(s) in '%s'", file, len(outputs), output_dir)
            return outputs
        finally:
            doc.close()

    # ------------------------------------------------------------------ #
    # Rotate
    # ------------------------------------------------------------------ #

    @staticmethod
    def rotate_pages(
        file: str,
        output_path: str,
        angle: int,
        pages: Iterable[int] | None = None,
        password: str | None = None,
    ) -> str:
        """
        Rotate `pages` (0-indexed) by `angle` degrees (multiple of 90,
        positive = clockwise). If `pages` is None, rotate every page.
        """
        if angle % 90 != 0:
            raise ValueError("Rotation angle must be a multiple of 90 degrees.")

        doc = PDFEngine._open(file, password)
        try:
            target_pages = list(pages) if pages is not None else range(doc.page_count)
            for i in target_pages:
                if i < 0 or i >= doc.page_count:
                    raise PageRangeError(f"Page {i + 1} is out of range.")
                page = doc[i]
                new_rotation = (page.rotation + angle) % 360
                page.set_rotation(new_rotation)

            output_path = str(unique_path(output_path))
            doc.save(output_path)
            logger.info("Rotated %d page(s) in '%s' by %d degrees", len(target_pages), file, angle)
            return output_path
        finally:
            doc.close()

    # ------------------------------------------------------------------ #
    # Delete pages
    # ------------------------------------------------------------------ #

    @staticmethod
    def delete_pages(
        file: str,
        output_path: str,
        pages: Iterable[int],
        password: str | None = None,
    ) -> str:
        """Delete `pages` (0-indexed) from the document."""
        doc = PDFEngine._open(file, password)
        try:
            pages = sorted(set(pages))
            if not pages:
                raise EmptyInputError("No pages selected for deletion.")
            if any(p < 0 or p >= doc.page_count for p in pages):
                raise PageRangeError("One or more selected pages are out of range.")
            if len(pages) >= doc.page_count:
                raise PageRangeError("Cannot delete every page in the document.")

            doc.delete_pages(pages)
            output_path = str(unique_path(output_path))
            doc.save(output_path)
            logger.info("Deleted %d page(s) from '%s'", len(pages), file)
            return output_path
        finally:
            doc.close()

    # ------------------------------------------------------------------ #
    # Reorder pages
    # ------------------------------------------------------------------ #

    @staticmethod
    def reorder_pages(
        file: str,
        output_path: str,
        new_order: Sequence[int],
        password: str | None = None,
    ) -> str:
        """
        Reorder pages according to `new_order`, a permutation of
        0-indexed page numbers (e.g. [2, 0, 1] moves page 3 to the front).
        """
        doc = PDFEngine._open(file, password)
        try:
            if sorted(new_order) != list(range(doc.page_count)):
                raise PageRangeError(
                    "The new page order must contain every page exactly once."
                )
            doc.select(list(new_order))
            output_path = str(unique_path(output_path))
            doc.save(output_path)
            logger.info("Reordered pages in '%s'", file)
            return output_path
        finally:
            doc.close()

    @staticmethod
    def select_pages(
        file: str,
        output_path: str,
        page_indices: Sequence[int],
        password: str | None = None,
    ) -> str:
        """
        Build a new document containing exactly `page_indices` (0-indexed),
        in the given order. Unlike `reorder_pages`, this does not need to
        cover every original page -- it is the combined "delete some pages
        and/or reorder the rest" operation.
        """
        doc = PDFEngine._open(file, password)
        try:
            if not page_indices:
                raise EmptyInputError("At least one page must be selected.")
            if any(p < 0 or p >= doc.page_count for p in page_indices):
                raise PageRangeError("One or more selected pages are out of range.")

            doc.select(list(page_indices))
            output_path = str(unique_path(output_path))
            doc.save(output_path)
            logger.info(
                "Saved %d selected page(s) from '%s' -> '%s'",
                len(page_indices), file, output_path,
            )
            return output_path
        finally:
            doc.close()

    # ------------------------------------------------------------------ #
    # Extract text
    # ------------------------------------------------------------------ #

    @staticmethod
    def extract_text(
        file: str,
        pages: Iterable[int] | None = None,
        password: str | None = None,
    ) -> str:
        """Return the extracted plain text of `pages` (0-indexed), or all pages."""
        doc = PDFEngine._open(file, password)
        try:
            target_pages = list(pages) if pages is not None else range(doc.page_count)
            chunks = []
            for i in target_pages:
                if i < 0 or i >= doc.page_count:
                    raise PageRangeError(f"Page {i + 1} is out of range.")
                text = doc[i].get_text("text")
                chunks.append(f"--- Page {i + 1} ---\n{text}")
            logger.info("Extracted text from %d page(s) of '%s'", len(target_pages), file)
            return "\n\n".join(chunks)
        finally:
            doc.close()

    @staticmethod
    def extract_text_to_file(
        file: str,
        output_txt: str,
        pages: Iterable[int] | None = None,
        password: str | None = None,
    ) -> str:
        text = PDFEngine.extract_text(file, pages, password)
        output_txt = str(unique_path(output_txt))
        Path(output_txt).write_text(text, encoding="utf-8")
        return output_txt

    # ------------------------------------------------------------------ #
    # Image <-> PDF conversion
    # ------------------------------------------------------------------ #

    @staticmethod
    def images_to_pdf(images: Sequence[str], output_path: str) -> str:
        """Combine one or more image files into a single PDF (one page each)."""
        if not images:
            raise EmptyInputError("No images were provided.")

        pil_images: list[Image.Image] = []
        try:
            for img_path in images:
                if not is_image(img_path):
                    raise UnsupportedFileError(f"Unsupported image file: {img_path}")
                try:
                    im = Image.open(img_path)
                    im = im.convert("RGB")
                except Exception as exc:
                    raise CorruptedPDFError(f"Could not read image '{img_path}': {exc}") from exc
                pil_images.append(im)

            output_path = str(unique_path(output_path))
            first, rest = pil_images[0], pil_images[1:]
            first.save(output_path, save_all=True, append_images=rest)
            logger.info("Converted %d image(s) to PDF -> '%s'", len(images), output_path)
            return output_path
        finally:
            for im in pil_images:
                im.close()

    @staticmethod
    def pdf_to_images(
        file: str,
        output_dir: str,
        dpi: int = 150,
        image_format: str = "png",
        pages: Iterable[int] | None = None,
        password: str | None = None,
    ) -> list[str]:
        """Render each page of `file` to a raster image."""
        doc = PDFEngine._open(file, password)
        try:
            ensure_dir(output_dir)
            stem = Path(file).stem
            zoom = dpi / 72.0
            matrix = fitz.Matrix(zoom, zoom)
            target_pages = list(pages) if pages is not None else range(doc.page_count)

            outputs = []
            for i in target_pages:
                if i < 0 or i >= doc.page_count:
                    raise PageRangeError(f"Page {i + 1} is out of range.")
                pix = doc[i].get_pixmap(matrix=matrix)
                out_path = str(
                    unique_path(Path(output_dir) / f"{stem}_page{i + 1}.{image_format}")
                )
                pix.save(out_path)
                outputs.append(out_path)

            logger.info("Rendered %d page(s) of '%s' to images", len(outputs), file)
            return outputs
        finally:
            doc.close()

    # ------------------------------------------------------------------ #
    # Preview (single-page render, returns a PIL Image directly)
    # ------------------------------------------------------------------ #

    @staticmethod
    def render_page(
        file: str,
        page_index: int,
        zoom: float = 1.5,
        password: str | None = None,
    ) -> Image.Image:
        """Render a single page (0-indexed) to a PIL Image for on-screen preview."""
        doc = PDFEngine._open(file, password)
        try:
            if page_index < 0 or page_index >= doc.page_count:
                raise PageRangeError(f"Page {page_index + 1} is out of range.")
            matrix = fitz.Matrix(zoom, zoom)
            pix = doc[page_index].get_pixmap(matrix=matrix)
            mode = "RGB" if pix.n < 4 else "RGBA"
            img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
            return img
        finally:
            doc.close()

    # ------------------------------------------------------------------ #
    # Watermark
    # ------------------------------------------------------------------ #

    @staticmethod
    def add_text_watermark(
        file: str,
        output_path: str,
        text: str,
        password: str | None = None,
        opacity: float = 0.3,
        font_size: int = 40,
        rotate: int = 45,
        color: tuple[float, float, float] = (0.5, 0.5, 0.5),
    ) -> str:
        """Stamp a diagonal repeating text watermark onto every page."""
        if not text.strip():
            raise EmptyInputError("Watermark text is empty.")

        doc = PDFEngine._open(file, password)
        try:
            for page in doc:
                rect = page.rect
                page.insert_textbox(
                    rect,
                    text,
                    fontsize=font_size,
                    fontname="helv",
                    color=color,
                    fill_opacity=opacity,
                    rotate=rotate % 360 if rotate % 360 in (0, 90, 180, 270) else 0,
                    align=1,
                )
            output_path = str(unique_path(output_path))
            doc.save(output_path)
            logger.info("Applied text watermark to '%s'", file)
            return output_path
        finally:
            doc.close()

    @staticmethod
    def add_image_watermark(
        file: str,
        output_path: str,
        image_path: str,
        password: str | None = None,
        opacity: float = 0.3,
        scale: float = 0.5,
    ) -> str:
        """Stamp a centered, semi-transparent image watermark onto every page."""
        if not is_image(image_path):
            raise UnsupportedFileError(f"Unsupported watermark image: {image_path}")

        doc = PDFEngine._open(file, password)
        try:
            for page in doc:
                rect = page.rect
                w, h = rect.width * scale, rect.height * scale
                x0 = (rect.width - w) / 2
                y0 = (rect.height - h) / 2
                target_rect = fitz.Rect(x0, y0, x0 + w, y0 + h)
                page.insert_image(target_rect, filename=image_path, overlay=True)
            output_path = str(unique_path(output_path))
            doc.save(output_path)
            logger.info("Applied image watermark to '%s'", file)
            return output_path
        finally:
            doc.close()

    # ------------------------------------------------------------------ #
    # Password protection
    # ------------------------------------------------------------------ #

    @staticmethod
    def set_password(
        file: str,
        output_path: str,
        user_password: str,
        owner_password: str | None = None,
        current_password: str | None = None,
        allow_printing: bool = True,
        allow_copy: bool = True,
    ) -> str:
        """Encrypt `file`, requiring `user_password` to open it."""
        if not user_password:
            raise EmptyInputError("A password is required to protect the PDF.")

        doc = PDFEngine._open(file, current_password)
        try:
            perms = fitz.PDF_PERM_ACCESSIBILITY
            if allow_printing:
                perms |= fitz.PDF_PERM_PRINT
            if allow_copy:
                perms |= fitz.PDF_PERM_COPY

            output_path = str(unique_path(output_path))
            doc.save(
                output_path,
                encryption=fitz.PDF_ENCRYPT_AES_256,
                owner_pw=owner_password or user_password,
                user_pw=user_password,
                permissions=perms,
            )
            logger.info("Password-protected '%s' -> '%s'", file, output_path)
            return output_path
        finally:
            doc.close()

    @staticmethod
    def remove_password(file: str, output_path: str, current_password: str) -> str:
        """Decrypt `file`, producing an unencrypted copy."""
        doc = PDFEngine._open(file, current_password)
        try:
            output_path = str(unique_path(output_path))
            doc.save(output_path, encryption=fitz.PDF_ENCRYPT_NONE)
            logger.info("Removed password protection from '%s'", file)
            return output_path
        finally:
            doc.close()
