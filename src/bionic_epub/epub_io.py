"""EPUB archive reading, transformation, and writing helpers."""

from __future__ import annotations

import posixpath
import tempfile
import zipfile
from pathlib import Path

from lxml import etree

from .html_transformer import transform_html

CONTENT_TYPES = {"application/xhtml+xml", "text/html"}


class EpubError(ValueError):
	"""Raised when an input file is not a usable EPUB archive."""


def _read_xml(path: Path) -> etree._Element:
	parser = etree.XMLParser(resolve_entities=False, remove_blank_text=False)
	try:
		return etree.parse(str(path), parser).getroot()
	except (etree.XMLSyntaxError, OSError) as error:
		raise EpubError(f"Could not parse EPUB XML: {path.name}") from error


def _content_documents(root: Path, process_toc: bool) -> list[Path]:
	container = _read_xml(root / "META-INF" / "container.xml")
	rootfile = container.find(".//{*}rootfile")
	if rootfile is None or not rootfile.get("full-path"):
		raise EpubError("EPUB container.xml does not define an OPF file")

	opf_relative = rootfile.get("full-path")
	opf_path = root / Path(opf_relative)
	opf = _read_xml(opf_path)
	opf_dir = posixpath.dirname(opf_relative)
	documents: list[Path] = []

	for item in opf.findall(".//{*}manifest/{*}item"):
		media_type = item.get("media-type", "")
		properties = set((item.get("properties") or "").split())
		if media_type not in CONTENT_TYPES:
			continue
		if not process_toc and ("nav" in properties or item.get("id") == "ncx"):
			continue
		href = item.get("href")
		if href:
			documents.append(root / Path(posixpath.normpath(posixpath.join(opf_dir, href))))
	return documents


def validate_epub(path: Path) -> None:
	"""Perform inexpensive structural checks on an EPUB archive."""
	if not path.is_file():
		raise EpubError(f"Input file does not exist: {path}")
	try:
		with zipfile.ZipFile(path) as archive:
			names = archive.namelist()
			if not names or names[0] != "mimetype":
				raise EpubError("EPUB mimetype must be the first archive entry")
			info = archive.getinfo("mimetype")
			if info.compress_type != zipfile.ZIP_STORED:
				raise EpubError("EPUB mimetype must be stored without compression")
			if archive.read("mimetype") != b"application/epub+zip":
				raise EpubError("Invalid EPUB mimetype content")
			if "META-INF/container.xml" not in names:
				raise EpubError("EPUB is missing META-INF/container.xml")
			for name in names:
				normalized = posixpath.normpath(name)
				if name.startswith("/") or normalized == ".." or normalized.startswith("../"):
					raise EpubError(f"Unsafe path in EPUB archive: {name}")
	except zipfile.BadZipFile as error:
		raise EpubError(f"Invalid ZIP archive: {path}") from error


def _write_epub(source: Path, output: Path) -> None:
	output.parent.mkdir(parents=True, exist_ok=True)
	if output.exists():
		raise EpubError(f"Output already exists: {output}; use --overwrite to replace it")

	with zipfile.ZipFile(output, "w") as archive:
		archive.write(source / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
		for path in sorted(source.rglob("*")):
			if not path.is_file() or path.name == "mimetype":
				continue
			archive.write(path, path.relative_to(source).as_posix(), compress_type=zipfile.ZIP_DEFLATED)


def convert_epub(
	input_path: Path,
	output_path: Path,
	*,
	strength: str = "standard",
	ratio: float | None = None,
	process_headings: bool = False,
	process_toc: bool = False,
	overwrite: bool = False,
) -> tuple[int, int]:
	"""Convert EPUB content documents and return (documents, words)."""
	validate_epub(input_path)
	if output_path.exists() and not overwrite:
		raise EpubError(f"Output already exists: {output_path}; use --overwrite to replace it")
	if input_path.resolve() == output_path.resolve():
		raise EpubError("Input and output paths must be different")
	if overwrite and output_path.exists():
		output_path.unlink()

	with tempfile.TemporaryDirectory(prefix="bionic-epub-") as temporary:
		working = Path(temporary)
		with zipfile.ZipFile(input_path) as archive:
			archive.extractall(working)
		documents = _content_documents(working, process_toc)
		words_changed = 0
		for document in documents:
			transformed = transform_html(
				document.read_bytes(),
				strength=strength,
				ratio=ratio,
				process_headings=process_headings,
			)
			document.write_bytes(transformed.html)
			words_changed += transformed.words_changed
		_write_epub(working, output_path)

	validate_epub(output_path)
	return len(documents), words_changed
