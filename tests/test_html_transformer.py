from lxml import etree

from bionic_epub.html_transformer import transform_html


XHTML = b'''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <body>
    <h1>Chapter Title</h1>
    <p>The quick <em>brown</em> fox.</p>
    <p><a href="https://example.com">Visit the website</a></p>
    <pre>do_not_change()</pre>
  </body>
</html>'''


def test_transform_preserves_structure_and_skips_headings_and_code():
    result = transform_html(XHTML)
    root = etree.fromstring(result.html)
    namespace = {"x": "http://www.w3.org/1999/xhtml"}

    assert result.words_changed == 7
    assert root.xpath("string(//x:h1)", namespaces=namespace) == "Chapter Title"
    assert "<strong>The</strong>" in result.html.decode()
    assert "<strong>br</strong>own" in result.html.decode()
    assert "do_not_change()" in result.html.decode()
    assert root.xpath("string(//x:a/@href)", namespaces=namespace) == "https://example.com"


def test_transform_can_process_headings():
    result = transform_html(XHTML, process_headings=True)
    assert "<strong>Cha</strong>pter" in result.html.decode()
