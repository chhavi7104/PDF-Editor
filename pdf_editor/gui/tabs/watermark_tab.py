"""Apply a text or image watermark across every page of a PDF."""

from __future__ import annotations

from tkinter import filedialog

import customtkinter as ctk

from pdf_editor.core.engine import PDFEngine
from pdf_editor.gui import theme
from pdf_editor.gui.tabs.base_tab import BaseTab

IMAGE_FILETYPES = [
    ("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp"),
    ("All files", "*.*"),
]


class WatermarkTab(BaseTab):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._source_file: str | None = None
        self._watermark_image: str | None = None

        ctk.CTkLabel(self, text="Watermark", font=theme.FONT_HEADER).grid(
            row=0, column=0, sticky="w", padx=theme.PAD_X, pady=(theme.PAD_Y, 0)
        )
        ctk.CTkLabel(
            self,
            text="Stamp a repeating text label or a semi-transparent image onto every page.",
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

        self.mode_var = ctk.StringVar(value="text")
        mode_row = ctk.CTkFrame(self, fg_color="transparent")
        mode_row.grid(row=3, column=0, sticky="ew", padx=theme.PAD_X, pady=4)
        ctk.CTkRadioButton(
            mode_row, text="Text watermark", variable=self.mode_var, value="text",
            command=self._toggle_mode,
        ).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(
            mode_row, text="Image watermark", variable=self.mode_var, value="image",
            command=self._toggle_mode,
        ).pack(side="left")

        # -- text options --
        self.text_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.text_frame.grid(row=4, column=0, sticky="ew", padx=theme.PAD_X, pady=4)
        ctk.CTkLabel(self.text_frame, text="Text:", font=theme.FONT_BODY).grid(row=0, column=0, sticky="w")
        self.text_entry = ctk.CTkEntry(self.text_frame, width=260, placeholder_text="CONFIDENTIAL")
        self.text_entry.grid(row=0, column=1, padx=8)
        ctk.CTkLabel(self.text_frame, text="Font size:", font=theme.FONT_BODY).grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.font_size_entry = ctk.CTkEntry(self.text_frame, width=80)
        self.font_size_entry.insert(0, "40")
        self.font_size_entry.grid(row=1, column=1, sticky="w", padx=8, pady=(6, 0))

        # -- image options --
        self.image_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.image_frame.grid(row=5, column=0, sticky="ew", padx=theme.PAD_X, pady=4)
        ctk.CTkButton(self.image_frame, text="Choose Watermark Image...", command=self._choose_image).pack(
            side="left"
        )
        self.image_label = ctk.CTkLabel(self.image_frame, text="No image selected", font=theme.FONT_BODY)
        self.image_label.pack(side="left", padx=10)
        self.image_frame.grid_remove()

        # -- shared opacity --
        opacity_row = ctk.CTkFrame(self, fg_color="transparent")
        opacity_row.grid(row=6, column=0, sticky="ew", padx=theme.PAD_X, pady=4)
        ctk.CTkLabel(opacity_row, text="Opacity:", font=theme.FONT_BODY).pack(side="left")
        self.opacity_slider = ctk.CTkSlider(opacity_row, from_=0.05, to=1.0, number_of_steps=19, width=200)
        self.opacity_slider.set(0.3)
        self.opacity_slider.pack(side="left", padx=8)

        ctk.CTkButton(self, text="Apply Watermark & Save As...", command=self._on_apply).grid(
            row=7, column=0, sticky="w", padx=theme.PAD_X, pady=theme.PAD_Y
        )

        self.build_log_console(self, row=8, padx=theme.PAD_X, pady=(0, theme.PAD_X))

    def _toggle_mode(self) -> None:
        if self.mode_var.get() == "text":
            self.text_frame.grid()
            self.image_frame.grid_remove()
        else:
            self.text_frame.grid_remove()
            self.image_frame.grid()

    def _choose_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        self._source_file = path
        self.file_label.configure(text=path.split("/")[-1].split("\\")[-1])

    def _choose_image(self) -> None:
        path = filedialog.askopenfilename(filetypes=IMAGE_FILETYPES)
        if not path:
            return
        self._watermark_image = path
        self.image_label.configure(text=path.split("/")[-1].split("\\")[-1])

    def _on_apply(self) -> None:
        if not self._source_file:
            self.log_console.warning("Choose a PDF file first.")
            return

        mode = self.mode_var.get()
        if mode == "text" and not self.text_entry.get().strip():
            self.log_console.warning("Enter watermark text.")
            return
        if mode == "image" and not self._watermark_image:
            self.log_console.warning("Choose a watermark image.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="watermarked.pdf",
        )
        if not output_path:
            return

        opacity = float(self.opacity_slider.get())

        def action():
            if mode == "text":
                try:
                    font_size = int(self.font_size_entry.get())
                except ValueError:
                    font_size = 40
                return PDFEngine.add_text_watermark(
                    self._source_file, output_path, self.text_entry.get(),
                    opacity=opacity, font_size=font_size,
                )
            else:
                return PDFEngine.add_image_watermark(
                    self._source_file, output_path, self._watermark_image, opacity=opacity,
                )

        self.run_safely(action, success_message=f"Watermark applied -> {output_path}")
