# Bionic EPUB

A local CLI that converts DRM-free EPUB books into Bionic Reading-style EPUBs for Kobo.

## Installation on Windows

Open the VS Code PowerShell terminal in this project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

If PowerShell blocks activation, run this once in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

Then activate the environment again.

## Development

```powershell
python -m pytest
```

The CLI will be available as `bionic-epub` after installation.

## Usage

Preview the transformation without touching an EPUB:

```powershell
bionic-epub preview "The quick brown fox"
```

Convert a DRM-free EPUB into a new file:

```powershell
bionic-epub convert book.epub -o book-bionic.epub
```

Adjust the visual strength or include headings when needed:

```powershell
bionic-epub convert book.epub -o book-bionic.epub --strength light
bionic-epub convert book.epub -o book-bionic.epub --process-headings
```

The input EPUB is not modified. The first version processes XHTML/HTML content
documents and preserves the rest of the EPUB archive.
