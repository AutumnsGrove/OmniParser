"""
Markdown parser implementation with YAML frontmatter support.

This module provides the MarkdownParser class for parsing Markdown files and
converting them to OmniParser's universal Document format. It includes YAML
frontmatter extraction, markdown normalization, heading-based chapter detection,
and image reference extraction.

Classes:
    MarkdownParser: Parser for Markdown files with optional YAML frontmatter.
"""

import logging
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml  # type: ignore[import-untyped]

from ..base.base_parser import BaseParser
from ..exceptions import FileReadError, ParsingError, ValidationError
from ..models import Chapter, Document, ImageReference, Metadata, ProcessingInfo
from ..processors.chapter_detector import detect_chapters

logger = logging.getLogger(__name__)


class MarkdownParser(BaseParser):
    """Parser for Markdown files with optional YAML frontmatter.

    Features:
    - YAML frontmatter extraction and parsing
    - Heading-based chapter detection (uses chapter_detector)
    - Markdown normalization (standardize heading styles)
    - Image reference extraction
    - Metadata from frontmatter

    Options:
        extract_frontmatter (bool): Extract YAML frontmatter (default: True)
        normalize_headings (bool): Standardize heading format (default: True)
        detect_chapters (bool): Use chapter_detector (default: True)
        clean_text (bool): Apply text cleaning (default: False)
        min_chapter_level (int): Minimum heading level for chapters (default: 1)
        max_chapter_level (int): Maximum heading level for chapters (default: 2)

    Example:
        >>> parser = MarkdownParser({'extract_frontmatter': True})
        >>> doc = parser.parse(Path("README.md"))
        >>> print(doc.metadata.title)
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize Markdown parser with options.

        Args:
            options: Parser configuration dictionary.
        """
        super().__init__(options)

        # Set default options
        self.options.setdefault("extract_frontmatter", True)
        self.options.setdefault("normalize_headings", True)
        self.options.setdefault("detect_chapters", True)
        self.options.setdefault("clean_text", False)
        self.options.setdefault("min_chapter_level", 1)
        self.options.setdefault("max_chapter_level", 2)

        # Initialize tracking
        self._warnings: List[str] = []
        self._start_time: Optional[float] = None

    def supports_format(self, file_path: Union[Path, str]) -> bool:
        """Check if file is Markdown.

        Args:
            file_path: Path to check.

        Returns:
            True if file has .md or .markdown extension, False otherwise.
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        return file_path.suffix.lower() in [".md", ".markdown"]

    def parse(self, file_path: Union[Path, str]) -> Document:
        """Parse Markdown file and return Document object.

        Process:
        1. Read file with UTF-8 encoding
        2. Extract frontmatter if present
        3. Parse frontmatter YAML to Metadata
        4. Get markdown content (after frontmatter)
        5. Normalize markdown if enabled
        6. Use chapter_detector to detect chapters
        7. Extract image references
        8. Build and return Document

        Args:
            file_path: Path to Markdown file.

        Returns:
            Document object with parsed content, chapters, images, and metadata.

        Raises:
            FileReadError: If file cannot be read.
            ParsingError: If parsing fails.
            ValidationError: If file validation fails.
        """
        # Convert string to Path if needed
        if isinstance(file_path, str):
            file_path = Path(file_path)

        self._start_time = time.time()
        self._warnings = []

        try:
            # Step 1: Validate markdown file
            self._validate_markdown(file_path)

            # Step 2: Read file content
            logger.info(f"Reading Markdown file: {file_path}")
            text = self._read_file(file_path)

            # Step 3: Extract frontmatter if enabled
            frontmatter_dict: Optional[Dict[str, Any]] = None
            content = text

            if self.options.get("extract_frontmatter"):
                logger.info("Extracting YAML frontmatter")
                frontmatter_dict, content = self._extract_frontmatter(text)
                if frontmatter_dict:
                    logger.info(
                        f"Found frontmatter with {len(frontmatter_dict)} fields"
                    )

            # Step 4: Create metadata from frontmatter
            if frontmatter_dict:
                metadata = self._frontmatter_to_metadata(frontmatter_dict, file_path)
            else:
                metadata = self._create_default_metadata(file_path)

            # Step 5: Normalize markdown if enabled
            if self.options.get("normalize_headings"):
                logger.info("Normalizing markdown headings")
                content = self._normalize_markdown(content)

            # Step 6: Detect chapters using chapter_detector
            chapters: List[Chapter] = []
            if self.options.get("detect_chapters"):
                logger.info("Detecting chapters from headings")
                min_level = self.options.get("min_chapter_level", 1)
                max_level = self.options.get("max_chapter_level", 2)
                chapters = detect_chapters(
                    content, min_level=min_level, max_level=max_level
                )
                logger.info(f"Detected {len(chapters)} chapters")

            # Step 7: Extract image references
            logger.info("Extracting image references")
            images = self._extract_image_references(content)
            logger.info(f"Found {len(images)} image references")

            # Step 8: Apply text cleaning if enabled
            if self.options.get("clean_text"):
                logger.info("Cleaning text")
                content = self.clean_text(content)
                for chapter in chapters:
                    chapter.content = self.clean_text(chapter.content)

            # Step 9: Calculate statistics
            word_count = self._count_words(content)
            reading_time = self._estimate_reading_time(word_count)

            # Step 10: Create processing info
            processing_time = time.time() - self._start_time
            processing_info = ProcessingInfo(
                parser_used="MarkdownParser",
                parser_version="1.0.0",
                processing_time=processing_time,
                timestamp=datetime.now(),
                warnings=self._warnings,
                options_used=self.options.copy(),
            )

            # Step 11: Create and return Document
            document = Document(
                document_id=str(uuid.uuid4()),
                content=content,
                chapters=chapters,
                images=images,
                metadata=metadata,
                processing_info=processing_info,
                word_count=word_count,
                estimated_reading_time=reading_time,
            )

            logger.info(
                f"Markdown parsing complete: {word_count} words, "
                f"{len(chapters)} chapters, {len(images)} images"
            )
            return document

        except (FileReadError, ValidationError):
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Markdown parsing failed: {e}")
            raise ParsingError(
                f"Failed to parse Markdown file: {e}",
                parser="MarkdownParser",
                original_error=e,
            )

    def _validate_markdown(self, file_path: Path) -> None:
        """Validate Markdown file before parsing.

        Checks:
        - File exists
        - File is readable
        - File has .md or .markdown extension
        - File size is reasonable

        Args:
            file_path: Path to Markdown file.

        Raises:
            FileReadError: If file doesn't exist or isn't readable.
            ValidationError: If file validation fails.
        """
        # Check file exists
        if not file_path.exists():
            raise FileReadError(f"File not found: {file_path}")

        # Check file is readable
        if not file_path.is_file():
            raise FileReadError(f"Not a file: {file_path}")

        # Check extension
        if not self.supports_format(file_path):
            raise ValidationError(f"Not a Markdown file: {file_path}")

        # Check file size
        file_size = file_path.stat().st_size
        if file_size == 0:
            raise ValidationError(f"Empty file: {file_path}")

        # Warn if file is very large (>50MB)
        if file_size > 50 * 1024 * 1024:
            logger.warning(f"Large Markdown file ({file_size / 1024 / 1024:.1f} MB)")
            self._warnings.append(f"Large file size: {file_size / 1024 / 1024:.1f} MB")

    def _read_file(self, file_path: Path) -> str:
        """Read markdown file with UTF-8 encoding.

        Args:
            file_path: Path to Markdown file.

        Returns:
            File content as string.

        Raises:
            FileReadError: If file cannot be read.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with latin-1 encoding as fallback
            logger.warning("UTF-8 decode failed, trying latin-1 encoding")
            self._warnings.append("Used latin-1 encoding (UTF-8 decode failed)")
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    return f.read()
            except Exception as e:
                raise FileReadError(f"Failed to read file: {e}")
        except Exception as e:
            raise FileReadError(f"Failed to read file: {e}")

    def _extract_frontmatter(self, text: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """Extract YAML frontmatter if present.

        Format:
        ---
        title: Document Title
        author: Author Name
        date: 2025-01-15
        tags: [python, parsing]
        ---

        Rest of markdown...

        Args:
            text: Full markdown text.

        Returns:
            Tuple of (frontmatter_dict, content_without_frontmatter).
        """
        # Pattern matches YAML frontmatter at start of document
        # Must start with --- and end with ---
        pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
        match = pattern.match(text)

        if not match:
            # No frontmatter found
            return None, text

        try:
            # Extract YAML content
            yaml_content = match.group(1)

            # Parse YAML
            frontmatter = yaml.safe_load(yaml_content)

            # Get content after frontmatter
            content = text[match.end() :]

            # Validate frontmatter is a dict
            if not isinstance(frontmatter, dict):
                logger.warning("Frontmatter is not a dictionary, ignoring")
                self._warnings.append("Invalid frontmatter format (not a dictionary)")
                return None, text

            return frontmatter, content

        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse YAML frontmatter: {e}")
            self._warnings.append(f"YAML parsing failed: {e}")
            return None, text

    def _frontmatter_to_metadata(
        self, frontmatter: Dict[str, Any], file_path: Path
    ) -> Metadata:
        """Convert frontmatter to Metadata object.

        Common frontmatter fields:
        - title
        - author / authors
        - date
        - tags / keywords
        - description / summary
        - language

        Args:
            frontmatter: Parsed YAML dict.
            file_path: Source file path.

        Returns:
            Metadata object.
        """
        # Extract title
        title = frontmatter.get("title")

        # Extract author(s)
        author = None
        authors = None

        if "authors" in frontmatter:
            authors_value = frontmatter["authors"]
            if isinstance(authors_value, list):
                authors = [str(a) for a in authors_value]
                author = authors[0] if authors else None
            else:
                author = str(authors_value)
                authors = [author]
        elif "author" in frontmatter:
            author = str(frontmatter["author"])
            authors = [author]

        # Extract date
        publication_date: Optional[datetime] = None
        if "date" in frontmatter:
            date_value = frontmatter["date"]
            if isinstance(date_value, datetime):
                publication_date = date_value
            elif isinstance(date_value, str):
                # Try to parse date string
                date_formats = [
                    "%Y-%m-%d",  # 2025-01-15
                    "%Y/%m/%d",  # 2025/01/15
                    "%Y-%m-%dT%H:%M:%S",  # 2025-01-15T10:30:00
                    "%Y-%m-%dT%H:%M:%SZ",  # 2025-01-15T10:30:00Z
                    "%Y",  # 2025
                    "%Y-%m",  # 2025-01
                ]
                for fmt in date_formats:
                    try:
                        publication_date = datetime.strptime(date_value, fmt)
                        break
                    except ValueError:
                        continue
                if publication_date is None:
                    logger.warning(f"Could not parse date: {date_value}")
                    self._warnings.append(f"Could not parse date: {date_value}")

        # Extract tags/keywords
        tags = None
        if "tags" in frontmatter:
            tags_value = frontmatter["tags"]
            if isinstance(tags_value, list):
                tags = [str(t) for t in tags_value]
            elif isinstance(tags_value, str):
                # Split comma-separated tags
                tags = [t.strip() for t in tags_value.split(",")]
        elif "keywords" in frontmatter:
            keywords_value = frontmatter["keywords"]
            if isinstance(keywords_value, list):
                tags = [str(k) for k in keywords_value]
            elif isinstance(keywords_value, str):
                tags = [k.strip() for k in keywords_value.split(",")]

        # Extract description/summary
        description = None
        if "description" in frontmatter:
            description = str(frontmatter["description"])
        elif "summary" in frontmatter:
            description = str(frontmatter["summary"])

        # Extract language
        language = None
        if "language" in frontmatter:
            language = str(frontmatter["language"])
        elif "lang" in frontmatter:
            language = str(frontmatter["lang"])

        # Extract publisher
        publisher = None
        if "publisher" in frontmatter:
            publisher = str(frontmatter["publisher"])

        # Get file size
        file_size = file_path.stat().st_size

        # Store all other frontmatter fields in custom_fields
        custom_fields = {
            k: v
            for k, v in frontmatter.items()
            if k
            not in [
                "title",
                "author",
                "authors",
                "date",
                "tags",
                "keywords",
                "description",
                "summary",
                "language",
                "lang",
                "publisher",
            ]
        }

        return Metadata(
            title=title,
            author=author,
            authors=authors,
            publisher=publisher,
            publication_date=publication_date,
            language=language,
            isbn=None,  # Markdown files don't have ISBN
            description=description,
            tags=tags,
            original_format="markdown",
            file_size=file_size,
            custom_fields=custom_fields if custom_fields else None,
        )

    def _create_default_metadata(self, file_path: Path) -> Metadata:
        """Create default metadata when no frontmatter is present.

        Args:
            file_path: Source file path.

        Returns:
            Metadata object with minimal information.
        """
        # Use filename (without extension) as title
        title = file_path.stem

        # Get file size
        file_size = file_path.stat().st_size

        return Metadata(
            title=title,
            author=None,
            authors=None,
            publisher=None,
            publication_date=None,
            language=None,
            isbn=None,
            description=None,
            tags=None,
            original_format="markdown",
            file_size=file_size,
            custom_fields=None,
        )

    def _normalize_markdown(self, text: str) -> str:
        """Normalize markdown format.

        Normalizations:
        - Convert underline-style headings to # style
        - Standardize list markers (normalize - and * to -)
        - Normalize link format
        - Remove excessive blank lines

        Args:
            text: Original markdown.

        Returns:
            Normalized markdown.
        """
        # Convert underline-style H1 (===) to # style
        # Pattern: text on one line, followed by line of ===
        text = re.sub(
            r"^(.+)\n=+\s*$",
            r"# \1",
            text,
            flags=re.MULTILINE,
        )

        # Convert underline-style H2 (---) to ## style
        # Pattern: text on one line, followed by line of ---
        # Only match if underline length is similar to text length (avoid horizontal rules)
        def replace_h2(match: re.Match[str]) -> str:
            title = match.group(1)
            underline = match.group(2)
            # Check if underline length is within 50% of title length
            # This avoids matching horizontal rules (---)
            if (
                len(underline) >= 3
                and abs(len(title) - len(underline)) <= len(title) * 0.5
            ):
                return f"## {title}"
            return match.group(0)

        text = re.sub(
            r"^(.+)\n(-{3,})\s*$",
            replace_h2,
            text,
            flags=re.MULTILINE,
        )

        # Normalize list markers: convert * to -
        text = re.sub(
            r"^(\s*)\*\s+",
            r"\1- ",
            text,
            flags=re.MULTILINE,
        )

        # Remove excessive blank lines (3+ newlines -> 2 newlines)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text

    def _extract_image_references(self, text: str) -> List[ImageReference]:
        """Extract image references from markdown.

        Format: ![alt text](image.png)

        Args:
            text: Markdown content.

        Returns:
            List of ImageReference objects.
        """
        images: List[ImageReference] = []

        # Pattern for markdown images: ![alt](url)
        pattern = re.compile(r"!\[([^\]]*)\]\(([^\)]+)\)")

        for idx, match in enumerate(pattern.finditer(text), start=1):
            alt_text = match.group(1).strip() or None
            image_url = match.group(2).strip()
            position = match.start()

            # Determine format from URL using improved detection
            format_name = self._extract_image_format(image_url)

            image_ref = ImageReference(
                image_id=f"img_{idx:03d}",
                position=position,
                file_path=image_url,  # Store URL or relative path
                alt_text=alt_text,
                size=None,  # Size not available without fetching image
                format=format_name,
            )

            images.append(image_ref)
            logger.debug(
                f"Found image {idx}: {image_url} (alt: {alt_text}, format: {format_name})"
            )

        return images

    def _extract_image_format(self, url: str) -> str:
        """Extract image format from URL or data URI.

        Handles:
        - Data URIs (data:image/png;base64,...)
        - URLs with format in query parameters (?format=png)
        - URLs with file extensions
        - URLs without extensions (returns 'unknown')

        Args:
            url: Image URL or data URI.

        Returns:
            Image format (e.g., 'png', 'jpg', 'webp') or 'unknown'.
        """
        # Handle data URIs
        if url.startswith("data:"):
            match = re.match(r"data:image/(\w+)", url)
            return match.group(1) if match else "unknown"

        # Check for query parameters with format
        if "?" in url:
            query_part = url.split("?", 1)[1]
            # Look for format=xxx or fmt=xxx in query
            format_match = re.search(r"(?:format|fmt)=(\w+)", query_part, re.IGNORECASE)
            if format_match:
                return format_match.group(1).lower()

        # Extract from file extension
        # Remove query parameters first
        path = url.split("?")[0]
        # Get the last part after the last slash
        filename = path.split("/")[-1]
        if "." in filename:
            ext = filename.split(".")[-1].lower()
            # Common image extensions
            if ext in ["jpg", "jpeg", "png", "gif", "webp", "svg", "bmp", "ico"]:
                return ext
            # Return extension even if not in common list
            return ext

        return "unknown"

    def _count_words(self, text: str) -> int:
        """Count words in text, excluding markdown syntax.

        Removes:
        - Code blocks (fenced with ```)
        - Inline code (backticks)
        - Markdown syntax characters (#, *, _, [], (), !)
        - URLs (http://, https://)

        Args:
            text: Text to count words in.

        Returns:
            Word count.
        """
        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", "", text)
        # Remove inline code
        text = re.sub(r"`[^`]+`", "", text)
        # Remove URLs
        text = re.sub(r"https?://\S+", "", text)
        # Remove markdown image syntax
        text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", r"\1", text)
        # Remove markdown link syntax, keep link text
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        # Remove markdown heading markers
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        # Remove emphasis markers (but not in the middle of words)
        text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
        text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)
        # Count remaining words
        return len([w for w in text.split() if w.strip()])

    def _estimate_reading_time(self, word_count: int) -> int:
        """Estimate reading time in minutes.

        Assumes average reading speed of 225 words per minute.

        Args:
            word_count: Total word count.

        Returns:
            Estimated reading time in minutes.
        """
        return max(1, round(word_count / 225))
