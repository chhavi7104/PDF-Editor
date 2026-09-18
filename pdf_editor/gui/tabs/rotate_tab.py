"""Rotate all pages, or a chosen subset, of a PDF by 90/180/270 degrees."""

from __future__ import annotations

from tkinter import filedialog

import customtkinter as ctk

from pdf_editor.core.engine import PDFEngine
from pdf_editor.gui import theme
from pdf_editor.gui.tabs.base_tab import BaseTab
from pdf_editor.utils.file_utils import parse_page_ranges


class RotateTab(BaseTab):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._source_file: str | None = None

        ctk.CTkLabel(self, text="Rotate Pages", font=theme.FONT_HEADER).grid(
            row=0, column=0, sticky="w", padx=theme.PAD_X, pady=(theme.PAD_Y, 0)
        )
        ctk.CTkLabel(
            self,
            text="Rotate every page, or only a specific set of pages, clockwise.",
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

        angle_row = ctk.CTkFrame(self, fg_color="transparent")
        angle_row.grid(row=3, column=0, sticky="ew", padx=theme.PAD_X, pady=4)
        ctk.CTkLabel(angle_row, text="Angle:", font=theme.FONT_BODY).pack(side="left")
        self.angle_var = ctk.StringVar(value="90")
        ctk.CTkOptionMenu(angle_row, values=["90", "180", "270"], variable=self.angle_var, width=90).pack(
            side="left", padx=8
        )

        pages_row = ctk.CTkFrame(self, fg_color="transparent")
        pages_row.grid(row=4, column=0, sticky="ew", padx=theme.PAD_X, pady=4)
        self.scope_var = ctk.StringVar(value="all")
        ctk.CTkRadioButton(
            pages_row, text="All pages", variable=self.scope_var, value="all",
            command=self._toggle_scope,
        ).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(
            pages_row, text="Specific pages", variable=self.scope_var, value="specific",
            command=self._toggle_scope,
        ).pack(side="left")

        self.pages_entry_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pages_entry_frame.grid(row=5, column=0, sticky="ew", padx=theme.PAD_X, pady=4)
        ctk.CTkLabel(self.pages_entry_frame, text="Pages (e.g. 1,3,5-7):", font=theme.FONT_BODY).pack(
            side="left"
        )
        self.pages_entry = ctk.CTkEntry(self.pages_entry_frame, width=260, placeholder_text="1,3,5-7")
        self.pages_entry.pack(side="left", padx=8)
        self.pages_entry_frame.grid_remove()

        ctk.CTkButton(self, text="Rotate & Save As...", command=self._on_rotate).grid(
            row=6, column=0, sticky="w", padx=theme.PAD_X, pady=theme.PAD_Y
        )

        self.build_log_console(self, row=7, padx=theme.PAD_X, pady=(0, theme.PAD_X))

    def _toggle_scope(self) -> None:
        if self.scope_var.get() == "specific":
            self.pages_entry_frame.grid()
        else:
            self.pages_entry_frame.grid_remove()

    def _choose_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        self._source_file = path
        self.file_label.configure(text=path.split("/")[-1].split("\\")[-1])

    def _on_rotate(self) -> None:
        if not self._source_file:
            self.log_console.warning("Choose a PDF file first.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="rotated.pdf",
        )
        if not output_path:
            return

        angle = int(self.angle_var.get())

        def action():
            pages = None
            if self.scope_var.get() == "specific":
                info = PDFEngine.validate_pdf(self._source_file)
                pages = parse_page_ranges(self.pages_entry.get(), info.page_count)
            return PDFEngine.rotate_pages(self._source_file, output_path, angle, pages=pages)

        self.run_safely(action, success_message=f"Rotated pages by {angle}° -> {output_path}")
