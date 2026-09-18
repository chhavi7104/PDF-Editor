"""Split a single PDF into multiple files, either per-page or by ranges."""

from __future__ import annotations

from tkinter import filedialog

import customtkinter as ctk

from pdf_editor.core.engine import PDFEngine
from pdf_editor.gui import theme
from pdf_editor.gui.tabs.base_tab import BaseTab
from pdf_editor.utils.file_utils import parse_page_ranges


class SplitTab(BaseTab):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._source_file: str | None = None

        ctk.CTkLabel(self, text="Split PDF", font=theme.FONT_HEADER).grid(
            row=0, column=0, sticky="w", padx=theme.PAD_X, pady=(theme.PAD_Y, 0)
        )
        ctk.CTkLabel(
            self,
            text="Split a PDF into one file per page, or into custom page ranges.",
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

        self.mode_var = ctk.StringVar(value="every_page")
        mode_row = ctk.CTkFrame(self, fg_color="transparent")
        mode_row.grid(row=3, column=0, sticky="ew", padx=theme.PAD_X, pady=4)
        ctk.CTkRadioButton(
            mode_row, text="One file per page", variable=self.mode_var, value="every_page",
            command=self._toggle_mode,
        ).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(
            mode_row, text="Custom ranges", variable=self.mode_var, value="ranges",
            command=self._toggle_mode,
        ).pack(side="left")

        self.ranges_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.ranges_frame.grid(row=4, column=0, sticky="ew", padx=theme.PAD_X, pady=4)
        ctk.CTkLabel(self.ranges_frame, text="Ranges (e.g. 1-3,5,8-10):", font=theme.FONT_BODY).pack(
            side="left"
        )
        self.ranges_entry = ctk.CTkEntry(self.ranges_frame, width=260, placeholder_text="1-3,5,8-10")
        self.ranges_entry.pack(side="left", padx=8)
        self.ranges_frame.grid_remove()

        ctk.CTkButton(self, text="Split & Choose Output Folder...", command=self._on_split).grid(
            row=5, column=0, sticky="w", padx=theme.PAD_X, pady=theme.PAD_Y
        )

        self.build_log_console(self, row=6, padx=theme.PAD_X, pady=(0, theme.PAD_X))

    def _toggle_mode(self) -> None:
        if self.mode_var.get() == "ranges":
            self.ranges_frame.grid()
        else:
            self.ranges_frame.grid_remove()

    def _choose_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        self._source_file = path
        self.file_label.configure(text=path.split("/")[-1].split("\\")[-1])

    def _on_split(self) -> None:
        if not self._source_file:
            self.log_console.warning("Choose a PDF file first.")
            return

        out_dir = filedialog.askdirectory(title="Choose output folder")
        if not out_dir:
            return

        mode = self.mode_var.get()

        def action():
            if mode == "every_page":
                return PDFEngine.split(self._source_file, out_dir, mode="every_page")
            else:
                info = PDFEngine.validate_pdf(self._source_file)
                zero_indexed = parse_page_ranges(self.ranges_entry.get(), info.page_count)
                # Collapse the parsed page list into contiguous ranges
                ranges: list[tuple[int, int]] = []
                for p in zero_indexed:
                    if ranges and p == ranges[-1][1] + 1:
                        ranges[-1] = (ranges[-1][0], p)
                    else:
                        ranges.append((p, p))
                return PDFEngine.split(self._source_file, out_dir, mode="ranges", ranges=ranges)

        self.run_safely(
            action,
            success_message="Split complete.",
            on_success=lambda outputs: self.log_console.info(
                f"Created {len(outputs)} file(s) in {out_dir}"
            ),
        )
