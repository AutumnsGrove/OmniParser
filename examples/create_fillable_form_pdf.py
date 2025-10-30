#!/usr/bin/env python3
"""
Example: Create a fillable form PDF from structured data

This script demonstrates how to create a professional PDF form with:
- Title and section headers
- Form fields with labels
- Input lines for user data
- Multi-paragraph text formatting
- Signature fields
- Automatic page breaks

Requires: reportlab
    pip install reportlab

Usage:
    python create_fillable_form_pdf.py
    # Or import and use programmatically:
    from create_fillable_form_pdf import create_form_pdf
    create_form_pdf(form_data, output_path)
"""
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from typing import Dict, List, Optional


def wrap_text(canvas_obj, text: str, font_name: str, font_size: int, max_width: float) -> List[str]:
    """
    Wrap text to fit within a specified width.

    Args:
        canvas_obj: ReportLab canvas object
        text: Text to wrap
        font_name: Font name (e.g., "Helvetica")
        font_size: Font size in points
        max_width: Maximum line width in points

    Returns:
        List of text lines that fit within the width
    """
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        if canvas_obj.stringWidth(test_line, font_name, font_size) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines


def draw_text_block(
    canvas_obj,
    text: str,
    x: float,
    y: float,
    font_name: str,
    font_size: int,
    max_width: float,
    line_height: float = None
) -> float:
    """
    Draw a block of text with automatic line wrapping.

    Args:
        canvas_obj: ReportLab canvas object
        text: Text to draw
        x: X position
        y: Starting Y position
        font_name: Font name
        font_size: Font size in points
        max_width: Maximum text width
        line_height: Line height (defaults to 1.5x font size)

    Returns:
        Final Y position after drawing text
    """
    if line_height is None:
        line_height = font_size * 1.5

    lines = wrap_text(canvas_obj, text, font_name, font_size, max_width)

    for line in lines:
        canvas_obj.drawString(x, y, line)
        y -= line_height

    return y


def create_form_pdf(
    form_data: Dict,
    output_path: Path,
    page_size=letter,
    margins: Dict[str, float] = None
) -> Path:
    """
    Create a fillable form PDF from structured data.

    Args:
        form_data: Dictionary containing form structure:
            {
                "title": "Form Title",
                "sections": [
                    {
                        "name": "Section Name",
                        "fields": ["Field 1", "Field 2", ...],
                        "paragraphs": ["Paragraph 1", "Paragraph 2", ...],
                        "signature_fields": ["Signature 1", "Signature 2", ...]
                    }
                ]
            }
        output_path: Path for output PDF file
        page_size: Page size (default: letter)
        margins: Dict with 'left', 'right', 'top', 'bottom' in inches

    Returns:
        Path to the created PDF file
    """
    # Default margins
    if margins is None:
        margins = {'left': 0.75, 'right': 0.75, 'top': 0.75, 'bottom': 0.75}

    # Create canvas
    c = canvas.Canvas(str(output_path), pagesize=page_size)
    width, height = page_size

    # Calculate margins
    left_margin = margins['left'] * inch
    right_margin = width - margins['right'] * inch
    top_margin = height - margins['top'] * inch
    bottom_margin = margins['bottom'] * inch
    text_width = right_margin - left_margin

    # Current y position
    y = top_margin

    # Draw title
    title = form_data.get("title", "Form")
    c.setFont("Helvetica-Bold", 16)
    title_width = c.stringWidth(title, "Helvetica-Bold", 16)
    c.drawString((width - title_width) / 2, y, title)
    y -= 0.5 * inch

    # Draw horizontal line under title
    c.line(left_margin, y, right_margin, y)
    y -= 0.3 * inch

    # Process each section
    for section in form_data.get("sections", []):
        # Check if we need a new page
        if y < bottom_margin + 4 * inch:
            c.showPage()
            y = top_margin

        # Section header
        section_name = section.get("name", "")
        if section_name:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(left_margin, y, section_name)
            y -= 0.3 * inch

        # Form fields
        for field in section.get("fields", []):
            # Check page break
            if y < bottom_margin + 0.5 * inch:
                c.showPage()
                y = top_margin

            if field:  # Skip empty fields (used for spacing)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(left_margin, y, field)
                y -= 0.15 * inch

            # Draw line for input
            c.line(left_margin, y, right_margin, y)
            y -= 0.35 * inch

        # Paragraphs
        for paragraph in section.get("paragraphs", []):
            # Check page break
            if y < bottom_margin + 2 * inch:
                c.showPage()
                y = top_margin

            c.setFont("Helvetica", 9)
            y = draw_text_block(c, paragraph, left_margin, y, "Helvetica", 9, text_width, 0.15 * inch)
            y -= 0.1 * inch

        # Signature fields
        signature_fields = section.get("signature_fields", [])
        if signature_fields:
            # Add horizontal line before signatures
            y -= 0.2 * inch
            c.line(left_margin, y, right_margin, y)
            y -= 0.3 * inch

            c.setFont("Helvetica-Bold", 12)
            c.drawString(left_margin, y, "Signatures")
            y -= 0.3 * inch

            for sig_field in signature_fields:
                # Check page break
                if y < bottom_margin + 0.7 * inch:
                    c.showPage()
                    y = top_margin

                c.setFont("Helvetica-Bold", 10)
                c.drawString(left_margin, y, sig_field)
                y -= 0.15 * inch
                # Draw signature line
                c.line(left_margin, y, right_margin, y)
                y -= 0.5 * inch

    # Save PDF
    c.save()
    print(f"✓ PDF created successfully: {output_path}")
    return output_path


def example_usage():
    """
    Example demonstrating how to use create_form_pdf.
    """
    # Define form structure
    form_data = {
        "title": "SAMPLE FORM",
        "sections": [
            {
                "name": "Contact Information",
                "fields": [
                    "NAME:",
                    "EMAIL:",
                    "PHONE:",
                    "ADDRESS:",
                    "",  # Empty field for extra address line
                ],
                "paragraphs": [],
                "signature_fields": []
            },
            {
                "name": "Consent & Authorization",
                "fields": [],
                "paragraphs": [
                    "I, ________________ (NAME), hereby authorize the use of the information provided in this form for the stated purposes. "
                    "This consent is given freely and with full understanding of the implications.",
                    "I understand that this form does not constitute a binding agreement and that I may withdraw my consent at any time "
                    "by providing written notice.",
                    "I acknowledge that I have read and understood the terms outlined above and agree to proceed."
                ],
                "signature_fields": [
                    "SIGNATURE:",
                    "DATE:",
                ]
            }
        ]
    }

    # Create PDF
    output_path = Path("example_form.pdf")
    create_form_pdf(form_data, output_path)


if __name__ == "__main__":
    example_usage()
