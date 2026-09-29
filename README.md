# Bionic EPUB

## 1. Environment setup

**To run the portable EXE:** use Windows on the same architecture as the build. The current build is Windows x64. Python, pip, and the dependencies below do not need to be installed on the user's computer.

**To develop or build from source:** use Windows, Python, and an internet connection for dependency installation. VS Code is optional. Run the commands below in PowerShell from the project folder.

| Component | Project requirement | Version verified locally |
| --- | --- | --- |
| Windows | Windows for the EXE build; architecture follows Python | Build 26200, x64 |
| Python | 3.10 or newer | 3.11.9, 64-bit |
| pip | Included with Python; no explicit project minimum | 24.0 |
| setuptools | 68 or newer for package builds | Installed by pip in an isolated build environment; exact isolated version was not recorded |
| lxml | 5.0 or newer | 6.1.3 |
| Typer | 0.12 or newer | 0.27.2 |
| Rich | 13.8 or newer; terminal help panels | 15.0.0 |
| pytest | 8.0 or newer; tests only | 9.1.1 |
| PyInstaller | 6.16 or newer, below 7; EXE packaging only | 6.22.3 |
| pyinstaller-hooks-contrib | Installed automatically with PyInstaller | 2026.7 |

Version requirements come from `pyproject.toml`. Verified versions describe the local test environment, not a dependency lock: installation may resolve newer compatible versions. The virtual environment's existing setuptools version may differ from the isolated package-build version.

Install 64-bit Python and make sure `python` is available in your terminal. Then prepare the project environment:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test,build]"
.\.venv\Scripts\python.exe -m pytest -q
```

No virtual environment activation is required. These commands use its Python directly, avoiding PowerShell activation-script restrictions. You do not need to change the execution policy.

## 2. Build the portable EXE

Run one command from the project folder:

```powershell
.\build.cmd
```

The script creates `.venv` if missing, installs the project and test/build dependencies, runs the tests, and builds a single-file console EXE. It then checks the EXE's help, preview, EPUB conversion, validation, and protection against overwriting an existing output.

Generated files:

| File | Purpose |
| --- | --- |
| `dist/bionic-epub.exe` | Standalone command-line program |
| `dist/bionic-epub-windows-portable.zip` | EXE and README for sharing |
| `dist/SHA256SUMS.txt` | SHA-256 checksums for the EXE and ZIP |

Run `.\build.cmd` again after editing the source to rebuild. Close any running copy of the output EXE first. Build output, virtual environments, caches, and local ebooks are excluded from Git. The build does not upload or publish anything.

## 3. Usage

Extract the portable ZIP and open PowerShell in the extracted folder. This is a CLI: run it in a terminal rather than double-clicking it.

Show commands and options:

```powershell
.\bionic-epub.exe --help
.\bionic-epub.exe convert --help
```

Preview bold word prefixes without opening a book:

```powershell
.\bionic-epub.exe preview "The quick brown fox"
```

Convert a DRM-free EPUB into a new file:

```powershell
.\bionic-epub.exe convert "book.epub" -o "book-bionic.epub"
```

The original book is not modified. Keep quotation marks around paths containing spaces. Existing output files are rejected unless you explicitly pass `--overwrite`.

Optional conversion settings:

| Option | Effect |
| --- | --- |
| `--strength light` | Lighter emphasis |
| `--strength standard` | Default emphasis |
| `--strength strong` | Stronger emphasis |
| `--process-headings` | Also process headings |
| `--overwrite` | Allow replacement of an existing output file |

For example:

```powershell
.\bionic-epub.exe convert "book.epub" -o "book-bionic.epub" --strength light --process-headings
.\bionic-epub.exe validate "book-bionic.epub"
```

`validate` checks basic EPUB archive structure, not rendering on every device. Open the converted book in a reader, then transfer it to Kobo and check text, chapters, and navigation.

When working from the project folder, use `.\dist\bionic-epub.exe` for the packaged program, or `.\.venv\Scripts\bionic-epub.exe` to run the installed source version. The arguments are the same.

Batch conversion and validation accept multiple files, directories, or a mixture:

```powershell
.\bionic-epub.exe batch-convert "book1.epub" "book2.epub" -o "converted"
.\bionic-epub.exe batch-convert "books" -o "converted"
.\bionic-epub.exe batch-validate "book1.epub" "book2.epub"
.\bionic-epub.exe batch-validate "converted"
```

Add `--recursive` / `-r` to include subfolders. Folder scans select `.epub` files and deduplicate repeated paths. Conversion excludes its output folder from scans; use a different folder from the input. Each result is named `<original-name>-bionic.epub` in the output directory (subfolder structure is not preserved). Inputs with conflicting output names are reported as failures rather than overwritten.

Batch conversion supports the same `--strength`, `--ratio`, `--process-headings`, `--process-toc`, and `--overwrite` settings as single-file conversion. Failed conversions preserve existing outputs. Each file reports OK or FAIL; processing continues after individual failures. The final summary lists successes and failures. Any failure, missing input, or empty folder produces a nonzero exit code.
