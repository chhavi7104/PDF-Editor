#!/usr/bin/env python3
"""
PDF Editor -- application entry point.

Run with:  python main.py
Package into an executable with PyInstaller (see build.spec / README.md).
"""

from __future__ import annotations

import sys
import traceback
from tkinter import messagebox

from pdf_editor.utils.logger import get_logger

logger = get_logger("main")


def main() -> int:
    try:
        from pdf_editor.gui.app import App
    except Exception:
        # Most likely a missing dependency -- give the user an actionable
        # message instead of a bare traceback.
        traceback.print_exc()
        print(
            "\nFailed to start PDF Editor. Make sure dependencies are installed:\n"
            "    pip install -r requirements.txt\n"
        )
        return 1

    try:
        app = App()
        app.mainloop()
        return 0
    except Exception as exc:  # last-resort catch so the app never crashes silently
        logger.exception("Fatal error, application is exiting")
        try:
            messagebox.showerror(
                "Fatal Error",
                f"PDF Editor encountered an unexpected error and must close:\n\n{exc}",
            )
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
