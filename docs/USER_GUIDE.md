# User Guide

## Launching the app

```bash
python main.py
```

or run the packaged executable (`dist/PDFEditor` / `PDFEditor.exe`) directly
— no Python installation needed for that version.

The window opens with one tab per feature along the top. Every tab has its
own status console at the bottom showing what happened (ℹ info, ✓ success,
⚠ warning, ✗ error).

## Merge

1. **Add Files** — pick two or more PDFs.
2. Select a file in the list and use **Up** / **Down** to set the order
   they'll appear in the merged output.
3. **Merge & Save As...** — choose where to save the result.

## Split

1. **Choose PDF...**
2. Pick a mode:
   - **One file per page** — every page becomes its own PDF.
   - **Custom ranges** — type ranges like `1-3,5,8-10`; each comma-separated
     group becomes one output file.
3. **Split & Choose Output Folder...**

## Rotate

1. **Choose PDF...**
2. Pick an angle (90° / 180° / 270°, clockwise).
3. Choose **All pages** or **Specific pages** (e.g. `1,3,5-7`).
4. **Rotate & Save As...**

## Delete & Reorder Pages

1. **Choose PDF...** — every page loads as a row, each with a checkbox.
2. **Uncheck** a page to delete it.
3. Click a row to select it, then use **Up** / **Down** to move it —
   this defines the page order in the output.
4. **Apply & Save As...**

## Extract Text

1. **Choose PDF...**
2. Leave **Pages** blank for the whole document, or type a range like
   `1-3,5`.
3. **Extract to Preview** to read it in the app, or **Extract & Save as
   .txt...** to save it to a file.

## Image ⇄ PDF

**Images → PDF** sub-tab:
1. **Add Files** — pick one or more images (PNG, JPG, BMP, TIFF, WEBP).
2. Reorder them with Up/Down if needed — each becomes one page, in order.
3. **Convert to PDF & Save As...**

**PDF → Images** sub-tab:
1. **Choose PDF...**
2. Pick an output **Format** (PNG/JPG) and **DPI** (higher = larger, sharper
   images).
3. **Convert to Images & Choose Folder...**

## Watermark

1. **Choose PDF...**
2. Pick **Text watermark** (type text, set font size) or **Image
   watermark** (choose an image file).
3. Adjust **Opacity**.
4. **Apply Watermark & Save As...**

## Password

**Add Password** sub-tab:
1. **Choose PDF...**
2. Enter and confirm a new password.
3. Choose whether printing/copying should remain allowed.
4. **Protect & Save As...** — the output is AES-256 encrypted.

**Remove Password** sub-tab:
1. **Choose PDF...** (an already-protected file)
2. Enter its current password.
3. **Unlock & Save As...**

## Preview

1. **Choose PDF...** — if the file is encrypted, you'll be prompted for the
   password.
2. Use **◀ Prev** / **Next ▶** to page through, and **Zoom -** / **Zoom +**
   to adjust size.

## Handling problems

- **Corrupted or invalid file** — the app shows an error message and does
  not crash; try a different file or re-export the original PDF.
- **Wrong password** — you'll be told the password was incorrect and asked
  to try again.
- **Invalid page range** — ranges are validated against the actual page
  count before anything is written; you'll get a specific message about
  which page number was out of bounds.

## Where are my files?

- Every "Save As..." dialog lets you choose the exact output location.
- If a chosen output filename already exists, the app automatically appends
  `(1)`, `(2)`, etc. rather than overwriting it.
- A full log of every operation (including full error tracebacks) is kept
  at `~/.pdf_editor/logs/pdf_editor.log` — that path is also shown at the
  bottom of the app window.
