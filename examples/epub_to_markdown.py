#!/usr/bin/env python3
"""
EPUB to Markdown Converter

Demonstrates OmniParser's EPUB parsing capabilities by converting an EPUB file
to a clean, well-formatted Markdown document with proper headers, chapters,
metadata, and embedded images.

Features:
- Extracts images to persistent directory ({output_name}_images/)
- Embeds images in markdown using relative paths (Obsidian-compatible)
- Preserves chapter structure and metadata
- Generates table of contents with anchor links
- Includes document statistics

Usage:
    python examples/epub_to_markdown.py <input.epub> [output.md]

Example:
    python examples/epub_to_markdown.py book.epub book.md
    # Creates: book.md and book_images/ directory with all images
"""

import sys
from pathlib import Path
from datetime import datetime

from omniparser import parse_document


def epub_to_markdown(
    epub_path: Path, output_path: Path, extract_images: bool = True
) -> None:
    """Convert EPUB to Markdown file with optional image extraction.

    Args:
        epub_path: Path to input EPUB file.
        output_path: Path to output Markdown file.
        extract_images: If True, extracts images to {output_name}_images/ directory.
    """
    print(f"📚 Parsing EPUB: {epub_path.name}")
    print(f"   File size: {epub_path.stat().st_size / 1024 / 1024:.2f} MB")
    print()

    # Determine image output directory
    image_dir = None
    if extract_images:
        # Create image directory: book.md -> book_images/
        image_dir_name = output_path.stem + "_images"
        image_dir = output_path.parent / image_dir_name
        print(f"🖼️  Images will be saved to: {image_dir}")
        print()

    # Parse the EPUB with image extraction options
    import time

    start = time.time()
    options = {}
    if image_dir:
        options["image_output_dir"] = str(image_dir)
    doc = parse_document(epub_path, options=options)
    elapsed = time.time() - start

    print(f"✅ Parsed successfully in {elapsed:.2f} seconds")
    print(f"   📖 {len(doc.chapters)} chapters")
    print(f"   📝 {doc.word_count:,} words")
    print(f"   🖼️  {len(doc.images)} images")
    print()

    # Create markdown content
    print(f"✍️  Generating Markdown...")

    markdown_lines = []

    # Add title and metadata header
    markdown_lines.append("---")
    markdown_lines.append(f"title: {doc.metadata.title or 'Unknown'}")
    if doc.metadata.author:
        markdown_lines.append(f"author: {doc.metadata.author}")
    if doc.metadata.authors and len(doc.metadata.authors) > 1:
        markdown_lines.append(f"authors: {', '.join(doc.metadata.authors)}")
    if doc.metadata.publisher:
        markdown_lines.append(f"publisher: {doc.metadata.publisher}")
    if doc.metadata.publication_date:
        markdown_lines.append(
            f"published: {doc.metadata.publication_date.strftime('%Y-%m-%d')}"
        )
    if doc.metadata.language:
        markdown_lines.append(f"language: {doc.metadata.language}")
    if doc.metadata.isbn:
        markdown_lines.append(f"isbn: {doc.metadata.isbn}")
    markdown_lines.append(f"word_count: {doc.word_count:,}")
    markdown_lines.append(f"reading_time: {doc.estimated_reading_time} minutes")
    markdown_lines.append(f"converted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    markdown_lines.append(f"source: {epub_path.name}")
    markdown_lines.append("---")
    markdown_lines.append("")

    # Add main title
    markdown_lines.append(f"# {doc.metadata.title or 'Unknown Title'}")
    markdown_lines.append("")

    # Add author if available
    if doc.metadata.author:
        markdown_lines.append(f"**Author:** {doc.metadata.author}")
        markdown_lines.append("")

    # Add description if available
    if doc.metadata.description:
        markdown_lines.append("## Description")
        markdown_lines.append("")
        markdown_lines.append(doc.metadata.description)
        markdown_lines.append("")

    # Add table of contents
    if doc.chapters:
        markdown_lines.append("## Table of Contents")
        markdown_lines.append("")
        for i, chapter in enumerate(doc.chapters, 1):
            # Indent based on chapter level
            indent = "  " * (chapter.level - 1)
            markdown_lines.append(
                f"{indent}{i}. [{chapter.title}](#{_to_anchor(chapter.title)})"
            )
        markdown_lines.append("")
        markdown_lines.append("---")
        markdown_lines.append("")

    # Add chapters
    for chapter in doc.chapters:
        # Add chapter heading (# for level 1, ## for level 2, etc.)
        heading_prefix = "#" * (chapter.level + 1)
        markdown_lines.append(f"{heading_prefix} {chapter.title}")
        markdown_lines.append("")

        # Add chapter content
        markdown_lines.append(chapter.content)
        markdown_lines.append("")
        markdown_lines.append("---")
        markdown_lines.append("")

    # Add images section if images were extracted
    if doc.images and image_dir:
        markdown_lines.append("## Images")
        markdown_lines.append("")
        markdown_lines.append(
            f"This document contains {len(doc.images)} images extracted from the EPUB:"
        )
        markdown_lines.append("")

        for img in doc.images:
            # Get relative path from markdown file to image
            img_path = Path(img.file_path)
            try:
                # Try to make it relative to the markdown file location
                relative_path = img_path.relative_to(output_path.parent)
            except ValueError:
                # If that fails, use the full path
                relative_path = img_path

            # Create markdown image embed
            alt_text = img.alt_text or f"Image {img.image_id}"
            size_info = f" ({img.size[0]}x{img.size[1]})" if img.size else ""
            markdown_lines.append(f"### {img.image_id}{size_info}")
            markdown_lines.append("")
            markdown_lines.append(f"![{alt_text}]({relative_path})")
            markdown_lines.append("")

        markdown_lines.append("---")
        markdown_lines.append("")

    # Add footer with statistics
    markdown_lines.append("---")
    markdown_lines.append("")
    markdown_lines.append("## Document Statistics")
    markdown_lines.append("")
    markdown_lines.append(f"- **Total Chapters:** {len(doc.chapters)}")
    markdown_lines.append(f"- **Total Words:** {doc.word_count:,}")
    markdown_lines.append(
        f"- **Estimated Reading Time:** {doc.estimated_reading_time} minutes"
    )
    markdown_lines.append(f"- **Images:** {len(doc.images)}")
    markdown_lines.append(f"- **Original Format:** EPUB")
    markdown_lines.append("")
    markdown_lines.append(
        f"*Converted from {epub_path.name} using [OmniParser](https://github.com/AutumnsGrove/omniparser)*"
    )

    # Write to file
    markdown_content = "\n".join(markdown_lines)
    output_path.write_text(markdown_content, encoding="utf-8")

    print(f"✅ Markdown file created: {output_path}")
    print(f"   📄 Size: {output_path.stat().st_size / 1024:.1f} KB")
    print()
    print(f"🎉 Conversion complete!")


def _to_anchor(text: str) -> str:
    """Convert text to markdown anchor link.

    Args:
        text: Text to convert.

    Returns:
        Anchor-friendly text (lowercase, hyphens, no special chars).
    """
    # Convert to lowercase
    anchor = text.lower()

    # Replace spaces with hyphens
    anchor = anchor.replace(" ", "-")

    # Remove special characters
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-"
    anchor = "".join(c for c in anchor if c in allowed)

    # Remove consecutive hyphens
    while "--" in anchor:
        anchor = anchor.replace("--", "-")

    # Strip leading/trailing hyphens
    anchor = anchor.strip("-")

    return anchor


def main():
    """Main entry point."""
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python epub_to_markdown.py <input.epub> [output.md]")
        print()
        print("Example:")
        print("  python epub_to_markdown.py book.epub")
        print("  python epub_to_markdown.py book.epub output.md")
        sys.exit(1)

    epub_path = Path(sys.argv[1])

    # Validate input file
    if not epub_path.exists():
        print(f"❌ Error: File not found: {epub_path}")
        sys.exit(1)

    if not epub_path.suffix.lower() == ".epub":
        print(f"❌ Error: File must be an EPUB (.epub extension)")
        sys.exit(1)

    # Determine output path
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        # Default: same name as input but with .md extension
        output_path = epub_path.with_suffix(".md")

    # Check if output file exists
    if output_path.exists():
        response = input(f"⚠️  Output file exists: {output_path}\nOverwrite? [y/N]: ")
        if response.lower() != "y":
            print("Cancelled.")
            sys.exit(0)

    # Convert EPUB to Markdown
    try:
        epub_to_markdown(epub_path, output_path)
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
