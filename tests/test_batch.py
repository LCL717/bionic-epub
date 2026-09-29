from pathlib import Path
from typer.testing import CliRunner
from bionic_epub.cli import app
from test_epub_io import _create_epub

runner = CliRunner()


def test_batch_continues_after_bad_book_and_deduplicates(tmp_path):
    good = tmp_path / "good.epub"
    bad = tmp_path / "bad.epub"
    _create_epub(good)
    before = good.read_bytes()
    bad.write_text("invalid")
    out = tmp_path / "output"
    result = runner.invoke(app, ["batch-convert", str(tmp_path), str(good), "-o", str(out)])
    assert result.exit_code == 1
    assert "1 succeeded, 1 failed" in result.output
    assert (out / "good-bionic.epub").exists()
    assert good.read_bytes() == before
    result = runner.invoke(app, ["batch-validate", str(bad), str(out)])
    assert result.exit_code == 1
    assert "1 succeeded, 1 failed" in result.output


def test_recursive_scan_excludes_output_and_handles_collisions(tmp_path):
    for folder in ["a", "b"]:
        (tmp_path / folder).mkdir()
        _create_epub(tmp_path / folder / "same.epub")
    out = tmp_path / "out"
    out.mkdir()
    _create_epub(out / "old.epub")
    result = runner.invoke(app, ["batch-convert", str(tmp_path), "-r", "-o", str(out), "--overwrite"])
    assert result.exit_code == 1
    assert "0 succeeded, 2 failed" in result.output
    assert list(out.iterdir()) == [out / "old.epub"]


def test_existing_output_and_failed_overwrite_are_safe(tmp_path):
    source = tmp_path / "book.epub"
    _create_epub(source)
    out = tmp_path / "out"
    args = ["batch-convert", str(source), "-o", str(out)]
    assert runner.invoke(app, args).exit_code == 0
    target = out / "book-bionic.epub"
    before = target.read_bytes()
    assert runner.invoke(app, args).exit_code == 1
    source.write_text("broken")
    assert runner.invoke(app, args + ["--overwrite"]).exit_code == 1
    assert target.read_bytes() == before


def test_empty_directory_and_input_output_alias(tmp_path):
    assert runner.invoke(app, ["batch-validate", str(tmp_path)]).exit_code == 1
    _create_epub(tmp_path / "book.epub")
    result = runner.invoke(app, ["batch-convert", str(tmp_path), "-o", str(tmp_path)])
    assert result.exit_code == 1
    assert not (tmp_path / "book-bionic.epub").exists()
