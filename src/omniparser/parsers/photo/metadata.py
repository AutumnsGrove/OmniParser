"""
EXIF metadata extraction for photo files.

This module provides comprehensive EXIF metadata extraction from image files,
including camera information, GPS coordinates, timestamps, and more.

Uses PIL/Pillow for EXIF parsing with fallback handling for missing data.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS

logger = logging.getLogger(__name__)


@dataclass
class GPSInfo:
    """GPS coordinate information extracted from photo EXIF.

    Attributes:
        latitude: Decimal latitude (-90 to 90).
        longitude: Decimal longitude (-180 to 180).
        altitude: Altitude in meters above sea level.
        altitude_ref: Altitude reference (0=above sea level, 1=below).
        timestamp: GPS timestamp if available.
        map_datum: GPS map datum (usually WGS-84).
    """

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    altitude_ref: Optional[int] = None
    timestamp: Optional[datetime] = None
    map_datum: Optional[str] = None

    def to_decimal_string(self) -> Optional[str]:
        """Format coordinates as decimal string.

        Returns:
            String like "40.7128, -74.0060" or None if no coordinates.
        """
        if self.latitude is not None and self.longitude is not None:
            return f"{self.latitude:.6f}, {self.longitude:.6f}"
        return None

    def to_dms_string(self) -> Optional[str]:
        """Format coordinates as degrees/minutes/seconds string.

        Returns:
            String like "40°42'46.1\"N 74°0'21.6\"W" or None if no coordinates.
        """
        if self.latitude is None or self.longitude is None:
            return None

        def decimal_to_dms(decimal: float) -> Tuple[int, int, float]:
            degrees = int(abs(decimal))
            minutes_float = (abs(decimal) - degrees) * 60
            minutes = int(minutes_float)
            seconds = (minutes_float - minutes) * 60
            return degrees, minutes, seconds

        lat_d, lat_m, lat_s = decimal_to_dms(self.latitude)
        lon_d, lon_m, lon_s = decimal_to_dms(self.longitude)

        lat_dir = "N" if self.latitude >= 0 else "S"
        lon_dir = "E" if self.longitude >= 0 else "W"

        return f"{lat_d}°{lat_m}'{lat_s:.1f}\"{lat_dir} {lon_d}°{lon_m}'{lon_s:.1f}\"{lon_dir}"


@dataclass
class CameraInfo:
    """Camera and lens information from EXIF.

    Attributes:
        make: Camera manufacturer (e.g., "Canon", "Nikon").
        model: Camera model (e.g., "EOS 5D Mark IV").
        lens_make: Lens manufacturer.
        lens_model: Lens model name.
        serial_number: Camera serial number if available.
        software: Software used to process image.
        firmware: Camera firmware version.
    """

    make: Optional[str] = None
    model: Optional[str] = None
    lens_make: Optional[str] = None
    lens_model: Optional[str] = None
    serial_number: Optional[str] = None
    software: Optional[str] = None
    firmware: Optional[str] = None


@dataclass
class ExposureInfo:
    """Exposure and shooting settings from EXIF.

    Attributes:
        aperture: F-number (e.g., 2.8).
        shutter_speed: Shutter speed as string (e.g., "1/250").
        shutter_speed_value: Shutter speed in seconds as float.
        iso: ISO sensitivity.
        exposure_bias: Exposure compensation in EV.
        exposure_mode: Exposure mode (auto, manual, etc.).
        exposure_program: Exposure program (portrait, landscape, etc.).
        metering_mode: Metering mode used.
        flash: Flash information.
        flash_fired: Whether flash was fired.
        focal_length: Focal length in mm.
        focal_length_35mm: 35mm equivalent focal length.
        white_balance: White balance mode.
    """

    aperture: Optional[float] = None
    shutter_speed: Optional[str] = None
    shutter_speed_value: Optional[float] = None
    iso: Optional[int] = None
    exposure_bias: Optional[float] = None
    exposure_mode: Optional[str] = None
    exposure_program: Optional[str] = None
    metering_mode: Optional[str] = None
    flash: Optional[str] = None
    flash_fired: Optional[bool] = None
    focal_length: Optional[float] = None
    focal_length_35mm: Optional[int] = None
    white_balance: Optional[str] = None


@dataclass
class PhotoMetadata:
    """Complete metadata extracted from a photo file.

    Attributes:
        file_path: Path to the image file.
        file_name: Name of the image file.
        file_size: File size in bytes.
        width: Image width in pixels.
        height: Image height in pixels.
        format: Image format (JPEG, PNG, etc.).
        mode: Color mode (RGB, RGBA, L, etc.).
        date_taken: Date/time photo was taken.
        date_modified: Date/time file was modified.
        date_digitized: Date/time photo was digitized.
        orientation: EXIF orientation value (1-8).
        camera: Camera information.
        exposure: Exposure settings.
        gps: GPS coordinates.
        copyright: Copyright information.
        artist: Photographer/artist name.
        description: Image description/caption from EXIF.
        user_comment: User comment from EXIF.
        rating: Image rating (0-5).
        keywords: Keywords/tags if embedded.
        raw_exif: Complete raw EXIF data dictionary.
    """

    file_path: str
    file_name: str
    file_size: int
    width: int
    height: int
    format: str
    mode: str
    date_taken: Optional[datetime] = None
    date_modified: Optional[datetime] = None
    date_digitized: Optional[datetime] = None
    orientation: Optional[int] = None
    camera: CameraInfo = field(default_factory=CameraInfo)
    exposure: ExposureInfo = field(default_factory=ExposureInfo)
    gps: GPSInfo = field(default_factory=GPSInfo)
    copyright: Optional[str] = None
    artist: Optional[str] = None
    description: Optional[str] = None
    user_comment: Optional[str] = None
    rating: Optional[int] = None
    keywords: List[str] = field(default_factory=list)
    raw_exif: Dict[str, Any] = field(default_factory=dict)

    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio (width/height)."""
        return self.width / self.height if self.height > 0 else 0

    @property
    def megapixels(self) -> float:
        """Calculate megapixels."""
        return (self.width * self.height) / 1_000_000

    @property
    def orientation_description(self) -> str:
        """Get human-readable orientation description."""
        orientations = {
            1: "Normal",
            2: "Mirrored horizontal",
            3: "Rotated 180°",
            4: "Mirrored vertical",
            5: "Mirrored horizontal, rotated 270° CW",
            6: "Rotated 90° CW",
            7: "Mirrored horizontal, rotated 90° CW",
            8: "Rotated 270° CW",
        }
        return orientations.get(self.orientation or 1, "Unknown")


