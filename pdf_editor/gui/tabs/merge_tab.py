"""Merge multiple PDFs into a single file, in a user-defined order."""

from __future__ import annotations

from tkinter import filedialog

import customtkinter as ctk

from pdf_editor.core.engine import PDFEngine
from pdf_editor.gui import theme
from pdf_editor.gui.tabs.base_tab import BaseTab
from pdf_editor.gui.widgets.file_list import FileListWidget


class MergeTab(BaseTab):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Merge PDFs", font=theme.FONT_HEADER).grid(
            row=0, column=0, sticky="w", padx=theme.PAD_X, pady=(theme.PAD_Y, 0)
        )
        ctk.CTkLabel(
            self,
            text="Add two or more PDFs, arrange them with Up/Down, then merge.",
            font=theme.FONT_BODY,
            text_color="gray",
        ).grid(row=1, column=0, sticky="w", padx=theme.PAD_X, pady=(0, theme.PAD_Y))

        self.file_list = FileListWidget(self, filetypes=[("PDF files", "*.pdf")])
        self.file_list.grid(row=2, column=0, sticky="nsew", padx=theme.PAD_X)

        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.grid(row=3, column=0, sticky="ew", padx=theme.PAD_X, pady=theme.PAD_Y)
        ctk.CTkButton(action_bar, text="Merge & Save As...", command=self._on_merge).pack(
            side="left"
        )

        self.build_log_console(self, row=4, padx=theme.PAD_X, pady=(0, theme.PAD_X))

    def _on_merge(self) -> None:
        files = self.file_list.files()
        if len(files) < 2:
            self.log_console.warning("Add at least two PDF files to merge.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="merged.pdf",
            title="Save merged PDF as",
        )
        if not output_path:
            return

        self.run_safely(
            lambda: PDFEngine.merge(files, output_path),
            success_message=f"Merged {len(files)} files -> {output_path}",
        )
