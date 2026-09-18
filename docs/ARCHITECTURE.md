# Architecture

## Layered design

The application is split into three layers, each with a single
responsibility, so that any one of them could be replaced without
rewriting the others.

```
┌───────────────────────────────────────────────────────┐
│  GUI layer            pdf_editor/gui/                 │
│  - App (main window), one CTkFrame subclass per tab    │
│  - Depends on: core layer, utils layer                 │
├───────────────────────────────────────────────────────┤
│  Core layer            pdf_editor/core/                │
│  - PDFEngine: every PDF operation, as static methods    │
│  - Custom exception hierarchy                          │
│  - Depends on: utils layer, PyMuPDF, Pillow             │
├───────────────────────────────────────────────────────┤
│  Utils layer            pdf_editor/utils/               │
│  - Logging configuration                                │
│  - Filesystem / page-range parsing helpers               │
│  - Depends on: nothing app-specific                      │
└───────────────────────────────────────────────────────┘
```

The core layer has **no Tkinter import anywhere**. This was a deliberate
constraint during development, verified by grepping the module — it means
`PDFEngine` can be imported and exercised from a plain Python script, a
future CLI, or a test suite without ever creating a window. The
`tests/test_engine.py` suite does exactly this.

## `PDFEngine`

`PDFEngine` (in `pdf_editor/core/engine.py`) is a stateless collection of
`@staticmethod`s — there's no instance state to manage because every
operation is a pure "take input path(s) + parameters, produce output
path(s)" transformation. Each public method:

1. Opens the input file(s) via the private `_open()` helper, which
   centralizes file-not-found, corrupted-file, and encrypted-file handling
   so every other method gets that behavior for free.
2. Validates its own parameters (page ranges, angles, non-empty inputs)
   and raises a specific `PDFEditorError` subclass on failure.
3. Performs the PyMuPDF operation.
4. Saves to a de-duplicated output path (via `unique_path()`, which appends
   `(1)`, `(2)`, ... if the target already exists, so a rerun never
   silently overwrites a previous result).
5. Logs the outcome.

## Exception hierarchy

```
PDFEditorError
├── CorruptedPDFError     # file missing / not a valid PDF / unreadable
├── EncryptedPDFError     # PDF needs a password that wasn't given
├── InvalidPasswordError  # a password was given but is wrong
├── UnsupportedFileError  # wrong file type for the requested operation
├── PageRangeError        # a page number/range is out of bounds
└── EmptyInputError       # operation triggered with no input (e.g. 0 files)
```

The GUI layer only ever needs to catch `PDFEditorError` (see
`BaseTab.run_safely`) to handle every *known* failure mode uniformly; any
other exception is treated as a genuine bug, logged with a full traceback,
and shown as a generic (but still non-fatal) error.

## GUI composition

`gui/app.py` builds a `CTkTabview` and instantiates one tab class per
feature, each living in its own module under `gui/tabs/`. Every tab
subclasses `BaseTab`, which provides:

- `build_log_console()` — attaches a shared `LogConsole` widget.
- `run_safely()` — the single choke point through which every engine call
  is invoked, providing consistent error handling and status reporting.

Two reusable widgets live under `gui/widgets/`:

- `FileListWidget` — an ordered, multi-select file list with
  add/remove/move-up/move-down/clear controls, used by Merge and the
  Image→PDF converter.
- `LogConsole` — a color-coded, append-only status console used by every
  tab.

## Why PyMuPDF for everything

Merging, splitting, rotation, page deletion/reordering, text extraction,
rendering-to-image, watermarking, and encryption are all implemented on
top of a single library (PyMuPDF/`fitz`) rather than mixing several PDF
libraries. This was a conscious trade-off: it avoids subtly different
page-indexing conventions and object models across libraries, at the cost
of being tied to one dependency for the whole core layer. Pillow is used
only for genuinely image-side work (opening arbitrary image formats,
building multi-page PDFs from images).

## Testing strategy

- **Unit tests** (`tests/test_engine.py`) exercise `PDFEngine` directly,
  generating their own sample PDFs/images via PyMuPDF/Pillow so they need
  no fixture files and run anywhere.
- **GUI smoke tests** (not checked in, but used during development) drove
  each tab's real button-click handlers programmatically under a headless
  X server (Xvfb), confirming the full path from widget interaction →
  `PDFEngine` call → file output works end-to-end, including the
  corrupted-file error path.
