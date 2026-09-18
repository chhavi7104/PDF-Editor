"""
FileListWidget
==============

A reusable list-box with "Add files", "Remove selected", "Move up",
"Move down" and "Clear" controls. Used by any tab that needs the user
to build an ordered list of input files (Merge, Split, image-to-PDF,
page reordering context, etc).
"""

from __future__ import annotations

from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from pdf_editor.gui import theme


class FileListWidget(ctk.CTkFrame):
    def __init__(
        self,
        master,
        filetypes: list[tuple[str, str]],
        allow_multiple: bool = True,
        on_change: Callable[[list[str]], None] | None = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.filetypes = filetypes
        self.allow_multiple = allow_multiple
        self.on_change = on_change
        self._files: list[str] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        button_bar = ctk.CTkFrame(self, fg_color="transparent")
        button_bar.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        ctk.CTkButton(button_bar, text="Add Files", width=100, command=self._add_files).pack(
            side="left", padx=(0, 6)
        )
        ctk.CTkButton(button_bar, text="Remove", width=90, command=self._remove_selected).pack(
            side="left", padx=6
        )
        ctk.CTkButton(button_bar, text="Up", width=50, command=lambda: self._move(-1)).pack(
            side="left", padx=6
        )
        ctk.CTkButton(button_bar, text="Down", width=60, command=lambda: self._move(1)).pack(
            side="left", padx=6
        )
        ctk.CTkButton(
            button_bar, text="Clear", width=70, fg_color="#b3413e", hover_color="#8f3230",
            command=self._clear,
        ).pack(side="left", padx=6)

        self.listbox = ctk.CTkScrollableFrame(self, label_text="")
        self.listbox.grid(row=1, column=0, sticky="nsew")
        self.listbox.grid_columnconfigure(0, weight=1)

        self._row_widgets: list[ctk.CTkLabel] = []
        self._selected_index: int | None = None

    # ------------------------------------------------------------------ #

    def files(self) -> list[str]:
        return list(self._files)

    def set_files(self, files: list[str]) -> None:
        self._files = list(files)
        self._refresh()

    def _add_files(self) -> None:
        if self.allow_multiple:
            paths = filedialog.askopenfilenames(filetypes=self.filetypes)
        else:
            single = filedialog.askopenfilename(filetypes=self.filetypes)
            paths = (single,) if single else ()
        if not paths:
            return
        for p in paths:
            if p and p not in self._files:
                self._files.append(p)
        self._refresh()

    def _remove_selected(self) -> None:
        if self._selected_index is None:
            return
        del self._files[self._selected_index]
        self._selected_index = None
        self._refresh()

    def _move(self, delta: int) -> None:
        i = self._selected_index
        if i is None:
            return
        j = i + delta
        if 0 <= j < len(self._files):
            self._files[i], self._files[j] = self._files[j], self._files[i]
            self._selected_index = j
            self._refresh()

    def _clear(self) -> None:
        self._files = []
        self._selected_index = None
        self._refresh()

    def _select(self, index: int) -> None:
        self._selected_index = index
        self._refresh()

    def _refresh(self) -> None:
        for w in self._row_widgets:
            w.destroy()
        self._row_widgets = []

        from pdf_editor.utils.file_utils import human_size
        import os

        for i, path in enumerate(self._files):
            name = path.split("/")[-1].split("\\")[-1]
            try:
                size = human_size(os.path.getsize(path))
            except OSError:
                size = "?"
            is_selected = i == self._selected_index
            row = ctk.CTkLabel(
                self.listbox,
                text=f"{i + 1}.  {name}   ({size})",
                anchor="w",
                fg_color=("#dbe9ff" if is_selected else "transparent"),
                corner_radius=6,
                font=theme.FONT_BODY,
            )
            row.grid(row=i, column=0, sticky="ew", padx=2, pady=1)
            row.bind("<Button-1>", lambda _e, idx=i: self._select(idx))
            self._row_widgets.append(row)

        if self.on_change:
            self.on_change(self.files())
