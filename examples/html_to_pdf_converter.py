#!/usr/bin/env python3
"""
Example: Convert HTML files to PDF

This script demonstrates different methods for converting HTML to PDF:
- wkhtmltopdf (command-line tool)
- weasyprint (Python library)
- pdfkit (Python wrapper for wkhtmltopdf)

Note: This script requires external dependencies. Install one of:
    brew install wkhtmltopdf           # macOS
    apt-get install wkhtmltopdf        # Ubuntu/Debian
    pip install weasyprint             # Python library
    pip install pdfkit                 # Python library

Usage:
    python html_to_pdf_converter.py input.html output.pdf
    python html_to_pdf_converter.py input.html  # Outputs to input.pdf
"""
import sys
import subprocess
from pathlib import Path


def convert_html_to_pdf_wkhtmltopdf(html_file: Path, pdf_file: Path) -> bool:
    """
    Convert HTML to PDF using wkhtmltopdf command-line tool.

    Args:
        html_file: Path to input HTML file
        pdf_file: Path to output PDF file

    Returns:
        True if successful, False otherwise
    """
    try:
        result = subprocess.run(
            ["wkhtmltopdf", str(html_file), str(pdf_file)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✓ PDF created successfully using wkhtmltopdf: {pdf_file}")
            return True
        else:
            print(f"wkhtmltopdf error: {result.stderr}")
            return False
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        print("Timeout while converting to PDF")
        return False


def convert_html_to_pdf_weasyprint(html_file: Path, pdf_file: Path) -> bool:
    """
    Convert HTML to PDF using weasyprint Python library.

    Args:
        html_file: Path to input HTML file
        pdf_file: Path to output PDF file

    Returns:
        True if successful, False otherwise
    """
    try:
        from weasyprint import HTML
        HTML(str(html_file)).write_pdf(str(pdf_file))
        print(f"✓ PDF created successfully using weasyprint: {pdf_file}")
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"Error with weasyprint: {e}")
        return False


def convert_html_to_pdf_pdfkit(html_file: Path, pdf_file: Path) -> bool:
    """
    Convert HTML to PDF using pdfkit Python library.

    Args:
        html_file: Path to input HTML file
        pdf_file: Path to output PDF file

    Returns:
        True if successful, False otherwise
    """
    try:
        import pdfkit
        pdfkit.from_file(str(html_file), str(pdf_file))
        print(f"✓ PDF created successfully using pdfkit: {pdf_file}")
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"Error with pdfkit: {e}")
        return False


def convert_html_to_pdf(html_file: Path, pdf_file: Path = None) -> Path:
    """
    Convert HTML to PDF using the first available method.

    Tries methods in order:
    1. wkhtmltopdf (command-line)
    2. weasyprint (Python library)
    3. pdfkit (Python library)

    Args:
        html_file: Path to input HTML file
        pdf_file: Path to output PDF file (optional)

    Returns:
        Path to the generated PDF file

    Raises:
        RuntimeError: If no conversion method is available
    """
    # Default output filename
    if pdf_file is None:
        pdf_file = html_file.with_suffix('.pdf')

    print(f"Converting {html_file.name} to PDF...")

    # Try each method
    methods = [
        ("wkhtmltopdf", convert_html_to_pdf_wkhtmltopdf),
        ("weasyprint", convert_html_to_pdf_weasyprint),
        ("pdfkit", convert_html_to_pdf_pdfkit),
    ]

    for name, method in methods:
        if method(html_file, pdf_file):
            return pdf_file

    # If we get here, no method worked
    raise RuntimeError(
        "No PDF conversion tools found. Please install one of:\n"
        "  - wkhtmltopdf: brew install wkhtmltopdf (or apt-get install wkhtmltopdf)\n"
        "  - weasyprint: pip install weasyprint\n"
        "  - pdfkit: pip install pdfkit"
    )


def main():
    """Main entry point for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python html_to_pdf_converter.py <input.html> [output.pdf]")
        sys.exit(1)

    html_file = Path(sys.argv[1])
    pdf_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if not html_file.exists():
        print(f"Error: File not found: {html_file}")
        sys.exit(1)

    if html_file.suffix.lower() not in ['.html', '.htm']:
        print(f"Error: Input file must be an .html or .htm file")
        sys.exit(1)

    try:
        convert_html_to_pdf(html_file, pdf_file)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
