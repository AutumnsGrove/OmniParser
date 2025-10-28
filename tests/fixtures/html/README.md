# HTML Test Fixtures

Test HTML files for validating OmniParser HTML parser functionality.

## Fixtures

### simple_article.html
- **Purpose:** Basic HTML structure testing
- **Features:** Standard meta tags, h1-h2 headings, paragraphs, lists, links
- **Expected Metadata:**
  - Title: "Simple Article Example"
  - Author: "Jane Doe"
  - Description: "A simple article for testing HTML parsing"
  - Language: "en"
  - Tags: ["testing", "html", "parser"]
- **Expected Chapters:** 4 (main title + 3 h2 sections)

### opengraph_article.html
- **Purpose:** OpenGraph and Dublin Core metadata testing
- **Features:** og:* properties, DC.* meta tags, multiple article tags, publication date
- **Expected Metadata:**
  - Title: "Advanced HTML Article" (from og:title, not DC.title or title tag)
  - Author: "John Smith" (from og:article:author, not DC.creator)
  - Description: from og:description
  - Tags: ["html", "metadata", "testing"] (from og:article:tag)
  - Publication Date: 2024-01-15T10:30:00Z
  - Publisher: "Test Publisher" (from DC.publisher)
- **Expected Chapters:** 5 (h1 + 4 h2 sections)

### complex_structure.html
- **Purpose:** Complex HTML elements testing
- **Features:** Tables, blockquotes, code blocks, nested headings (h1-h4), images, horizontal rules
- **Expected Metadata:**
  - Title: "Complex Document Structure"
  - Author: "Alice Johnson"
  - Language: "fr"
- **Expected Chapters:** Depends on max_chapter_level setting
  - Level 1-2: 7 chapters (h1 + 6 h2)
  - Level 1-3: 8 chapters (+ 1 h3)
  - Level 1-4: 9 chapters (+ 1 h4)

### no_headings.html
- **Purpose:** Edge case - document without headings
- **Features:** Plain paragraphs, no heading tags
- **Expected Metadata:**
  - Title: "Document Without Headings"
  - Description: "Testing documents without heading structure"
- **Expected Chapters:** 1 (auto-generated "Full Document")

### minimal.html
- **Purpose:** Minimal valid HTML
- **Features:** Single paragraph, minimal structure
- **Expected Metadata:**
  - Title: "Minimal HTML"
  - All other fields: None
- **Expected Chapters:** 1 (no headings)

## Usage

```python
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "html"

def test_simple_article():
    html_path = FIXTURES_DIR / "simple_article.html"
    parser = HTMLParser()
    doc = parser.parse(html_path)

    assert doc.metadata.title == "Simple Article Example"
    assert doc.metadata.author == "Jane Doe"
    assert len(doc.chapters) == 4
```

## Provenance

All HTML fixtures are original creations for OmniParser testing purposes.
No external content is included. All examples are MIT licensed.
