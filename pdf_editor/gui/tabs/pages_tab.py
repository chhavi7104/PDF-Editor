"""
Delete & Reorder Pages tab.

Both operations share the same mental model (a list of the document's
pages that the user rearranges/prunes), so they live in one tab: a
scrollable list of "Page N" rows that can be selected for deletion, or
dragged via Up/Down buttons to define a new order.
"""

from __future__ import annotations

from tkinter import filedialog

import customtkinter as ctk

from pdf_editor.core.engine import PDFEngine
from pdf_editor.gui import theme
from pdf_editor.gui.tabs.base_tab import BaseTab


class PagesTab(BaseTab):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._source_file: str | None = None
        self._page_order: list[int] = []          # 0-indexed order, current working state
        self._checked: dict[int, ctk.BooleanVar] = {}  # original page index -> "keep" checkbox
        self._row_widgets: list[ctk.CTkFrame] = []
        self._selected_row: int | None = None

        ctk.CTkLabel(self, text="Delete & Reorder Pages", font=theme.FONT_HEADER).grid(
            row=0, column=0, sticky="w", padx=theme.PAD_X, pady=(theme.PAD_Y, 0)
        )
        ctk.CTkLabel(
            self,
            text="Uncheck pages to delete them. Select a row and use Up/Down to reorder.",
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
        ctk.CTkButton(file_row, text="Up", width=50, command=lambda: self._move(-1)).pack(
            side="left", padx=(20, 4)
        )
        ctk.CTkButton(file_row, text="Down", width=60, command=lambda: self._move(1)).pack(
            side="left", padx=4
        )

        self.pages_frame = ctk.CTkScrollableFrame(self, label_text="Pages")
        self.pages_frame.grid(row=3, column=0, sticky="nsew", padx=theme.PAD_X)
        self.pages_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(self, text="Apply & Save As...", command=self._on_apply).grid(
            row=4, column=0, sticky="w", padx=theme.PAD_X, pady=theme.PAD_Y
        )

        self.build_log_console(self, row=5, padx=theme.PAD_X, pady=(0, theme.PAD_X))

    # ------------------------------------------------------------------ #

    def _choose_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not path:
            return

        def action():
            return PDFEngine.validate_pdf(path)

        def on_success(info):
            self._source_file = path
            self.file_label.configure(text=path.split("/")[-1].split("\\")[-1])
            self._page_order = list(range(info.page_count))
            self._checked = {i: ctk.BooleanVar(value=True) for i in range(info.page_count)}
            self._selected_row = None
            self._rebuild_rows()

        self.run_safely(action, success_message="Loaded document.", on_success=on_success)

    def _rebuild_rows(self) -> None:
        for w in self._row_widgets:
            w.destroy()
        self._row_widgets = []

        for row_pos, original_index in enumerate(self._page_order):
            row = ctk.CTkFrame(
                self.pages_frame,
                fg_color=("#dbe9ff" if row_pos == self._selected_row else "transparent"),
                corner_radius=6,
            )
            row.grid(row=row_pos, column=0, sticky="ew", pady=1)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkCheckBox(
                row, text="", variable=self._checked[original_index], width=20
            ).grid(row=0, column=0, padx=(4, 8))

            label = ctk.CTkLabel(
                row,
                text=f"Position {row_pos + 1}  —  Original Page {original_index + 1}",
                anchor="w",
                font=theme.FONT_BODY,
            )
            label.grid(row=0, column=1, sticky="ew")
            label.bind("<Button-1>", lambda _e, rp=row_pos: self._select(rp))
            row.bind("<Button-1>", lambda _e, rp=row_pos: self._select(rp))

            self._row_widgets.append(row)

    def _select(self, row_pos: int) -> None:
        self._selected_row = row_pos
        self._rebuild_rows()

    def _move(self, delta: int) -> None:
        i = self._selected_row
        if i is None:
            return
        j = i + delta
        if 0 <= j < len(self._page_order):
            self._page_order[i], self._page_order[j] = self._page_order[j], self._page_order[i]
            self._selected_row = j
            self._rebuild_rows()

    # ------------------------------------------------------------------ #

    def _on_apply(self) -> None:
        if not self._source_file:
            self.log_console.warning("Choose a PDF file first.")
            return

        kept_order = [i for i in self._page_order if self._checked[i].get()]
        deleted = [i for i in self._page_order if not self._checked[i].get()]

        if not kept_order:
            self.log_console.warning("At least one page must remain.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="edited.pdf",
        )
        if not output_path:
            return

        def action():
            # A single selection call covers both "which pages survive" and
            # "in what order" as one atomic engine call.
            return PDFEngine.select_pages(self._source_file, output_path, kept_order)

        self.run_safely(
            action,
            success_message=(
                f"Saved {len(kept_order)} page(s)"
                + (f", removed {len(deleted)}" if deleted else "")
                + f" -> {output_path}"
            ),
        )
