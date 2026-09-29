"""Command line entry point."""

from __future__ import annotations

from pathlib import Path
from io import StringIO
import shutil
import sys
import os
import tempfile
from collections import Counter

from rich import box

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

import typer

from .epub_io import EpubError, convert_epub, validate_epub
from .tokenizer import bold_prefix
from .batch import discover

class CommandHelp(typer.core.TyperGroup):
    def format_help(self, ctx, formatter) -> None:
        border = box.ROUNDED
        try:
            chr(0x256d).encode(sys.stdout.encoding or "utf-8")
        except UnicodeEncodeError:
            border = box.ASCII
        buffer = StringIO()
        console = Console(file=buffer, width=ctx.terminal_width or shutil.get_terminal_size().columns,
                          force_terminal=True,
                          color_system="standard", legacy_windows=False, safe_box=False)
        console.print(Text.assemble(("Usage: ", "bold"), "bionic-epub.exe ", ("[OPTIONS] COMMAND [ARGS]...", "cyan")))
        console.print()
        console.print(Panel(Text.assemble(("--help", "bold cyan"), "   Show this help and exit."), title="Options", title_align="left", box=border, border_style="dim"))
        commands = Table.grid(padding=(0, 2), expand=True)
        commands.add_column(ratio=1, overflow="fold")
        commands.add_column(ratio=1, overflow="fold")
        for template, description in [
            ("convert <file> -o <output>", "Convert an EPUB into a new EPUB."),
            ("batch-convert <paths> -o <dir>", "Convert EPUB files or folders."),
            ("batch-validate <paths>", "Validate EPUB files or folders."),
            ("validate <file>", "Check basic EPUB archive structure."),
            ('preview "<text>"', "Preview bold word prefixes."),
        ]:
            syntax = Text(template, style="cyan")
            syntax.highlight_regex(r"<[^>]+>", "magenta")
            commands.add_row(syntax, Text(description))
        console.print(Panel(commands, title="Commands", title_align="left", box=border, border_style="dim"))
        formatter.write(buffer.getvalue())


app = typer.Typer(cls=CommandHelp, add_completion=False, invoke_without_command=True)


@app.callback()
def main(ctx: typer.Context) -> None:
    """Show usage when launched without a command."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command(help=(
    'Convert an EPUB into a new file. Both INPUT_PATH and -o / --output are required.\n\n'
    'Example: bionic-epub.exe convert "book.epub" -o "book-bionic.epub"\n\n'
    'Use --overwrite only when you want to replace an existing output file.'
))
def convert(
    input_path: str = typer.Argument(..., help="Input DRM-free EPUB."),
    output_path: str = typer.Option(..., "--output", "-o", help="Required: output EPUB file path. Example: -o book-bionic.epub"),
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


def batch_summary(succeeded: int, failed: int):
    typer.echo(f"Summary: {succeeded} succeeded, {failed} failed")
    if failed:
        raise typer.Exit(1)


@app.command("batch-validate")
def batch_validate(
    inputs: list[str] = typer.Argument(..., help="One or more EPUB files or directories."),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Include subdirectories."),
):
    """Validate each EPUB; continue after errors and report a summary."""
    files, errors = discover(inputs, recursive)
    succeeded = 0
    for path, detail in errors:
        typer.echo(f"FAIL {path}: {detail}", err=True)
    failed = len(errors)
    for source in files:
        try:
            validate_epub(source)
            typer.echo(f"OK {source}")
            succeeded += 1
        except Exception as error:
            typer.echo(f"FAIL {source}: {error}", err=True)
            failed += 1
    batch_summary(succeeded, failed)


@app.command("batch-convert")
def batch_convert(
    inputs: list[str] = typer.Argument(..., help="One or more EPUB files or directories."),
    output: Path = typer.Option(..., "--output", "-o", help="Destination directory; files use <name>-bionic.epub."),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Include subdirectories; output directory is excluded from scans."),
    strength: str = typer.Option("standard", help="light, standard, or strong"),
    ratio: float | None = typer.Option(None, min=0.01, max=1.0),
    process_headings: bool = typer.Option(False),
    process_toc: bool = typer.Option(False),
    overwrite: bool = typer.Option(False, help="Replace existing output files, never input files."),
):
    """Convert each EPUB into the output folder; continue after individual failures."""
    if strength not in {"light", "standard", "strong"}:
        raise typer.BadParameter("strength must be light, standard, or strong")
    files, errors = discover(inputs, recursive, output)
    targets = [output / f"{source.stem}-bionic.epub" for source in files]
    counts = Counter(str(target.resolve()).casefold() for target in targets)
    sources = {str(source.resolve()).casefold() for source in files}
    for path, detail in errors:
        typer.echo(f"FAIL {path}: {detail}", err=True)
    succeeded, failed = 0, len(errors)
    for source, target in zip(files, targets):
        try:
            key = str(target.resolve()).casefold()
            if counts[key] > 1:
                raise EpubError("Multiple input files map to the same output name")
            if key in sources:
                raise EpubError("Output would replace an input file")
            if target.exists() and not overwrite:
                raise EpubError("Output already exists; use --overwrite to replace it")
            output.mkdir(parents=True, exist_ok=True)
            # Build beside the destination. A failed conversion leaves old output intact.
            with tempfile.TemporaryDirectory(prefix=".bionic-", dir=output) as temporary:
                staged = Path(temporary) / "result.epub"
                documents, words = convert_epub(source, staged, strength=strength, ratio=ratio,
                    process_headings=process_headings, process_toc=process_toc)
                if overwrite:
                    os.replace(staged, target)
                else:
                    # Windows rename refuses an existing destination.
                    if os.name == "nt":
                        os.rename(staged, target)
                    else:
                        os.link(staged, target)
            typer.echo(f"OK {source} -> {target} ({documents} documents, {words} words)")
            succeeded += 1
        except Exception as error:
            typer.echo(f"FAIL {source}: {error}", err=True)
            failed += 1
    batch_summary(succeeded, failed)


if __name__ == "__main__":
    app()
