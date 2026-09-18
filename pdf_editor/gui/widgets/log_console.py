"""
LogConsole
==========

A small read-only text box each tab can push status/error messages into,
color-coded by severity. Gives the user visible feedback beyond a single
popup, and keeps a scrollable history of what happened during a session.
"""

from __future__ import annotations

import customtkinter as ctk

from pdf_editor.gui import theme


class LogConsole(ctk.CTkFrame):
    def __init__(self, master, height: int = 120, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.textbox = ctk.CTkTextbox(self, height=height, font=theme.FONT_MONO, wrap="word")
        self.textbox.grid(row=0, column=0, sticky="nsew")
        self.textbox.configure(state="disabled")

        self.textbox.tag_config("info", foreground="#3b8fd4")
        self.textbox.tag_config("success", foreground=theme.SUCCESS_COLOR)
        self.textbox.tag_config("error", foreground=theme.ERROR_COLOR)
        self.textbox.tag_config("warning", foreground=theme.WARNING_COLOR)

    def _write(self, message: str, tag: str) -> None:
        self.textbox.configure(state="normal")
        self.textbox.insert("end", message + "\n", tag)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def info(self, message: str) -> None:
        self._write(f"ℹ  {message}", "info")

    def success(self, message: str) -> None:
        self._write(f"✓  {message}", "success")

    def error(self, message: str) -> None:
        self._write(f"✗  {message}", "error")

    def warning(self, message: str) -> None:
        self._write(f"⚠  {message}", "warning")

    def clear(self) -> None:
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
