#!/usr/bin/env python3
"""Generate QR code test fixtures.

This script generates QR code images for testing the QR detection functionality.
Run this script to create the fixture images in the current directory.

Usage:
    python generate_fixtures.py
"""

import sys
from pathlib import Path

try:
    import qrcode
except ImportError:
    print("Error: qrcode library not installed")
    print("Install with: pip install qrcode[pil]")
    sys.exit(1)


def generate_qr_code(data: str, filename: str, box_size: int = 10) -> None:
    """Generate a QR code image.

    Args:
        data: Data to encode in the QR code.
        filename: Output filename (without extension).
        box_size: Size of each box in pixels.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    output_path = Path(__file__).parent / f"{filename}.png"
    img.save(output_path)
    print(f"Generated: {output_path}")


def main():
    """Generate all QR code test fixtures."""
    fixtures = [
        # URL QR codes
        ("https://example.com", "url_qr"),
        ("https://www.example.org/recipe/chocolate-cake", "url_long_qr"),
        ("http://httpbin.org/html", "url_http_qr"),

        # Text QR codes
        ("Hello, World!", "text_qr"),
        ("This is a longer text message for QR code testing purposes.", "text_long_qr"),

        # Email QR codes
        ("mailto:test@example.com", "email_qr"),
        ("test@example.com", "email_plain_qr"),

        # Phone QR codes
        ("tel:+1234567890", "phone_qr"),

        # WiFi QR codes
        ("WIFI:T:WPA;S:MyNetwork;P:MyPassword;;", "wifi_qr"),

        # vCard QR codes
        (
            "BEGIN:VCARD\nVERSION:3.0\nFN:John Doe\nORG:Example Inc\nEND:VCARD",
            "vcard_qr"
        ),

        # Geo location QR codes
        ("geo:37.7749,-122.4194", "geo_qr"),

        # SMS QR codes
        ("sms:+1234567890?body=Hello", "sms_qr"),
    ]

    print("Generating QR code fixtures...")
    for data, filename in fixtures:
        generate_qr_code(data, filename)

    print(f"\nGenerated {len(fixtures)} QR code fixtures.")


if __name__ == "__main__":
    main()
