import zipfile
from pathlib import Path

from bionic_epub.epub_io import convert_epub, validate_epub


def _create_epub(path: Path) -> None:
    files = {
        "mimetype": b"application/epub+zip",
        "META-INF/container.xml": b'''<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>''',
        "OEBPS/content.opf": b'''<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <manifest><item id="chapter" href="chapter.xhtml" media-type="application/xhtml+xml"/></manifest>
  <spine><itemref idref="chapter"/></spine>
</package>''',
        "OEBPS/chapter.xhtml": b'''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body><p>The quick brown fox.</p></body></html>''',
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", files["mimetype"], compress_type=zipfile.ZIP_STORED)
        for name, content in files.items():
            if name != "mimetype":
                archive.writestr(name, content, compress_type=zipfile.ZIP_DEFLATED)


def test_convert_epub_preserves_archive_and_transforms_chapter(tmp_path: Path):
    source = tmp_path / "book.epub"
    output = tmp_path / "book-bionic.epub"
    _create_epub(source)

    documents, words = convert_epub(source, output)

    assert (documents, words) == (1, 4)
    validate_epub(output)
    with zipfile.ZipFile(output) as archive:
        assert archive.namelist()[0] == "mimetype"
        assert b"<strong>The</strong>" in archive.read("OEBPS/chapter.xhtml")
    assert source.exists()