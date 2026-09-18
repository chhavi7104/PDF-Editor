"""
pdf_editor.gui.app
===================

`App` is the top-level CustomTkinter window. It hosts a `CTkTabview`
with one tab per feature, a menu-less top bar showing the app title,
and a status/about footer. Keeping this file thin -- it only assembles
already-built tab frames -- makes the overall structure easy to extend:
adding a new feature means writing one new tab module and registering
it here.
"""

from __future__ import annotations

import customtkinter as ctk

from pdf_editor import __version__
from pdf_editor.gui import theme
from pdf_editor.gui.tabs.convert_tab import ConvertTab
from pdf_editor.gui.tabs.extract_tab import ExtractTextTab
from pdf_editor.gui.tabs.merge_tab import MergeTab
from pdf_editor.gui.tabs.pages_tab import PagesTab
from pdf_editor.gui.tabs.preview_tab import PreviewTab
from pdf_editor.gui.tabs.rotate_tab import RotateTab
from pdf_editor.gui.tabs.security_tab import SecurityTab
from pdf_editor.gui.tabs.split_tab import SplitTab
from pdf_editor.gui.tabs.watermark_tab import WatermarkTab
from pdf_editor.utils.logger import get_logger, log_file_path

logger = get_logger("gui.app")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode(theme.APPEARANCE_MODE)
        ctk.set_default_color_theme(theme.COLOR_THEME)

        self.title(f"{theme.APP_TITLE} v{__version__}")
        self.minsize(theme.APP_MIN_WIDTH, theme.APP_MIN_HEIGHT)
        self.geometry(f"{theme.APP_MIN_WIDTH}x{theme.APP_MIN_HEIGHT}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_tabs()
        self._build_footer()

        logger.info("Application started (v%s)", __version__)

    # ------------------------------------------------------------------ #

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, height=56, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        ctk.CTkLabel(
            header, text=f"📄  {theme.APP_TITLE}", font=("Segoe UI", 20, "bold")
        ).pack(side="left", padx=16, pady=10)

        ctk.CTkOptionMenu(
            header,
            values=["System", "Light", "Dark"],
            command=self._change_appearance,
            width=110,
        ).pack(side="right", padx=16, pady=10)
        ctk.CTkLabel(header, text="Appearance:", font=theme.FONT_BODY).pack(
            side="right", pady=10
        )

    def _build_tabs(self) -> None:
        self.tabview = ctk.CTkTabview(self, corner_radius=8)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 0))

        tab_registry = [
            ("Merge", MergeTab),
            ("Split", SplitTab),
            ("Rotate", RotateTab),
            ("Delete / Reorder", PagesTab),
            ("Extract Text", ExtractTextTab),
            ("Image ⇄ PDF", ConvertTab),
            ("Watermark", WatermarkTab),
            ("Password", SecurityTab),
            ("Preview", PreviewTab),
        ]

        for name, tab_cls in tab_registry:
            self.tabview.add(name)
            frame = tab_cls(self.tabview.tab(name))
            frame.pack(fill="both", expand=True)

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, height=28, corner_radius=0, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew")
        ctk.CTkLabel(
            footer,
            text=f"Logs: {log_file_path()}",
            font=("Segoe UI", 10),
            text_color="gray",
        ).pack(side="left", padx=16, pady=4)

    def _change_appearance(self, mode: str) -> None:
        ctk.set_appearance_mode(mode)
