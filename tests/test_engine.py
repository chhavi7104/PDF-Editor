"""
Unit tests for `pdf_editor.core.engine.PDFEngine`.

These tests generate their own sample PDFs/images on the fly (via PyMuPDF
and Pillow) so the suite has no external file dependencies and can run
anywhere, e.g. `python -m pytest tests/ -v`.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import pymupdf as fitz
from PIL import Image

from pdf_editor.core.engine import PDFEngine
from pdf_editor.core.exceptions import (
    CorruptedPDFError,
    EmptyInputError,
    EncryptedPDFError,
    InvalidPasswordError,
    PageRangeError,
)


def make_pdf(path: str, page_count: int, label: str = "") -> str:
    doc = fitz.open()
    for i in range(page_count):
        page = doc.new_page()
        page.insert_text((72, 72), f"{label} page {i + 1}")
    doc.save(path)
    doc.close()
    return path


class PDFEngineTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="pdf_editor_test_"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def p(self, name: str) -> str:
        return str(self.tmpdir / name)

    # -- validate ---------------------------------------------------- #

    def test_validate_pdf_ok(self):
        f = make_pdf(self.p("a.pdf"), 3, "A")
        info = PDFEngine.validate_pdf(f)
        self.assertEqual(info.page_count, 3)
        self.assertFalse(info.is_encrypted)

    def test_validate_corrupted_pdf(self):
        bad = self.p("bad.pdf")
        Path(bad).write_bytes(b"not a real pdf file at all")
        with self.assertRaises(CorruptedPDFError):
            PDFEngine.validate_pdf(bad)

    def test_validate_missing_file(self):
        with self.assertRaises(CorruptedPDFError):
            PDFEngine.validate_pdf(self.p("does_not_exist.pdf"))

    # -- merge --------------------------------------------------------#

    def test_merge_two_pdfs(self):
        a = make_pdf(self.p("a.pdf"), 2, "A")
        b = make_pdf(self.p("b.pdf"), 3, "B")
        out = PDFEngine.merge([a, b], self.p("merged.pdf"))
        info = PDFEngine.validate_pdf(out)
        self.assertEqual(info.page_count, 5)

    def test_merge_empty_list_raises(self):
        with self.assertRaises(EmptyInputError):
            PDFEngine.merge([], self.p("out.pdf"))

    # -- split ----------------------------------------------------------#

    def test_split_every_page(self):
        f = make_pdf(self.p("a.pdf"), 4, "A")
        out_dir = self.p("split_out")
        outputs = PDFEngine.split(f, out_dir, mode="every_page")
        self.assertEqual(len(outputs), 4)
        for o in outputs:
            self.assertEqual(PDFEngine.validate_pdf(o).page_count, 1)

    def test_split_ranges(self):
        f = make_pdf(self.p("a.pdf"), 6, "A")
        out_dir = self.p("split_out2")
        outputs = PDFEngine.split(f, out_dir, mode="ranges", ranges=[(0, 1), (2, 5)])
        self.assertEqual(len(outputs), 2)
        self.assertEqual(PDFEngine.validate_pdf(outputs[0]).page_count, 2)
        self.assertEqual(PDFEngine.validate_pdf(outputs[1]).page_count, 4)

    def test_split_bad_range_raises(self):
        f = make_pdf(self.p("a.pdf"), 3, "A")
        with self.assertRaises(PageRangeError):
            PDFEngine.split(f, self.p("out3"), mode="ranges", ranges=[(0, 10)])

    # -- rotate ---------------------------------------------------------#

    def test_rotate_all_pages(self):
        f = make_pdf(self.p("a.pdf"), 2, "A")
        out = PDFEngine.rotate_pages(f, self.p("rotated.pdf"), 90)
        doc = fitz.open(out)
        self.assertEqual(doc[0].rotation, 90)
        self.assertEqual(doc[1].rotation, 90)
        doc.close()

    def test_rotate_invalid_angle(self):
        f = make_pdf(self.p("a.pdf"), 1, "A")
        with self.assertRaises(ValueError):
            PDFEngine.rotate_pages(f, self.p("out.pdf"), 45)

    # -- delete -----------------------------------------------------------#

    def test_delete_pages(self):
        f = make_pdf(self.p("a.pdf"), 5, "A")
        out = PDFEngine.delete_pages(f, self.p("deleted.pdf"), [0, 2])
        self.assertEqual(PDFEngine.validate_pdf(out).page_count, 3)

    def test_delete_all_pages_raises(self):
        f = make_pdf(self.p("a.pdf"), 2, "A")
        with self.assertRaises(PageRangeError):
            PDFEngine.delete_pages(f, self.p("out.pdf"), [0, 1])

    # -- reorder ----------------------------------------------------------#

    def test_reorder_pages(self):
        f = make_pdf(self.p("a.pdf"), 3, "A")
        out = PDFEngine.reorder_pages(f, self.p("reordered.pdf"), [2, 0, 1])
        doc = fitz.open(out)
        self.assertIn("page 3", doc[0].get_text())
        self.assertIn("page 1", doc[1].get_text())
        self.assertIn("page 2", doc[2].get_text())
        doc.close()

    def test_reorder_invalid_permutation(self):
        f = make_pdf(self.p("a.pdf"), 3, "A")
        with self.assertRaises(PageRangeError):
            PDFEngine.reorder_pages(f, self.p("out.pdf"), [0, 1])

    def test_select_pages_subset_and_reorder(self):
        f = make_pdf(self.p("a.pdf"), 4, "A")
        # Keep pages 4 and 2 (0-indexed 3, 1), in that order -> delete + reorder combined
        out = PDFEngine.select_pages(f, self.p("selected.pdf"), [3, 1])
        doc = fitz.open(out)
        self.assertEqual(doc.page_count, 2)
        self.assertIn("page 4", doc[0].get_text())
        self.assertIn("page 2", doc[1].get_text())
        doc.close()

    def test_select_pages_empty_raises(self):
        f = make_pdf(self.p("a.pdf"), 2, "A")
        with self.assertRaises(EmptyInputError):
            PDFEngine.select_pages(f, self.p("out.pdf"), [])

    # -- text extraction ----------------------------------------------- #

    def test_extract_text(self):
        f = make_pdf(self.p("a.pdf"), 2, "Hello")
        text = PDFEngine.extract_text(f)
        self.assertIn("Hello page 1", text)
        self.assertIn("Hello page 2", text)

    def test_extract_text_to_file(self):
        f = make_pdf(self.p("a.pdf"), 1, "Hello")
        out = PDFEngine.extract_text_to_file(f, self.p("out.txt"))
        self.assertTrue(Path(out).exists())
        self.assertIn("Hello page 1", Path(out).read_text())

    # -- image conversion ---------------------------------------------- #

    def test_images_to_pdf_and_back(self):
        img_path = self.p("img.png")
        Image.new("RGB", (200, 100), color="red").save(img_path)
        pdf_out = PDFEngine.images_to_pdf([img_path], self.p("from_img.pdf"))
        self.assertEqual(PDFEngine.validate_pdf(pdf_out).page_count, 1)

        images = PDFEngine.pdf_to_images(pdf_out, self.p("rendered"))
        self.assertEqual(len(images), 1)
        self.assertTrue(Path(images[0]).exists())

    # -- preview ------------------------------------------------------- #

    def test_render_page_returns_image(self):
        f = make_pdf(self.p("a.pdf"), 1, "A")
        img = PDFEngine.render_page(f, 0, zoom=1.0)
        self.assertIsInstance(img, Image.Image)
        self.assertGreater(img.width, 0)

    # -- watermark ------------------------------------------------------- #

    def test_text_watermark(self):
        f = make_pdf(self.p("a.pdf"), 1, "A")
        out = PDFEngine.add_text_watermark(f, self.p("wm.pdf"), "CONFIDENTIAL")
        text = PDFEngine.extract_text(out)
        self.assertIn("CONFIDENTIAL", text)

    # -- password ------------------------------------------------------- #

    def test_set_and_remove_password(self):
        f = make_pdf(self.p("a.pdf"), 2, "A")
        protected = PDFEngine.set_password(f, self.p("protected.pdf"), "secret123")

        with self.assertRaises(EncryptedPDFError):
            PDFEngine.validate_pdf(protected)

        with self.assertRaises(InvalidPasswordError):
            PDFEngine.validate_pdf(protected, password="wrong")

        info = PDFEngine.validate_pdf(protected, password="secret123")
        self.assertEqual(info.page_count, 2)

        decrypted = PDFEngine.remove_password(
            protected, self.p("decrypted.pdf"), current_password="secret123"
        )
        info2 = PDFEngine.validate_pdf(decrypted)
        self.assertFalse(info2.is_encrypted)


if __name__ == "__main__":
    unittest.main()
