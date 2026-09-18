"""Convert one or more images into a PDF, or render a PDF's pages out as images."""

from __future__ import annotations

from tkinter import filedialog

import customtkinter as ctk

from pdf_editor.core.engine import PDFEngine
from pdf_editor.gui import theme
from pdf_editor.gui.tabs.base_tab import BaseTab
from pdf_editor.gui.widgets.file_list import FileListWidget

IMAGE_FILETYPES = [
    ("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp"),
    ("All files", "*.*"),
]


class ConvertTab(BaseTab):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=theme.PAD_X, pady=theme.PAD_Y)
        self.tabview.add("Images → PDF")
        self.tabview.add("PDF → Images")

        self._build_images_to_pdf(self.tabview.tab("Images → PDF"))
        self._build_pdf_to_images(self.tabview.tab("PDF → Images"))

    # ------------------------------------------------------------------ #
    # Images -> PDF
    # ------------------------------------------------------------------ #

    def _build_images_to_pdf(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            parent,
            text="Combine one or more images (in order) into a single PDF, one page each.",
            font=theme.FONT_BODY,
            text_color="gray",
        ).grid(row=0, column=0, sticky="w", pady=(4, 6))

        self.image_list = FileListWidget(parent, filetypes=IMAGE_FILETYPES)
        self.image_list.grid(row=1, column=0, sticky="nsew")

        ctk.CTkButton(
            parent, text="Convert to PDF & Save As...", command=self._on_images_to_pdf
        ).grid(row=2, column=0, sticky="w", pady=8)

        self.i2p_log = self.build_log_console(parent, row=3)

    def _on_images_to_pdf(self) -> None:
        images = self.image_list.files()
        if not images:
            self.i2p_log.warning("Add at least one image.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="images.pdf",
        )
        if not output_path:
            return

        self.run_safely(
            lambda: PDFEngine.images_to_pdf(images, output_path),
            success_message=f"Created PDF from {len(images)} image(s) -> {output_path}",
        )

    # ------------------------------------------------------------------ #
    # PDF -> Images
    # ------------------------------------------------------------------ #

    def _build_pdf_to_images(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        self._pdf_source: str | None = None

        ctk.CTkLabel(
            parent,
            text="Render every page of a PDF out as separate raster images.",
            font=theme.FONT_BODY,
            text_color="gray",
        ).grid(row=0, column=0, sticky="w", pady=(4, 6))

        file_row = ctk.CTkFrame(parent, fg_color="transparent")
        file_row.grid(row=1, column=0, sticky="ew", pady=4)
        ctk.CTkButton(file_row, text="Choose PDF...", command=self._choose_pdf, width=140).pack(
            side="left"
        )
        self.pdf_file_label = ctk.CTkLabel(file_row, text="No file selected", font=theme.FONT_BODY)
        self.pdf_file_label.pack(side="left", padx=10)

        options_row = ctk.CTkFrame(parent, fg_color="transparent")
        options_row.grid(row=2, column=0, sticky="ew", pady=4)
        ctk.CTkLabel(options_row, text="Format:", font=theme.FONT_BODY).pack(side="left")
        self.format_var = ctk.StringVar(value="png")
        ctk.CTkOptionMenu(options_row, values=["png", "jpg"], variable=self.format_var, width=80).pack(
            side="left", padx=(6, 20)
        )
        ctk.CTkLabel(options_row, text="DPI:", font=theme.FONT_BODY).pack(side="left")
        self.dpi_var = ctk.StringVar(value="150")
        ctk.CTkOptionMenu(
            options_row, values=["72", "150", "300", "600"], variable=self.dpi_var, width=80
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            parent, text="Convert to Images & Choose Folder...", command=self._on_pdf_to_images
        ).grid(row=3, column=0, sticky="w", pady=8)

        self.p2i_log = self.build_log_console(parent, row=4)

    def _choose_pdf(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        self._pdf_source = path
        self.pdf_file_label.configure(text=path.split("/")[-1].split("\\")[-1])

    def _on_pdf_to_images(self) -> None:
        if not self._pdf_source:
            self.p2i_log.warning("Choose a PDF file first.")
            return

        out_dir = filedialog.askdirectory(title="Choose output folder")
        if not out_dir:
            return

        fmt = self.format_var.get()
        dpi = int(self.dpi_var.get())

        def action():
            return PDFEngine.pdf_to_images(self._pdf_source, out_dir, dpi=dpi, image_format=fmt)

        self.run_safely(
            action,
            success_message="Conversion complete.",
            on_success=lambda outputs: self.p2i_log.info(f"Created {len(outputs)} image(s) in {out_dir}"),
        )

    def run_safely(self, action, *, success_message, on_success=None):
        # Route errors to whichever sub-tab's console is active so feedback
        # appears in the right place regardless of which inner tab is open.
        active_log = self.i2p_log if self.tabview.get() == "Images → PDF" else self.p2i_log
        self.log_console = active_log
        super().run_safely(action, success_message=success_message, on_success=on_success)
