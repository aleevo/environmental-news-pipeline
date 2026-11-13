
from html.parser import HTMLParser
import re


class ArticleHTMLParser(HTMLParser):
    """
    Extract readable text from HTML while ignoring
    script and style content.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text_parts = []
        self.skip_content = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip_content += 1
            return

        if self.skip_content == 0:
            self.text_parts.append(" ")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip_content = max(0, self.skip_content - 1)
            return

        if self.skip_content == 0:
            self.text_parts.append(" ")

    def handle_data(self, data):
        if self.skip_content == 0:
            self.text_parts.append(data)

    def get_text(self):
        return "".join(self.text_parts)


def clean_article_text(text):
    """
    Clean HTML and normalize article text.

    Returns an empty string for missing input.
    """

    if not isinstance(text, str) or not text.strip():
        return ""

    parser = ArticleHTMLParser()
    parser.feed(text)
    parser.close()

    cleaned_text = parser.get_text()

    # Normalize whitespace
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)

    # Remove spaces before punctuation
    cleaned_text = re.sub(r"\s+([,.;:!?])", r"\1", cleaned_text)

    return cleaned_text.strip()