def extract_photo_metadata(file_path: Union[Path, str]) -> PhotoMetadata:
    """Extract comprehensive metadata from a photo file.

    Args:
        file_path: Path to the image file.

    Returns:
        PhotoMetadata object with all extracted information.

    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If file is not a valid image.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {file_path}")

    try:
        with Image.open(path) as img:
            # Basic file info
            file_stat = path.stat()

            metadata = PhotoMetadata(
                file_path=str(path.absolute()),
                file_name=path.name,
                file_size=file_stat.st_size,
                width=img.width,
                height=img.height,
                format=img.format or path.suffix.lstrip(".").upper(),
                mode=img.mode,
            )

            # Extract EXIF data
            exif_data = _extract_exif_dict(img)
            if exif_data:
                metadata.raw_exif = exif_data
                _populate_metadata_from_exif(metadata, exif_data)

            return metadata

    except Exception as e:
        logger.error(f"Failed to extract metadata from {file_path}: {e}")
        raise ValueError(f"Failed to read image file: {e}")


def _extract_exif_dict(img: Image.Image) -> Dict[str, Any]:
    """Extract EXIF data as a dictionary with human-readable keys.

    Args:
        img: PIL Image object.

    Returns:
        Dictionary of EXIF tag names to values.
    """
    exif_dict: Dict[str, Any] = {}

    try:
        exif_raw = img._getexif()  # type: ignore[attr-defined]
        if not exif_raw:
            return exif_dict

        for tag_id, value in exif_raw.items():
            tag_name = TAGS.get(tag_id, str(tag_id))

            # Handle GPS info specially
            if tag_name == "GPSInfo" and isinstance(value, dict):
                gps_data = {}
                for gps_tag_id, gps_value in value.items():
                    gps_tag_name = GPSTAGS.get(gps_tag_id, str(gps_tag_id))
                    gps_data[gps_tag_name] = gps_value
                exif_dict[tag_name] = gps_data
            else:
                # Convert bytes to string if possible
                if isinstance(value, bytes):
                    try:
                        value = value.decode("utf-8", errors="ignore").strip("\x00")
                    except Exception:
                        value = str(value)
                exif_dict[tag_name] = value

    except Exception as e:
        logger.debug(f"Error extracting EXIF: {e}")

    return exif_dict


def _populate_metadata_from_exif(
    metadata: PhotoMetadata, exif: Dict[str, Any]
) -> None:
    """Populate PhotoMetadata fields from EXIF dictionary.

    Args:
        metadata: PhotoMetadata object to populate.
        exif: EXIF dictionary with tag names as keys.
    """
    # Date/time fields
    metadata.date_taken = _parse_exif_datetime(exif.get("DateTimeOriginal"))
    metadata.date_modified = _parse_exif_datetime(exif.get("DateTime"))
    metadata.date_digitized = _parse_exif_datetime(exif.get("DateTimeDigitized"))

    # Orientation
    metadata.orientation = exif.get("Orientation")

    # Camera info
    metadata.camera.make = _clean_string(exif.get("Make"))
    metadata.camera.model = _clean_string(exif.get("Model"))
    metadata.camera.lens_make = _clean_string(exif.get("LensMake"))
    metadata.camera.lens_model = _clean_string(exif.get("LensModel"))
    metadata.camera.serial_number = _clean_string(exif.get("BodySerialNumber"))
    metadata.camera.software = _clean_string(exif.get("Software"))

    # Exposure info
    metadata.exposure.aperture = _get_float_from_ratio(exif.get("FNumber"))
    metadata.exposure.shutter_speed = _format_shutter_speed(
        exif.get("ExposureTime")
    )
    metadata.exposure.shutter_speed_value = _get_float_from_ratio(
        exif.get("ExposureTime")
    )
    metadata.exposure.iso = exif.get("ISOSpeedRatings")
    if isinstance(metadata.exposure.iso, tuple):
        metadata.exposure.iso = metadata.exposure.iso[0]
    metadata.exposure.exposure_bias = _get_float_from_ratio(
        exif.get("ExposureBiasValue")
    )
    metadata.exposure.focal_length = _get_float_from_ratio(exif.get("FocalLength"))
    metadata.exposure.focal_length_35mm = exif.get("FocalLengthIn35mmFilm")
    metadata.exposure.metering_mode = _decode_metering_mode(exif.get("MeteringMode"))
    metadata.exposure.exposure_mode = _decode_exposure_mode(exif.get("ExposureMode"))
    metadata.exposure.exposure_program = _decode_exposure_program(
        exif.get("ExposureProgram")
    )
    metadata.exposure.white_balance = _decode_white_balance(exif.get("WhiteBalance"))
    metadata.exposure.flash = _decode_flash(exif.get("Flash"))
    if exif.get("Flash") is not None:
        metadata.exposure.flash_fired = bool(exif.get("Flash", 0) & 1)

    # Copyright and artist
    metadata.copyright = _clean_string(exif.get("Copyright"))
    metadata.artist = _clean_string(exif.get("Artist"))

    # Description and comments
    metadata.description = _clean_string(exif.get("ImageDescription"))
    metadata.user_comment = _extract_user_comment(exif.get("UserComment"))

    # Rating
    metadata.rating = exif.get("Rating")

    # GPS data
    gps_info = exif.get("GPSInfo", {})
    if gps_info:
        _populate_gps_info(metadata.gps, gps_info)


def _populate_gps_info(gps: GPSInfo, gps_data: Dict[str, Any]) -> None:
    """Populate GPSInfo from GPS EXIF data.

    Args:
        gps: GPSInfo object to populate.
        gps_data: GPS EXIF dictionary.
    """
    # Latitude
    lat = gps_data.get("GPSLatitude")
    lat_ref = gps_data.get("GPSLatitudeRef", "N")
    if lat:
        gps.latitude = _convert_gps_to_decimal(lat, lat_ref)

    # Longitude
    lon = gps_data.get("GPSLongitude")
    lon_ref = gps_data.get("GPSLongitudeRef", "E")
    if lon:
        gps.longitude = _convert_gps_to_decimal(lon, lon_ref)

    # Altitude
    alt = gps_data.get("GPSAltitude")
    if alt:
        gps.altitude = _get_float_from_ratio(alt)
        gps.altitude_ref = gps_data.get("GPSAltitudeRef", 0)

    # Map datum
    gps.map_datum = gps_data.get("GPSMapDatum")


def _convert_gps_to_decimal(
    coords: Tuple[Any, ...], ref: str
) -> Optional[float]:
    """Convert GPS coordinates from degrees/minutes/seconds to decimal.

    Args:
        coords: Tuple of (degrees, minutes, seconds).
        ref: Reference direction (N/S/E/W).

    Returns:
        Decimal coordinate value.
    """
    try:
        degrees = _get_float_from_ratio(coords[0])
        minutes = _get_float_from_ratio(coords[1])
        seconds = _get_float_from_ratio(coords[2])

        if degrees is None or minutes is None or seconds is None:
            return None

        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

        if ref in ("S", "W"):
            decimal = -decimal

        return decimal
    except Exception:
        return None


def _get_float_from_ratio(value: Any) -> Optional[float]:
    """Extract float from various EXIF ratio formats.

    Args:
        value: EXIF value (IFDRational, tuple, float, etc.).

    Returns:
        Float value or None.
    """
    if value is None:
        return None

    try:
        # Handle IFDRational (has numerator/denominator)
        if hasattr(value, "numerator") and hasattr(value, "denominator"):
            if value.denominator == 0:
                return None
            return float(value.numerator) / float(value.denominator)

        # Handle tuple (numerator, denominator)
        if isinstance(value, tuple) and len(value) == 2:
            if value[1] == 0:
                return None
            return float(value[0]) / float(value[1])

        # Direct conversion
        return float(value)
    except (ValueError, TypeError, ZeroDivisionError):
        return None


def _format_shutter_speed(value: Any) -> Optional[str]:
    """Format shutter speed as human-readable string.

    Args:
        value: EXIF exposure time value.

    Returns:
        String like "1/250" or "2.5s".
    """
    speed = _get_float_from_ratio(value)
    if speed is None:
        return None

    if speed >= 1:
        return f"{speed}s"
    else:
        # Format as fraction
        denominator = round(1 / speed)
        return f"1/{denominator}"


def _parse_exif_datetime(value: Any) -> Optional[datetime]:
    """Parse EXIF datetime string.

    Args:
        value: EXIF datetime string in format "YYYY:MM:DD HH:MM:SS".

    Returns:
        datetime object or None.
    """
    if not value or not isinstance(value, str):
        return None

    try:
        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        try:
            # Try without time
            return datetime.strptime(value.split()[0], "%Y:%m:%d")
        except ValueError:
            return None


def _clean_string(value: Any) -> Optional[str]:
    """Clean string value from EXIF.

    Args:
        value: EXIF string value.

    Returns:
        Cleaned string or None.
    """
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    value = str(value).strip().strip("\x00")
    return value if value else None


def _extract_user_comment(value: Any) -> Optional[str]:
    """Extract user comment, handling encoding prefix.

    Args:
        value: EXIF UserComment value.

    Returns:
        Cleaned comment string or None.
    """
    if not value:
        return None

    if isinstance(value, bytes):
        # UserComment often has 8-byte encoding prefix
        if len(value) > 8:
            # Check for common encoding prefixes
            if value.startswith(b"UNICODE\x00"):
                try:
                    return value[8:].decode("utf-16").strip("\x00")
                except Exception:
                    pass
            elif value.startswith(b"ASCII\x00\x00\x00"):
                return value[8:].decode("ascii", errors="ignore").strip("\x00")

        try:
            return value.decode("utf-8", errors="ignore").strip("\x00")
        except Exception:
            return None

    return _clean_string(value)


def _decode_metering_mode(value: Any) -> Optional[str]:
    """Decode metering mode EXIF value."""
    modes = {
        0: "Unknown",
        1: "Average",
        2: "Center-weighted average",
        3: "Spot",
        4: "Multi-spot",
        5: "Pattern",
        6: "Partial",
        255: "Other",
    }
    return modes.get(value)


def _decode_exposure_mode(value: Any) -> Optional[str]:
    """Decode exposure mode EXIF value."""
    modes = {
        0: "Auto",
        1: "Manual",
        2: "Auto bracket",
    }
    return modes.get(value)


def _decode_exposure_program(value: Any) -> Optional[str]:
    """Decode exposure program EXIF value."""
    programs = {
        0: "Not defined",
        1: "Manual",
        2: "Normal program",
        3: "Aperture priority",
        4: "Shutter priority",
        5: "Creative program",
        6: "Action program",
        7: "Portrait mode",
        8: "Landscape mode",
    }
    return programs.get(value)


def _decode_white_balance(value: Any) -> Optional[str]:
    """Decode white balance EXIF value."""
    modes = {
        0: "Auto",
        1: "Manual",
    }
    return modes.get(value)


def _decode_flash(value: Any) -> Optional[str]:
    """Decode flash EXIF value."""
    if value is None:
        return None

    flash_modes = {
        0x0: "No flash",
        0x1: "Flash fired",
        0x5: "Flash fired, strobe return not detected",
        0x7: "Flash fired, strobe return detected",
        0x9: "Flash fired, compulsory",
        0xD: "Flash fired, compulsory, return not detected",
        0xF: "Flash fired, compulsory, return detected",
        0x10: "Flash did not fire, compulsory",
        0x18: "Flash did not fire, auto",
        0x19: "Flash fired, auto",
        0x1D: "Flash fired, auto, return not detected",
        0x1F: "Flash fired, auto, return detected",
        0x20: "No flash function",
        0x41: "Flash fired, red-eye reduction",
        0x45: "Flash fired, red-eye reduction, return not detected",
        0x47: "Flash fired, red-eye reduction, return detected",
        0x49: "Flash fired, compulsory, red-eye reduction",
        0x4D: "Flash fired, compulsory, red-eye reduction, return not detected",
        0x4F: "Flash fired, compulsory, red-eye reduction, return detected",
        0x59: "Flash fired, auto, red-eye reduction",
        0x5D: "Flash fired, auto, red-eye reduction, return not detected",
        0x5F: "Flash fired, auto, red-eye reduction, return detected",
    }
    return flash_modes.get(value, f"Unknown ({value})")
