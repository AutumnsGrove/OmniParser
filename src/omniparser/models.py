"""
Data models for OmniParser document representation.

This module defines the core dataclasses used to represent parsed documents
in a universal format, enabling consistent handling across different file types
(EPUB, PDF, TXT, etc.).

Classes:
    ImageReference: Reference to an image within a document.
    QRCodeReference: Reference to a QR code found in the document.
    Chapter: A chapter or section with position tracking.
    Metadata: Universal metadata applicable to any document.
    ProcessingInfo: Information about the parsing execution.
    Document: Main container for all document data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ImageReference:
    """Reference to an image in the document.

    Attributes:
        image_id: Unique identifier for the image.
        position: Character position of image reference in document text.
        file_path: Local file path where the image is stored, if extracted.
        alt_text: Alternative text description of the image.
        size: Image dimensions as (width, height) tuple in pixels.
        format: Image format (e.g., "jpeg", "png", "webp").

    Example:
        >>> img = ImageReference(
        ...     image_id="img_001",
        ...     position=1250,
        ...     file_path="/tmp/image_001.png",
        ...     alt_text="Cover image",
        ...     size=(800, 600),
        ...     format="png"
        ... )
    """

    image_id: str
    position: int
    file_path: Optional[str] = None
    alt_text: Optional[str] = None
    size: Optional[tuple[int, int]] = None
    format: str = "unknown"


@dataclass
class QRCodeReference:
    """Reference to a QR code found in the document.

    Attributes:
        qr_id: Unique identifier for the QR code.
        raw_data: Raw data encoded in the QR code.
        data_type: Type of data (URL, TEXT, VCARD, WIFI, etc.).
        source_image: Image ID or file path where QR code was found.
        position: Bounding box position as dict with x, y, width, height.
        page_number: Page number where QR code was found (1-indexed).
        fetched_content: Content retrieved from URL (if data_type is URL).
        fetch_status: Status of content fetch (success, partial, failed, skipped).
        fetch_notes: List of notes about the fetch process.

    Example:
        >>> qr = QRCodeReference(
        ...     qr_id="qr_001",
        ...     raw_data="https://example.com/recipe",
        ...     data_type="URL",
        ...     source_image="img_005",
        ...     page_number=3,
        ...     fetched_content="Recipe content here...",
        ...     fetch_status="success",
        ...     fetch_notes=["Followed 2 redirects"]
        ... )
    """

    qr_id: str
    raw_data: str
    data_type: str = "TEXT"
    source_image: Optional[str] = None
    position: Optional[Dict[str, int]] = None
    page_number: Optional[int] = None
    fetched_content: Optional[str] = None
    fetch_status: str = "pending"
    fetch_notes: List[str] = field(default_factory=list)


@dataclass
class Chapter:
    """Chapter or section with position tracking for text range extraction.

    Attributes:
        chapter_id: Unique identifier for the chapter (typically sequential).
        title: Chapter title or heading.
        content: Full text content of the chapter.
        start_position: Character position where chapter begins in full document text.
        end_position: Character position where chapter ends in full document text.
        word_count: Number of words in the chapter content.
        level: Heading level (1=main chapter, 2=subsection, 3=subsubsection, etc.).
        metadata: Optional dictionary for chapter-specific metadata.

    Example:
        >>> chapter = Chapter(
        ...     chapter_id=1,
        ...     title="Introduction",
        ...     content="This is the introduction content...",
        ...     start_position=0,
        ...     end_position=450,
        ...     word_count=75,
        ...     level=1
        ... )
    """

    chapter_id: int
    title: str
    content: str
    start_position: int
    end_position: int
    word_count: int
    level: int = 1
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Metadata:
    """Universal document metadata applicable to any format.

    This class provides a unified interface for metadata across different
    document types (EPUB, PDF, TXT, etc.), allowing consistent access to
    common document properties.

    Attributes:
        title: Document title.
        author: Primary author name.
        authors: List of all authors/contributors.
        publisher: Publishing organization or imprint.
        publication_date: Date document was published.
        language: Primary language code (e.g., "en", "fr").
        isbn: International Standard Book Number (for books).
        description: Summary or abstract of document content.
        tags: List of keywords or categorization tags.
        original_format: Original file format before parsing (e.g., "epub", "pdf").
        file_size: Size of original file in bytes.
        custom_fields: Dictionary for format-specific metadata not covered above.

    Example:
        >>> metadata = Metadata(
        ...     title="The Great Gatsby",
        ...     author="F. Scott Fitzgerald",
        ...     publisher="Scribner",
        ...     publication_date=datetime(1925, 4, 10),
        ...     language="en",
        ...     isbn="978-0743273565",
        ...     description="A novel set in Jazz Age America.",
        ...     tags=["fiction", "classic", "american-literature"],
        ...     original_format="epub",
        ...     file_size=1024000
        ... )
    """

    title: Optional[str] = None
    author: Optional[str] = None
    authors: Optional[List[str]] = None
    publisher: Optional[str] = None
    publication_date: Optional[datetime] = None
    language: Optional[str] = None
    isbn: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    original_format: Optional[str] = None
    file_size: int = 0
    custom_fields: Optional[Dict[str, Any]] = None


@dataclass
class ProcessingInfo:
    """Information about the document parsing execution.

    Tracks metadata about how a document was parsed, including which parser
    was used, how long it took, and any issues encountered.

    Attributes:
        parser_used: Name of the parser implementation used.
        parser_version: Version of the parser.
        processing_time: Time taken to parse document in seconds.
        timestamp: Datetime when parsing was completed.
        warnings: List of non-fatal issues encountered during parsing.
        options_used: Dictionary of parsing options/settings applied.

    Example:
        >>> info = ProcessingInfo(
        ...     parser_used="EPUBParser",
        ...     parser_version="1.0.0",
        ...     processing_time=2.543,
        ...     timestamp=datetime.now(),
        ...     warnings=["Missing cover image", "Invalid chapter link"],
        ...     options_used={"extract_images": True, "parse_toc": True}
        ... )
    """

    parser_used: str
    parser_version: str
    processing_time: float
    timestamp: datetime
    warnings: List[str] = field(default_factory=list)
    options_used: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """Main container for parsed document data.

    Provides a universal representation of document content and metadata,
    enabling consistent access and processing regardless of original format.

    Attributes:
        document_id: Unique identifier for the document instance.
        content: Full concatenated text content of the document.
        chapters: List of Chapter objects representing document structure.
        images: List of ImageReference objects found in the document.
        metadata: Metadata object containing document-level information.
        processing_info: ProcessingInfo object with parsing execution details.
        word_count: Total number of words in the document.
        estimated_reading_time: Estimated reading time in minutes (based on avg
            reading speed of 200-250 words per minute).

    Example:
        >>> doc = Document(
        ...     document_id="doc_12345",
        ...     content="Full document text here...",
        ...     chapters=[chapter1, chapter2],
        ...     images=[image1, image2],
        ...     metadata=Metadata(title="My Document"),
        ...     processing_info=info,
        ...     word_count=50000,
        ...     estimated_reading_time=200
        ... )
    """

    document_id: str
    content: str
    chapters: List[Chapter]
    images: List[ImageReference]
    metadata: Metadata
    processing_info: ProcessingInfo
    word_count: int
    estimated_reading_time: int

    def get_chapter(self, chapter_id: int) -> Optional[Chapter]:
        """Get chapter by ID.

        Args:
            chapter_id: Chapter ID to retrieve.

        Returns:
            Chapter object if found, None otherwise.
        """
        for chapter in self.chapters:
            if chapter.chapter_id == chapter_id:
                return chapter
        return None

    def get_text_range(self, start: int, end: int) -> str:
        """Extract text between positions.

        Args:
            start: Start character position.
            end: End character position.

        Returns:
            Text substring from start to end.
        """
        return self.content[start:end]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation of Document.
        """
        from dataclasses import asdict

        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Deserialize from dictionary.

        Args:
            data: Dictionary with Document data.

        Returns:
            Document object.
        """
        # Handle nested dataclasses
        if "metadata" in data and isinstance(data["metadata"], dict):
            data["metadata"] = Metadata(**data["metadata"])
        if "processing_info" in data and isinstance(data["processing_info"], dict):
            data["processing_info"] = ProcessingInfo(**data["processing_info"])
        if "chapters" in data:
            data["chapters"] = [
                Chapter(**c) if isinstance(c, dict) else c for c in data["chapters"]
            ]
        if "images" in data:
            data["images"] = [
                ImageReference(**i) if isinstance(i, dict) else i
                for i in data["images"]
            ]
        return cls(**data)

    def save_json(self, path: str) -> None:
        """Save to JSON file.

        Args:
            path: File path to save to.
        """
        import json
        from datetime import datetime

        def json_serializer(obj: Any) -> str:
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=json_serializer)

    @classmethod
    def load_json(cls, path: str) -> "Document":
        """Load from JSON file.

        Args:
            path: File path to load from.

        Returns:
            Document object.
        """
        import json
        from datetime import datetime

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Convert ISO datetime strings back to datetime objects
        if "metadata" in data and data["metadata"].get("publication_date"):
            data["metadata"]["publication_date"] = datetime.fromisoformat(
                data["metadata"]["publication_date"]
            )
        if "processing_info" in data and data["processing_info"].get("timestamp"):
            data["processing_info"]["timestamp"] = datetime.fromisoformat(
                data["processing_info"]["timestamp"]
            )

        return cls.from_dict(data)
