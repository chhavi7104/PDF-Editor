"""Render and page through a PDF's pages, including prompting for a password
if the document is encrypted."""

from __future__ import annotations

from tkinter import filedialog, simpledialog

import customtkinter as ctk
from PIL import Image

from pdf_editor.core.engine import PDFEngine
from pdf_editor.core.exceptions import EncryptedPDFError
from pdf_editor.gui import theme
from pdf_editor.gui.tabs.base_tab import BaseTab


class PreviewTab(BaseTab):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._source_file: str | None = None
        self._password: str | None = None
        self._page_count = 0
        self._current_page = 0
        self._zoom = 1.5
        self._tk_image = None  # keep a reference to avoid garbage collection

        ctk.CTkLabel(self, text="Page Preview", font=theme.FONT_HEADER).grid(
            row=0, column=0, sticky="w", padx=theme.PAD_X, pady=(theme.PAD_Y, 0)
        )

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", padx=theme.PAD_X, pady=4)
        ctk.CTkButton(controls, text="Choose PDF...", command=self._choose_file, width=140).pack(
            side="left"
        )
        ctk.CTkButton(controls, text="◀ Prev", width=70, command=lambda: self._go(-1)).pack(
            side="left", padx=(20, 4)
        )
        ctk.CTkButton(controls, text="Next ▶", width=70, command=lambda: self._go(1)).pack(
            side="left", padx=4
        )
        self.page_indicator = ctk.CTkLabel(controls, text="No document loaded", font=theme.FONT_BODY)
        self.page_indicator.pack(side="left", padx=16)

        ctk.CTkButton(controls, text="Zoom -", width=70, command=lambda: self._change_zoom(-0.25)).pack(
            side="right", padx=4
        )
        ctk.CTkButton(controls, text="Zoom +", width=70, command=lambda: self._change_zoom(0.25)).pack(
            side="right", padx=4
        )

        self.canvas_frame = ctk.CTkScrollableFrame(self, label_text="")
        self.canvas_frame.grid(row=2, column=0, sticky="nsew", padx=theme.PAD_X)
        self.image_label = ctk.CTkLabel(self.canvas_frame, text="")
        self.image_label.pack(padx=4, pady=4)

        self.build_log_console(self, row=3, padx=theme.PAD_X, pady=(4, theme.PAD_X))

    # ------------------------------------------------------------------ #

    def _choose_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        self._source_file = path
        self._password = None
        self._load(page_index=0)

    def _load(self, page_index: int) -> None:
        def action():
            try:
                info = PDFEngine.validate_pdf(self._source_file, self._password)
            except EncryptedPDFError:
                pw = simpledialog.askstring(
                    "Password Required", "This PDF is encrypted. Enter password:", show="•"
                )
                if pw is None:
                    raise
                self._password = pw
                info = PDFEngine.validate_pdf(self._source_file, self._password)
            return info

        def on_success(info):
            self._page_count = info.page_count
            self._current_page = max(0, min(page_index, info.page_count - 1))
            self._render_current_page()

        self.run_safely(action, success_message="Document loaded.", on_success=on_success)

    def _render_current_page(self) -> None:
        def action():
            return PDFEngine.render_page(
                self._source_file, self._current_page, zoom=self._zoom, password=self._password
            )

        def on_success(pil_image: Image.Image):
            self._tk_image = ctk.CTkImage(
                light_image=pil_image, dark_image=pil_image,
                size=(pil_image.width, pil_image.height),
            )
            self.image_label.configure(image=self._tk_image, text="")
            self.page_indicator.configure(
                text=f"Page {self._current_page + 1} of {self._page_count}"
            )

        self.run_safely(action, success_message="Rendered page.", on_success=on_success)

    def _go(self, delta: int) -> None:
        if not self._source_file or self._page_count == 0:
            self.log_console.warning("Choose a PDF file first.")
            return
        new_page = self._current_page + delta
        if 0 <= new_page < self._page_count:
            self._current_page = new_page
            self._render_current_page()

    def _change_zoom(self, delta: float) -> None:
        if not self._source_file:
            return
        self._zoom = max(0.5, min(4.0, self._zoom + delta))
        self._render_current_page()
