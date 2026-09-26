"""Command line entry point."""

from __future__ import annotations

from pathlib import Path

import typer

from .epub_io import EpubError, convert_epub, validate_epub
from .tokenizer import bold_prefix

app = typer.Typer(help="Convert EPUB books into Bionic Reading-style EPUBs.")


@app.command()
def convert(
    input_path: str = typer.Argument(..., help="Input DRM-free EPUB."),
    output_path: str = typer.Option(..., "--output", "-o", help="Output EPUB."),
    strength: str = typer.Option("standard", help="light, standard, or strong"),
    ratio: float | None = typer.Option(None, min=0.01, max=1.0),
    process_headings: bool = typer.Option(False, help="Also process h1-h6 elements."),
    process_toc: bool = typer.Option(False, help="Also process navigation documents."),
    overwrite: bool = typer.Option(False, help="Replace an existing output file."),
) -> None:
    """Convert an EPUB into a Bionic Reading-style EPUB."""
    try:
        documents, words = convert_epub(
            Path(input_path),
            Path(output_path),
            strength=strength,
            ratio=ratio,
            process_headings=process_headings,
            process_toc=process_toc,
            overwrite=overwrite,
        )
    except EpubError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Converted {documents} document(s), {words} word(s): {output_path}")


@app.command()
def validate(path: str = typer.Argument(..., help="EPUB to validate.")) -> None:
    """Check basic EPUB archive structure."""
    try:
        validate_epub(Path(path))
    except EpubError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Valid EPUB: {path}")


@app.command()
def preview(
    text: str = typer.Argument(..., help="Text to preview."),
    strength: str = typer.Option("standard", help="light, standard, or strong"),
) -> None:
    """Preview the word-prefix transformation on plain text."""
    output: list[str] = []
    for token in text.split(" "):
        transformed, _ = bold_prefix(token, strength)
        output.append(transformed)
    typer.echo(" ".join(output))


if __name__ == "__main__":
    app()
