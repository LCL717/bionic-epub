from typer.testing import CliRunner

from bionic_epub.cli import app

runner = CliRunner()


def test_main_help_explains_required_output():
    for args in (["--help"], []):
        result = runner.invoke(app, args, terminal_width=120)
        assert result.exit_code == 0
        assert 'convert <file> -o <output>' in result.output
        assert 'validate <file>' in result.output
        assert 'preview "<text>"' in result.output
        assert 'Piranesi' not in result.output
        assert 'Quick start' not in result.output
        assert "Missing command" not in result.output


def test_convert_help_and_missing_output():
    result = runner.invoke(app, ["convert", "--help"], terminal_width=120)
    assert result.exit_code == 0
    assert "--output" in result.output
    assert "required" in result.output.lower()
    assert "book-bionic.epub" in result.output
    result = runner.invoke(app, ["convert", "book.epub"])
    assert result.exit_code != 0
    assert "--output" in result.output


def test_help_restores_colors_when_requested():
    result = runner.invoke(app, ["--help"], color=True, terminal_width=120)
    assert result.exit_code == 0
    assert "\x1b[" in result.output
    assert "Quick start" not in result.output
