"""
BaseTab
=======

Every feature tab (Merge, Split, Rotate, ...) subclasses this. It wires
up a shared LogConsole and provides `run_safely`, a helper that executes
an engine call, catches the application's exception hierarchy, and
reports the outcome consistently -- so individual tabs don't each
reimplement try/except/log/messagebox boilerplate.
"""

from __future__ import annotations

from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from pdf_editor.core.exceptions import PDFEditorError
from pdf_editor.gui.widgets.log_console import LogConsole
from pdf_editor.utils.logger import get_logger

logger = get_logger("gui.tabs")


class BaseTab(ctk.CTkFrame):
    """Common scaffolding shared by every feature tab frame."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.log_console: LogConsole | None = None

    def build_log_console(self, parent, row: int, column: int = 0, columnspan: int = 1, **grid_kw):
        self.log_console = LogConsole(parent, height=110)
        self.log_console.grid(row=row, column=column, columnspan=columnspan, sticky="nsew", **grid_kw)
        return self.log_console

    def run_safely(
        self,
        action: Callable[[], object],
        *,
        success_message: str,
        busy_message: str = "Working...",
        on_success: Callable[[object], None] | None = None,
    ) -> None:
        """
        Execute `action()` with unified error handling.

        Intentionally synchronous: PDF operations here are local, fast
        file operations (typically well under a second to a few seconds
        even for large documents), so blocking the UI briefly keeps the
        code simple and avoids thread-safety concerns with Tk widgets.
        """
        if self.log_console:
            self.log_console.info(busy_message)
        self.update_idletasks()

        try:
            result = action()
        except (PDFEditorError, ValueError) as exc:
            logger.warning("Handled error: %s", exc)
            if self.log_console:
                self.log_console.error(str(exc))
            messagebox.showerror("Operation Failed", str(exc))
        except Exception as exc:  # unexpected: log full detail, show generic message
            logger.exception("Unexpected error during operation")
            if self.log_console:
                self.log_console.error(f"Unexpected error: {exc}")
            messagebox.showerror(
                "Unexpected Error",
                f"Something went wrong:\n{exc}\n\nSee the log file for details.",
            )
        else:
            if self.log_console:
                self.log_console.success(success_message)
            if on_success:
                on_success(result)
