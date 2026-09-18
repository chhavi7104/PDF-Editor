"""Add or remove password protection (AES-256 encryption) on a PDF."""

from __future__ import annotations

from tkinter import filedialog

import customtkinter as ctk

from pdf_editor.core.engine import PDFEngine
from pdf_editor.gui import theme
from pdf_editor.gui.tabs.base_tab import BaseTab


class SecurityTab(BaseTab):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=theme.PAD_X, pady=theme.PAD_Y)
        self.tabview.add("Add Password")
        self.tabview.add("Remove Password")

        self._build_add(self.tabview.tab("Add Password"))
        self._build_remove(self.tabview.tab("Remove Password"))

    # ------------------------------------------------------------------ #

    def _build_add(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        self._add_source: str | None = None

        ctk.CTkLabel(
            parent,
            text="Encrypt a PDF with AES-256 so it can only be opened with the password.",
            font=theme.FONT_BODY, text_color="gray",
        ).grid(row=0, column=0, sticky="w", pady=(4, 6))

        file_row = ctk.CTkFrame(parent, fg_color="transparent")
        file_row.grid(row=1, column=0, sticky="ew", pady=4)
        ctk.CTkButton(file_row, text="Choose PDF...", command=self._choose_add_source, width=140).pack(
            side="left"
        )
        self.add_file_label = ctk.CTkLabel(file_row, text="No file selected", font=theme.FONT_BODY)
        self.add_file_label.pack(side="left", padx=10)

        pw_row = ctk.CTkFrame(parent, fg_color="transparent")
        pw_row.grid(row=2, column=0, sticky="ew", pady=4)
        ctk.CTkLabel(pw_row, text="New password:", font=theme.FONT_BODY).pack(side="left")
        self.new_password_entry = ctk.CTkEntry(pw_row, width=220, show="•")
        self.new_password_entry.pack(side="left", padx=8)

        confirm_row = ctk.CTkFrame(parent, fg_color="transparent")
        confirm_row.grid(row=3, column=0, sticky="ew", pady=4)
        ctk.CTkLabel(confirm_row, text="Confirm password:", font=theme.FONT_BODY).pack(side="left")
        self.confirm_password_entry = ctk.CTkEntry(confirm_row, width=220, show="•")
        self.confirm_password_entry.pack(side="left", padx=8)

        perms_row = ctk.CTkFrame(parent, fg_color="transparent")
        perms_row.grid(row=4, column=0, sticky="ew", pady=4)
        self.allow_print_var = ctk.BooleanVar(value=True)
        self.allow_copy_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(perms_row, text="Allow printing", variable=self.allow_print_var).pack(
            side="left", padx=(0, 20)
        )
        ctk.CTkCheckBox(perms_row, text="Allow copying text", variable=self.allow_copy_var).pack(
            side="left"
        )

        ctk.CTkButton(parent, text="Protect & Save As...", command=self._on_add_password).grid(
            row=5, column=0, sticky="w", pady=8
        )

        self.add_log = self.build_log_console(parent, row=6)

    def _choose_add_source(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        self._add_source = path
        self.add_file_label.configure(text=path.split("/")[-1].split("\\")[-1])

    def _on_add_password(self) -> None:
        if not self._add_source:
            self.add_log.warning("Choose a PDF file first.")
            return
        pw, confirm = self.new_password_entry.get(), self.confirm_password_entry.get()
        if not pw:
            self.add_log.warning("Enter a password.")
            return
        if pw != confirm:
            self.add_log.warning("Passwords do not match.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="protected.pdf",
        )
        if not output_path:
            return

        def action():
            return PDFEngine.set_password(
                self._add_source, output_path, pw,
                allow_printing=self.allow_print_var.get(),
                allow_copy=self.allow_copy_var.get(),
            )

        self.log_console = self.add_log
        self.run_safely(action, success_message=f"Password protection applied -> {output_path}")

    # ------------------------------------------------------------------ #

    def _build_remove(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        self._remove_source: str | None = None

        ctk.CTkLabel(
            parent,
            text="Decrypt a password-protected PDF, producing an unlocked copy.",
            font=theme.FONT_BODY, text_color="gray",
        ).grid(row=0, column=0, sticky="w", pady=(4, 6))

        file_row = ctk.CTkFrame(parent, fg_color="transparent")
        file_row.grid(row=1, column=0, sticky="ew", pady=4)
        ctk.CTkButton(file_row, text="Choose PDF...", command=self._choose_remove_source, width=140).pack(
            side="left"
        )
        self.remove_file_label = ctk.CTkLabel(file_row, text="No file selected", font=theme.FONT_BODY)
        self.remove_file_label.pack(side="left", padx=10)

        pw_row = ctk.CTkFrame(parent, fg_color="transparent")
        pw_row.grid(row=2, column=0, sticky="ew", pady=4)
        ctk.CTkLabel(pw_row, text="Current password:", font=theme.FONT_BODY).pack(side="left")
        self.current_password_entry = ctk.CTkEntry(pw_row, width=220, show="•")
        self.current_password_entry.pack(side="left", padx=8)

        ctk.CTkButton(parent, text="Unlock & Save As...", command=self._on_remove_password).grid(
            row=3, column=0, sticky="w", pady=8
        )

        self.remove_log = self.build_log_console(parent, row=4)

    def _choose_remove_source(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        self._remove_source = path
        self.remove_file_label.configure(text=path.split("/")[-1].split("\\")[-1])

    def _on_remove_password(self) -> None:
        if not self._remove_source:
            self.remove_log.warning("Choose a PDF file first.")
            return
        pw = self.current_password_entry.get()
        if not pw:
            self.remove_log.warning("Enter the current password.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="unlocked.pdf",
        )
        if not output_path:
            return

        self.log_console = self.remove_log
        self.run_safely(
            lambda: PDFEngine.remove_password(self._remove_source, output_path, pw),
            success_message=f"Password removed -> {output_path}",
        )
