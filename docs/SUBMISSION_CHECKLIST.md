# Submission Checklist

## ✅ Already done in this project

- [x] Complete source code (modular, OOP, `pdf_editor/` package)
- [x] 9 functional features implemented (5 required)
- [x] Logging (`~/.pdf_editor/logs/pdf_editor.log`) & exception handling
      throughout (`core/exceptions.py`, `BaseTab.run_safely`)
- [x] `requirements.txt`
- [x] `README.md`
- [x] Project documentation (`docs/ARCHITECTURE.md`, `docs/USER_GUIDE.md`)
- [x] Executable build config (`build.spec`) — verified to build and run
- [x] Unit tests (22 passing, `tests/test_engine.py`)
- [x] `.gitignore`, `LICENSE`

## 📤 Steps to finish the submission

### 1. Push to GitHub

```bash
cd pdf_editor_app
git init
git add .
git commit -m "Initial commit: PDF Editor with 9 features, tests, docs"
git branch -M main
git remote add origin https://github.com/<your-username>/pdf-editor.git
git push -u origin main
```

If you already built `dist/PDFEditor` locally, don't commit it — it's
excluded by `.gitignore` (`build/`, `dist/`). Instead, attach the built
executable to a **GitHub Release** for that repo (Releases → Draft a new
release → attach the binary), so the repo itself stays lightweight.

### 2. Build & attach the executable

```bash
pip install -r requirements.txt
pyinstaller build.spec
# -> dist/PDFEditor (Linux/Mac) or dist/PDFEditor.exe (Windows)
```

Build on each target OS you want to support (PyInstaller produces
platform-specific binaries — a Linux build won't run on Windows, etc.).

### 3. Post on LinkedIn

Use `docs/LINKEDIN_POST.md` as a starting draft — swap in your repo link
and a screenshot before posting.

### 4. Double-check the README

- [ ] Replace `<your-username>` in the clone URL with your actual GitHub
      username.
- [ ] Add real screenshots if you'd like (the current README uses an ASCII
      mockup as a placeholder).
