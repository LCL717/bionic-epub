"""Command line entry point."""

from __future__ import annotations

from pathlib import Path
from io import StringIO
import shutil
import sys

from rich import box

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

import typer

from .epub_io import EpubError, convert_epub, validate_epub
from .tokenizer import bold_prefix

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


if __name__ == "__main__":
    app()
