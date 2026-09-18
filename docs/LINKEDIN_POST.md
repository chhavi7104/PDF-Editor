# LinkedIn Project Post (Draft)

Feel free to edit tone/emoji to match your own voice before posting.

---

🚀 **Week 2 Project: Built a full-featured PDF Editor in Python**

I just wrapped up a desktop PDF Editor built with Python, PyMuPDF, and
CustomTkinter — and pushed it up to GitHub.

Instead of the minimum 5 required features, I implemented **9**:

✅ Merge PDFs
✅ Split PDFs (per-page or custom ranges)
✅ Rotate pages (all or selected)
✅ Delete & reorder pages
✅ Extract text
✅ Image ⇄ PDF conversion
✅ Watermarking (text or image)
✅ Password protection (AES-256) + removal
✅ Page preview, including for password-protected PDFs

A few things I focused on beyond "make it work":

🏗️ **Modular architecture** — the PDF logic lives in a GUI-independent
`PDFEngine` class, so it's fully unit-testable on its own. 22 tests cover
every operation, including edge cases like corrupted files and wrong
passwords.

🛡️ **Real error handling** — a custom exception hierarchy
(`CorruptedPDFError`, `EncryptedPDFError`, `PageRangeError`, ...) means bad
input never crashes the app; the user always gets a clear message, and
everything is logged to a rotating log file for debugging.

📦 **Packaged as a standalone executable** via PyInstaller — no Python
install required to run it.

Repo (with full README, architecture docs, and a user guide):
👉 [link to your GitHub repo]

#Python #SoftwareDevelopment #OOP #OpenSource #PDF #DesktopApp

---

**Suggested image/carousel:** a screenshot of the app with the Merge tab
open, and a second slide showing the tab bar (Merge / Split / Rotate /
Delete-Reorder / Extract Text / Image⇄PDF / Watermark / Password / Preview)
to visually communicate feature breadth at a glance.
