# 📄 PDF Editor

A clean, desktop **PDF Editor** built in Python with a CustomTkinter GUI and a
[PyMuPDF](https://pymupdf.readthedocs.io/)-powered engine. Built as a Week 2
project to demonstrate object-oriented design, modular architecture, and
robust error handling in a real, usable desktop application.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-22%20passing-brightgreen)

---

## ✨ Features

The app implements **nine** functional features (well beyond the 5 required):

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Merge PDFs** | Combine two or more PDFs, in a user-defined order |
| 2 | **Split PDFs** | Split into one file per page, or custom page ranges |
| 3 | **Rotate Pages** | Rotate all pages or a specific subset, 90/180/270° |
| 4 | **Delete & Reorder Pages** | Interactively drop pages and rearrange the rest |
| 5 | **Extract Text** | Pull plain text from all or specific pages, preview or save as `.txt` |
| 6 | **Image ⇄ PDF Conversion** | Combine images into a PDF, or render PDF pages out as images |
| 7 | **Watermarking** | Stamp a text or semi-transparent image watermark onto every page |
| 8 | **Password Protection** | Add AES-256 encryption, or remove an existing password |
| 9 | **Page Preview** | Page through a rendered preview of any PDF, including encrypted ones |

Plus: **graceful handling of corrupted, empty, or unreadable PDFs** everywhere
in the app — bad input never crashes the UI, it surfaces a clear message.

---

## 🖥️ Screenshots

> The app opens with a tabbed interface — one tab per feature — and a
> shared status console at the bottom of each tab reporting what happened.

```
┌─────────────────────────────────────────────────────────────┐
│  📄  PDF Editor                          Appearance: [System]│
├─────────────────────────────────────────────────────────────┤
│ [Merge] [Split] [Rotate] [Delete/Reorder] [Extract Text] ... │
│                                                               │
│   Merge PDFs                                                 │
│   Add two or more PDFs, arrange them with Up/Down, ...       │
│                                                               │
│   [Add Files] [Remove] [Up] [Down] [Clear]                   │
│   1. report_part1.pdf   (240 KB)                              │
│   2. report_part2.pdf   (180 KB)                              │
│                                                               │
│   [Merge & Save As...]                                       │
│   ✓ Merged 2 files -> /Users/you/Desktop/merged.pdf           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture

```
pdf_editor_app/
├── main.py                    # Application entry point
├── build.spec                 # PyInstaller build configuration
├── requirements.txt
├── pdf_editor/
│   ├── core/
│   │   ├── engine.py          # PDFEngine — all PDF operations (GUI-independent)
│   │   └── exceptions.py      # Application exception hierarchy
│   ├── gui/
│   │   ├── app.py             # Main window (App class)
│   │   ├── theme.py           # Shared visual constants
│   │   ├── tabs/               # One module per feature tab
│   │   │   ├── base_tab.py     # Shared error-handling scaffolding
│   │   │   ├── merge_tab.py
│   │   │   ├── split_tab.py
│   │   │   ├── rotate_tab.py
│   │   │   ├── pages_tab.py    # Delete + reorder
│   │   │   ├── extract_tab.py
│   │   │   ├── convert_tab.py  # Image <-> PDF
│   │   │   ├── watermark_tab.py
│   │   │   ├── security_tab.py # Password add/remove
│   │   │   └── preview_tab.py
│   │   └── widgets/             # Reusable widgets (file list, log console)
│   └── utils/
│       ├── logger.py          # Centralized logging
│       └── file_utils.py      # Filesystem / page-range helpers
├── tests/
│   └── test_engine.py         # 22 unit tests for the core engine
└── docs/
    ├── ARCHITECTURE.md
    └── USER_GUIDE.md
```

### Design principles

- **Separation of concerns.** `pdf_editor/core/engine.py` contains 100% of
  the PDF logic and has zero Tkinter imports — it can be unit tested, reused
  from a script, or driven from a different UI entirely.
- **One exception hierarchy.** All engine errors are translated into
  `PDFEditorError` subclasses (`CorruptedPDFError`, `EncryptedPDFError`,
  `InvalidPasswordError`, `PageRangeError`, …) so the GUI layer never has to
  know about PyMuPDF's own exception types.
- **One feature, one file.** Each tab is a self-contained `CTkFrame`
  subclass, making it easy to add a new feature without touching existing
  code — register the new tab class in `gui/app.py` and you're done.
- **Shared error handling.** Every tab inherits `BaseTab.run_safely()`,
  which wraps any engine call with unified try/except/log/messagebox
  behavior, so no tab has to reimplement error plumbing.
- **Logging everywhere.** Every operation logs to both the console and a
  rotating log file (`~/.pdf_editor/logs/pdf_editor.log`), so bug reports
  can include real diagnostic detail.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for more detail.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+

### Installation

```bash
git clone https://github.com/<your-username>/pdf-editor.git
cd pdf-editor
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

### Run the tests

```bash
python -m pytest tests/ -v
```

### Build a standalone executable

```bash
pyinstaller build.spec
```

The executable is produced at `dist/PDFEditor` (`dist/PDFEditor.exe` on
Windows). It is fully self-contained — no Python installation is required to
run it.

---

## 🧪 Testing & Quality

- **22 unit tests** cover every engine operation (`tests/test_engine.py`),
  including edge cases: corrupted files, invalid page ranges, wrong
  passwords, and permutation validation for reordering.
- Tests generate their own sample PDFs/images on the fly via PyMuPDF and
  Pillow, so the suite has **no external file dependencies** and runs
  anywhere.
- The GUI itself was smoke-tested end-to-end (headless, via Xvfb) by driving
  every tab's real button-click code paths against generated sample PDFs,
  including a corrupted-file case to confirm the app degrades gracefully
  instead of crashing.

```bash
$ python -m pytest tests/ -v
...
22 passed in 0.36s
```

---

## 🛡️ Error Handling

Every user-facing operation is wrapped in `BaseTab.run_safely()`, which:

1. Catches the application's own exception hierarchy (`PDFEditorError` and
   subclasses) and shows the user a clear, specific message (e.g. *"'x.pdf'
   is password-protected. Please supply the password."*).
2. Catches any unexpected exception as a last resort, logs the full
   traceback to the log file, and shows a generic — but non-crashing —
   error dialog.
3. Logs every outcome (info/warning/error) to both the in-app status
   console and the rotating log file.

This means a corrupted PDF, a wrong password, an out-of-range page number,
or an unsupported file type never crashes the application — the user always
gets actionable feedback.

---

## 📦 Tech Stack

- **Python 3.11+**
- **[PyMuPDF](https://pymupdf.readthedocs.io/)** — PDF parsing, editing, rendering, encryption
- **[Pillow](https://pillow.readthedocs.io/)** — image I/O for the Image ⇄ PDF conversion
- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)** — modern-looking Tkinter GUI
- **[PyInstaller](https://pyinstaller.org/)** — packaging into a standalone executable
- **pytest** — unit testing

---

## 🗺️ Roadmap / Possible Extensions

- Drag-and-drop file input
- Thumbnail grid view for page reordering (instead of a list)
- Batch processing (apply one operation across many files)
- PDF/A conversion and compression
- Digital signature support

---

## 📄 License

MIT — see [LICENSE](LICENSE).
