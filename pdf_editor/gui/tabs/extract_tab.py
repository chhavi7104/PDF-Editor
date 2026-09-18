"""Extract plain text from a PDF (all pages or a chosen range) and preview/save it."""

from __future__ import annotations

from tkinter import filedialog

import customtkinter as ctk

from pdf_editor.core.engine import PDFEngine
from pdf_editor.gui import theme
from pdf_editor.gui.tabs.base_tab import BaseTab
from pdf_editor.utils.file_utils import parse_page_ranges


class ExtractTextTab(BaseTab):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)
        self._source_file: str | None = None

        ctk.CTkLabel(self, text="Extract Text", font=theme.FONT_HEADER).grid(
            row=0, column=0, sticky="w", padx=theme.PAD_X, pady=(theme.PAD_Y, 0)
        )
        ctk.CTkLabel(
            self,
            text="Pull the plain text out of a PDF for reuse, search, or archiving.",
            font=theme.FONT_BODY,
            text_color="gray",
        ).grid(row=1, column=0, sticky="w", padx=theme.PAD_X, pady=(0, theme.PAD_Y))

        file_row = ctk.CTkFrame(self, fg_color="transparent")
        file_row.grid(row=2, column=0, sticky="ew", padx=theme.PAD_X, pady=4)
        ctk.CTkButton(file_row, text="Choose PDF...", command=self._choose_file, width=140).pack(
            side="left"
        )
        self.file_label = ctk.CTkLabel(file_row, text="No file selected", font=theme.FONT_BODY)
        self.file_label.pack(side="left", padx=10)

        pages_row = ctk.CTkFrame(self, fg_color="transparent")
        pages_row.grid(row=3, column=0, sticky="ew", padx=theme.PAD_X, pady=4)
        ctk.CTkLabel(pages_row, text="Pages (blank = all):", font=theme.FONT_BODY).pack(side="left")
        self.pages_entry = ctk.CTkEntry(pages_row, width=200, placeholder_text="e.g. 1-3,5")
        self.pages_entry.pack(side="left", padx=8)

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.grid(row=4, column=0, sticky="ew", padx=theme.PAD_X, pady=4)
        ctk.CTkButton(button_row, text="Extract to Preview", command=self._on_preview).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(button_row, text="Extract & Save as .txt...", command=self._on_save).pack(
            side="left"
        )

        self.preview_box = ctk.CTkTextbox(self, font=theme.FONT_MONO, wrap="word")
        self.preview_box.grid(row=5, column=0, sticky="nsew", padx=theme.PAD_X, pady=4)

        self.build_log_console(self, row=6, padx=theme.PAD_X, pady=(0, theme.PAD_X))

    def _choose_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        self._source_file = path
        self.file_label.configure(text=path.split("/")[-1].split("\\")[-1])

    def _resolve_pages(self):
        if not self.pages_entry.get().strip():
            return None
        info = PDFEngine.validate_pdf(self._source_file)
        return parse_page_ranges(self.pages_entry.get(), info.page_count)

    def _on_preview(self) -> None:
        if not self._source_file:
            self.log_console.warning("Choose a PDF file first.")
            return

        def action():
            pages = self._resolve_pages()
            return PDFEngine.extract_text(self._source_file, pages=pages)

        def on_success(text: str):
            self.preview_box.delete("1.0", "end")
            self.preview_box.insert("1.0", text if text.strip() else "(No text found on the selected pages.)")

        self.run_safely(action, success_message="Text extracted.", on_success=on_success)

    def _on_save(self) -> None:
        if not self._source_file:
            self.log_console.warning("Choose a PDF file first.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile="extracted.txt",
        )
        if not output_path:
            return

        def action():
            pages = self._resolve_pages()
            return PDFEngine.extract_text_to_file(self._source_file, output_path, pages=pages)

        self.run_safely(action, success_message=f"Text saved -> {output_path}")
