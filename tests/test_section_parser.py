from backend.scraper.section_parser import SectionParser


def test_parse_simple_html():
    html = """
    <html><body>
    <main>
      <h1>Title</h1>
      <p>Hello world</p>
      <img src="https://example.com/img.jpg" alt="img" />
    </main>
    </body></html>
    """

    sections = SectionParser(html, "https://example.com").parse_sections()
    assert isinstance(sections, list)
    assert len(sections) >= 1
    assert any('Hello world' in s['content']['text'] for s in sections)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-q'])
