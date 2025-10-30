#!/usr/bin/env python3
"""
Example: Convert DOCX files to Markdown using OmniParser

This script demonstrates how to:
- Parse a DOCX file with OmniParser
- Extract content, metadata, chapters, and images
- Generate clean Markdown output

Usage:
    python docx_to_markdown.py input.docx output.md
    python docx_to_markdown.py input.docx  # Outputs to input.md
"""
import sys
from pathlib import Path
from omniparser import parse_document


def convert_docx_to_markdown(input_file: Path, output_file: Path = None) -> Path:
    """
    Convert a DOCX file to Markdown format.

    Args:
        input_file: Path to the input DOCX file
        output_file: Path to the output Markdown file (optional)

    Returns:
        Path to the generated Markdown file
    """
    # Default output filename
    if output_file is None:
        output_file = input_file.with_suffix('.md')

    print(f"Parsing {input_file.name}...")

    # Parse the DOCX file with full options
    doc = parse_document(
        input_file,
        options={
            "extract_images": True,
            "preserve_formatting": True,
            "extract_hyperlinks": True,
            "extract_lists": True,
        }
    )

    print(f"Generating markdown...")

    # Build markdown content
    markdown_content = []

    # Add title if available
    if doc.metadata.title and doc.metadata.title != "Word Document":
        markdown_content.append(f"# {doc.metadata.title}\n\n")

    # Add author if available
    if doc.metadata.author:
        markdown_content.append(f"**Author:** {doc.metadata.author}\n\n")

    # Add main content
    if doc.content:
        markdown_content.append(doc.content)
        markdown_content.append("\n\n")

    # Add chapters if any
    for chapter in doc.chapters:
        if chapter.title:
            markdown_content.append(f"## {chapter.title}\n\n")
        if chapter.content:
            markdown_content.append(chapter.content)
            markdown_content.append("\n\n")

    # Add image references if any
    if doc.images:
        markdown_content.append("\n---\n\n## Images\n\n")
        for img in doc.images:
            if img.alt_text:
                markdown_content.append(f"- {img.alt_text}\n")
            else:
                markdown_content.append(f"- Image: {img.filename}\n")

    # Write to file
    markdown_text = "".join(markdown_content)
    output_file.write_text(markdown_text, encoding="utf-8")

    print(f"✓ Markdown saved to: {output_file}")
    print(f"\nDocument Info:")
    print(f"  Title: {doc.metadata.title or 'N/A'}")
    print(f"  Author: {doc.metadata.author or 'N/A'}")
    print(f"  Word count: {doc.word_count}")
    print(f"  Chapters: {len(doc.chapters)}")
    print(f"  Images: {len(doc.images)}")

    return output_file


def main():
    """Main entry point for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python docx_to_markdown.py <input.docx> [output.md]")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    if input_file.suffix.lower() != '.docx':
        print(f"Error: Input file must be a .docx file")
        sys.exit(1)

    convert_docx_to_markdown(input_file, output_file)


if __name__ == "__main__":
    main()
