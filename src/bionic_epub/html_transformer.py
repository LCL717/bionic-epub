"""Transform XHTML text nodes without disturbing their element structure."""

from __future__ import annotations

from dataclasses import dataclass

from lxml import etree

from .tokenizer import WORD_RE, prefix_length, should_skip

SKIP_TAGS = {"code", "pre", "script", "style", "strong", "b"}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


@dataclass(frozen=True)
class TransformResult:
    html: bytes
    words_changed: int


def _local_name(element: etree._Element) -> str:
    return etree.QName(element).localname.lower()


def _can_transform(element: etree._Element, process_headings: bool) -> bool:
    for candidate in (element, *element.iterancestors()):
        tag = _local_name(candidate)
        if tag in SKIP_TAGS:
            return False
        if not process_headings and tag in HEADING_TAGS:
            return False
    return True


def _parts(text: str, strength: str, ratio: float | None) -> tuple[list[tuple[str, str]], int]:
    parts: list[tuple[str, str]] = []
    changed = 0
    cursor = 0
    for match in WORD_RE.finditer(text):
        if match.start() > cursor:
            parts.append(("text", text[cursor : match.start()]))
        word = match.group()
        if should_skip(word):
            parts.append(("text", word))
        else:
            length = prefix_length(word, strength, ratio)
            parts.append(("strong", word[:length]))
            if length < len(word):
                parts.append(("text", word[length:]))
            changed += 1
        cursor = match.end()
    if cursor < len(text):
        parts.append(("text", text[cursor:]))
    return parts, changed


def _insert_parts(parent: etree._Element, index: int, parts: list[tuple[str, str]]) -> None:
    """Insert strong elements while storing ordinary text in text/tail fields."""
    pending_text = ""
    last = parent if index == -1 else parent[index]
    for kind, value in parts:
        if kind == "text":
            pending_text += value
            continue

        namespace = parent.nsmap.get(None)
        tag = f"{{{namespace}}}strong" if namespace else "strong"
        strong = etree.Element(tag)
        strong.text = value
        if last is parent:
            parent.text = pending_text
            parent.insert(0, strong)
        else:
            last.tail = pending_text
            parent.insert(parent.index(last) + 1, strong)
        pending_text = ""
        last = strong

    if last is parent:
        parent.text = pending_text
    else:
        last.tail = pending_text


def _replace_text_node(
    element: etree._Element,
    attribute: str,
    text: str,
    strength: str,
    ratio: float | None,
) -> int:
    parts, changed = _parts(text, strength, ratio)
    if not changed:
        return 0

    if attribute == "text":
        element.text = None
        _insert_parts(element, -1, parts)
    else:
        parent = element.getparent()
        if parent is None:
            return 0
        index = parent.index(element)
        element.tail = None
        _insert_parts(parent, index, parts)
    return changed


def transform_html(
    html: bytes,
    *,
    strength: str = "standard",
    ratio: float | None = None,
    process_headings: bool = False,
) -> TransformResult:
    """Bold word prefixes in an XHTML document and return serialized XHTML."""
    parser = etree.XMLParser(resolve_entities=False, remove_blank_text=False)
    root = etree.fromstring(html, parser)
    words_changed = 0

    text_nodes = []
    for element in root.iter():
        if _can_transform(element, process_headings) and element.text:
            text_nodes.append((element, "text", element.text))
        for child in element:
            if _can_transform(child, process_headings) and child.tail:
                text_nodes.append((child, "tail", child.tail))

    for element, attribute, text in text_nodes:
        words_changed += _replace_text_node(element, attribute, text, strength, ratio)

    return TransformResult(
        html=etree.tostring(root, encoding="UTF-8", xml_declaration=True),
        words_changed=words_changed,
    )
