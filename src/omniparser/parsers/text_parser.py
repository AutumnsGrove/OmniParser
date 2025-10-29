"""
Text parser implementation for plain text files.

This module provides the TextParser class for parsing plain text files with
automatic encoding detection, line ending normalization, and heuristic chapter
detection. It converts text files to OmniParser's universal Document format.

Features:
- Automatic encoding detection using chardet
- Line ending normalization (Windows/Mac to Unix)
- Pattern-based chapter detection
- Text cleaning integration
- Fallback to single chapter if no structure detected
"""

import logging
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..base.base_parser import BaseParser
from ..exceptions import FileReadError, ParsingError, ValidationError
from ..models import Chapter, Document, ImageReference, Metadata, ProcessingInfo
from ..processors.text_cleaner import clean_text
from ..utils.encoding import detect_encoding, normalize_line_endings

logger = logging.getLogger(__name__)


class TextParser(BaseParser):
    """
    Parser for plain text files with encoding detection.

    Features:
    - Automatic encoding detection (chardet)
    - Line ending normalization (Unix style)
    - Heuristic chapter detection from text patterns
    - Text cleaning and normalization
    - Fallback to single chapter if no structure detected

    Options:
        auto_detect_encoding (bool): Auto-detect encoding (default: True)
        encoding (str): Force specific encoding (default: None)
        normalize_line_endings_enabled (bool): Normalize line endings (default: True)
        attempt_chapter_detection (bool): Try to detect chapters (default: True)
        clean_text (bool): Apply text cleaning (default: True)
        min_chapter_length (int): Minimum words per chapter (default: 50)

    Chapter Detection Patterns:
        - "Chapter 1", "Chapter One", "CHAPTER I"
        - "Part 1", "Section A"
        - "I. Introduction", "II. Methods"
        - Numbered patterns at line start

    Example:
        >>> parser = TextParser({'auto_detect_encoding': True})
        >>> doc = parser.parse(Path("notes.txt"))
        >>> print(doc.chapters[0].title)
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize Text parser with options.

        Args:
            options: Parser configuration dictionary.
        """
        super().__init__(options)

        # Set default options
        self.options.setdefault("auto_detect_encoding", True)
        self.options.setdefault("encoding", None)
        self.options.setdefault("normalize_line_endings_enabled", True)
        self.options.setdefault("attempt_chapter_detection", True)
        self.options.setdefault("clean_text", True)
        self.options.setdefault("min_chapter_length", 50)

        # Initialize tracking
        self._warnings: List[str] = []
        self._start_time: Optional[float] = None
        self._detected_encoding: Optional[str] = None

        # Chapter detection patterns (ordered by specificity)
        self.chapter_patterns = [
            # Chapter with numbers
            (
                r"^Chapter\s+(\d+|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)",
                "Chapter",
            ),
            # CHAPTER (all caps)
            (r"^CHAPTER\s+(\d+|[IVX]+)", "Chapter"),
            # Part/Section
            (r"^Part\s+(\d+|[IVX]+|One|Two|Three|Four|Five)", "Part"),
            (r"^Section\s+(\d+|[A-Z])", "Section"),
            # Roman numerals at line start
            (r"^([IVX]+)\.\s+[A-Z]", "Section"),
            # Numbers at line start (e.g., "1. Introduction")
            (r"^(\d+)\.\s+[A-Z][a-z]+", "Chapter"),
        ]

    def supports_format(self, file_path: Union[Path, str]) -> bool:
        """Check if file is plain text.

        Args:
            file_path: Path to check.

        Returns:
            True if file has .txt extension or no extension, False otherwise.
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        return file_path.suffix.lower() in [".txt", ""]

    def parse(self, file_path: Union[Path, str]) -> Document:
        """
        Parse plain text file.

        Process:
        1. Detect encoding (or use specified)
        2. Read file with correct encoding
        3. Normalize line endings
        4. Attempt chapter detection
        5. If no chapters found, create single chapter
        6. Apply text cleaning
        7. Create minimal metadata
        8. Build and return Document

        Args:
            file_path: Path to text file.

        Returns:
            Document object with parsed content, chapters, and metadata.

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
            # Step 1: Validate text file
            self._validate_text_file(file_path)

            # Step 2: Read file with encoding detection
            logger.info(f"Reading text file: {file_path}")
            text = self._read_with_encoding(file_path)

            # Step 3: Normalize line endings
            if self.options.get("normalize_line_endings_enabled"):
                logger.info("Normalizing line endings")
                text = normalize_line_endings(text)

            # Step 4: Detect chapters or create single chapter
            if self.options.get("attempt_chapter_detection"):
                logger.info("Attempting chapter detection")
                chapters = self._detect_chapters_from_patterns(text)
                if not chapters:
                    logger.info("No chapters detected, creating single chapter")
                    chapters = self._create_single_chapter(text)
            else:
                logger.info("Chapter detection disabled, creating single chapter")
                chapters = self._create_single_chapter(text)

            # Step 5: Apply text cleaning (if enabled)
            if self.options.get("clean_text"):
                logger.info("Cleaning text")
                text = clean_text(text)
                for chapter in chapters:
                    chapter.content = clean_text(chapter.content)

            # Step 6: Filter chapters by minimum length
            chapters = self._postprocess_chapters(chapters)

            # Step 7: Create metadata
            metadata = self._create_metadata(file_path, text)

            # Step 8: Calculate statistics
            word_count = self._count_words(text)
            reading_time = self._estimate_reading_time(word_count)

            # Step 9: Create processing info
            processing_time = time.time() - self._start_time
            options_with_encoding = self.options.copy()
            if self._detected_encoding:
                options_with_encoding["detected_encoding"] = self._detected_encoding

            processing_info = ProcessingInfo(
                parser_used="TextParser",
                parser_version="1.0.0",
                processing_time=processing_time,
                timestamp=datetime.now(),
                warnings=self._warnings,
                options_used=options_with_encoding,
            )

            # Step 10: Create and return Document
            document = Document(
                document_id=str(uuid.uuid4()),
                content=text,
                chapters=chapters,
                images=[],  # Text files don't have images
                metadata=metadata,
                processing_info=processing_info,
                word_count=word_count,
                estimated_reading_time=reading_time,
            )

            logger.info(
                f"Text parsing complete: {word_count} words, {len(chapters)} chapters"
            )
            return document

        except (FileReadError, ValidationError):
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Text parsing failed: {e}")
            raise ParsingError(
                f"Failed to parse text file: {e}",
                parser="TextParser",
                original_error=e,
            )

    def _validate_text_file(self, file_path: Path) -> None:
        """Validate text file before parsing.

        Checks:
        - File exists
        - File is readable
        - File size is reasonable (not empty, not too large)

        Args:
            file_path: Path to text file.

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

        # Check file size
        file_size = file_path.stat().st_size
        if file_size == 0:
            raise ValidationError(f"Empty file: {file_path}")

        # Warn if file is very large (>50MB)
        if file_size > 50 * 1024 * 1024:
            logger.warning(f"Large text file ({file_size / 1024 / 1024:.1f} MB)")
            self._warnings.append(f"Large file size: {file_size / 1024 / 1024:.1f} MB")

    def _read_with_encoding(self, file_path: Path) -> str:
        """
        Read file with detected or specified encoding.

        Uses encoding.py utilities:
        - detect_encoding()
        - Falls back to utf-8 if detection fails

        Args:
            file_path: Path to text file.

        Returns:
            File content as string.

        Raises:
            FileReadError: If file cannot be read.
        """
        # Determine encoding
        if self.options.get("auto_detect_encoding") and not self.options.get(
            "encoding"
        ):
            try:
                encoding = detect_encoding(file_path)
                self._detected_encoding = encoding
                logger.info(f"Detected encoding: {encoding}")
            except Exception as e:
                logger.warning(f"Encoding detection failed: {e}, using utf-8")
                self._warnings.append(f"Encoding detection failed: {e}")
                encoding = "utf-8"
                self._detected_encoding = encoding
        else:
            encoding = self.options.get("encoding", "utf-8")
            self._detected_encoding = encoding
            logger.info(f"Using specified encoding: {encoding}")

        # Read file with encoding
        try:
            with open(file_path, "r", encoding=encoding, errors="replace") as f:
                text = f.read()
            return text
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            raise FileReadError(f"Failed to read file {file_path}: {e}")

    def _detect_chapters_from_patterns(self, text: str) -> List[Chapter]:
        """
        Attempt to detect chapters using regex patterns.

        Process:
        1. Apply each pattern to find chapter markers
        2. If found, split text at markers
        3. Create Chapter objects with detected titles
        4. Return list of chapters

        If no patterns match, return empty list (caller creates single chapter).

        Args:
            text: Normalized text

        Returns:
            List of Chapter objects or empty list
        """
        lines = text.split("\n")
        chapter_markers: List[tuple[int, str, str]] = []  # (line_num, title, type)

        # Find all chapter markers
        for line_num, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # Try each pattern
            for pattern, chapter_type in self.chapter_patterns:
                match = re.match(pattern, line_stripped, re.IGNORECASE)
                if match:
                    # Found a chapter marker
                    title = line_stripped
                    chapter_markers.append((line_num, title, chapter_type))
                    logger.debug(f"Found chapter marker at line {line_num}: {title}")
                    break  # Only match first pattern

        # If no markers found, return empty list
        if len(chapter_markers) < 2:
            # Need at least 2 markers to create meaningful chapters
            logger.info(
                f"Found {len(chapter_markers)} chapter markers, need at least 2"
            )
            return []

        # Create chapters from markers
        chapters: List[Chapter] = []
        chapter_id = 1

        for i, (line_num, title, chapter_type) in enumerate(chapter_markers):
            # Determine start and end line numbers
            start_line = line_num
            if i + 1 < len(chapter_markers):
                end_line = chapter_markers[i + 1][0]
            else:
                end_line = len(lines)

            # Extract chapter content
            chapter_lines = lines[start_line:end_line]
            chapter_content = "\n".join(chapter_lines).strip()

            # Calculate positions in full text
            start_position = sum(len(lines[j]) + 1 for j in range(start_line))
            end_position = sum(len(lines[j]) + 1 for j in range(end_line))

            # Calculate word count
            word_count = len(chapter_content.split())

            # Create chapter object
            chapter = Chapter(
                chapter_id=chapter_id,
                title=title,
                content=chapter_content,
                start_position=start_position,
                end_position=end_position,
                word_count=word_count,
                level=1,
                metadata={
                    "detection_method": "pattern",
                    "pattern_type": chapter_type,
                    "line_number": line_num,
                },
            )

            chapters.append(chapter)
            chapter_id += 1

            logger.debug(
                f"Created chapter {chapter_id - 1}: '{title}' ({word_count} words)"
            )

        logger.info(f"Detected {len(chapters)} chapters using patterns")
        return chapters

    def _create_single_chapter(self, text: str) -> List[Chapter]:
        """
        Create single chapter when no structure detected.

        Args:
            text: Full text content

        Returns:
            List with single Chapter object
        """
        # Try to extract title from first line
        lines = text.split("\n")
        first_line = lines[0].strip() if lines else "Document"

        # Use first line as title if it's short (< 100 chars) and not empty
        if first_line and len(first_line) < 100:
            title = first_line
        else:
            title = "Document"

        word_count = len(text.split())

        chapter = Chapter(
            chapter_id=1,
            title=title,
            content=text,
            start_position=0,
            end_position=len(text),
            word_count=word_count,
            level=1,
            metadata={"detection_method": "single_chapter"},
        )

        logger.info(f"Created single chapter: '{title}' ({word_count} words)")
        return [chapter]

    def _postprocess_chapters(self, chapters: List[Chapter]) -> List[Chapter]:
        """Post-process chapters: filter short ones and handle duplicates.

        Applies the following filters:
        - Remove chapters below min_chapter_length threshold
        - Disambiguate duplicate chapter titles

        Args:
            chapters: List of chapters to process.

        Returns:
            Filtered and cleaned chapter list.
        """
        min_length = self.options.get("min_chapter_length", 50)

        # Filter short chapters
        filtered_chapters: List[Chapter] = []
        removed_count = 0

        for chapter in chapters:
            if chapter.word_count < min_length:
                logger.debug(
                    f"Filtering chapter '{chapter.title}' ({chapter.word_count} words < {min_length} minimum)"
                )
                self._warnings.append(
                    f"Filtered short chapter: '{chapter.title}' ({chapter.word_count} words)"
                )
                removed_count += 1
            else:
                filtered_chapters.append(chapter)

        if removed_count > 0:
            logger.info(
                f"Filtered {removed_count} short chapters (< {min_length} words)"
            )

        # Handle duplicate titles
        title_counts: Dict[str, int] = {}
        for chapter in filtered_chapters:
            title = chapter.title
            if title in title_counts:
                # Duplicate found - add disambiguation
                title_counts[title] += 1
                new_title = f"{title} ({title_counts[title]})"
                logger.debug(
                    f"Disambiguating duplicate title: '{title}' -> '{new_title}'"
                )
                chapter.title = new_title
            else:
                title_counts[title] = 1

        # Re-number chapter IDs to be sequential after filtering
        for i, chapter in enumerate(filtered_chapters, start=1):
            chapter.chapter_id = i

        return filtered_chapters

    def _create_metadata(self, file_path: Path, text: str) -> Metadata:
        """
        Create minimal metadata for text file.

        Can extract:
        - Title from first line (if short)
        - File size
        - Custom fields (detected encoding, line count)

        Args:
            file_path: Source file path
            text: Full text content

        Returns:
            Metadata object
        """
        # Try to extract title from first line
        lines = text.split("\n")
        first_line = lines[0].strip() if lines else ""

        # Use first line as title if it's short and not empty
        title: Optional[str] = None
        if first_line and len(first_line) < 100:
            title = first_line
        else:
            # Use filename without extension
            title = file_path.stem

        # Calculate file size
        file_size = file_path.stat().st_size

        # Calculate line count
        line_count = len(lines)

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
            original_format="text",
            file_size=file_size,
            custom_fields={
                "encoding": self._detected_encoding,
                "line_count": line_count,
            },
        )

    def _count_words(self, text: str) -> int:
        """Count words in text.

        Args:
            text: Text to count words in.

        Returns:
            Word count.
        """
        return len(text.split())

    def _estimate_reading_time(self, word_count: int) -> int:
        """Estimate reading time in minutes.

        Assumes average reading speed of 200-250 words per minute.
        Uses 225 WPM as middle ground.

        Args:
            word_count: Total word count.

        Returns:
            Estimated reading time in minutes.
        """
        return max(1, round(word_count / 225))
