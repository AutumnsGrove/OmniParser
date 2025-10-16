"""Tests for exception classes."""

import pytest
from src.omniparser.exceptions import (
    OmniparserError,
    UnsupportedFormatError,
    ParsingError,
    FileReadError,
    NetworkError,
    ValidationError,
)


class TestOmniparserError:
    """Tests for OmniparserError base exception."""

    def test_can_be_raised(self):
        """Test that OmniparserError can be raised."""
        with pytest.raises(OmniparserError):
            raise OmniparserError("Test error")

    def test_inherits_from_exception(self):
        """Test that OmniparserError inherits from Exception."""
        assert issubclass(OmniparserError, Exception)

    def test_error_message_preserved(self):
        """Test that error message is preserved."""
        msg = "This is a test error"
        with pytest.raises(OmniparserError, match=msg):
            raise OmniparserError(msg)

    def test_can_be_caught_as_exception(self):
        """Test that OmniparserError can be caught as Exception."""
        try:
            raise OmniparserError("Test")
        except Exception as e:
            assert isinstance(e, OmniparserError)


class TestUnsupportedFormatError:
    """Tests for UnsupportedFormatError."""

    def test_can_be_raised(self):
        """Test that UnsupportedFormatError can be raised."""
        with pytest.raises(UnsupportedFormatError):
            raise UnsupportedFormatError("Unsupported format: .xyz")

    def test_inherits_from_omniparser_error(self):
        """Test proper inheritance."""
        assert issubclass(UnsupportedFormatError, OmniparserError)

    def test_message_preserved(self):
        """Test that error message is preserved."""
        msg = "Format .xyz is not supported"
        with pytest.raises(UnsupportedFormatError, match=msg):
            raise UnsupportedFormatError(msg)

    def test_can_be_caught_as_omniparser_error(self):
        """Test that UnsupportedFormatError can be caught as OmniparserError."""
        try:
            raise UnsupportedFormatError("Test")
        except OmniparserError as e:
            assert isinstance(e, UnsupportedFormatError)


class TestParsingError:
    """Tests for ParsingError."""

    def test_can_be_raised(self):
        """Test that ParsingError can be raised."""
        with pytest.raises(ParsingError):
            raise ParsingError("Parsing failed")

    def test_inherits_from_omniparser_error(self):
        """Test proper inheritance."""
        assert issubclass(ParsingError, OmniparserError)

    def test_stores_parser_name(self):
        """Test that parser name is stored."""
        error = ParsingError("Failed", parser="epub")
        assert error.parser == "epub"

    def test_stores_original_error(self):
        """Test that original error is stored."""
        original = ValueError("Bad value")
        error = ParsingError("Failed", original_error=original)
        assert error.original_error is original

    def test_optional_attributes_default_none(self):
        """Test that optional attributes default to None."""
        error = ParsingError("Failed")
        assert error.parser is None
        assert error.original_error is None

    def test_message_preserved(self):
        """Test that error message is preserved."""
        msg = "Parsing failed at line 42"
        with pytest.raises(ParsingError, match=msg):
            raise ParsingError(msg)

    def test_all_attributes_stored(self):
        """Test that all attributes are stored correctly."""
        original = IOError("File corrupted")
        error = ParsingError("Failed to parse", parser="pdf", original_error=original)
        assert str(error) == "Failed to parse"
        assert error.parser == "pdf"
        assert error.original_error is original

    def test_can_be_caught_as_omniparser_error(self):
        """Test that ParsingError can be caught as OmniparserError."""
        try:
            raise ParsingError("Test", parser="epub")
        except OmniparserError as e:
            assert isinstance(e, ParsingError)
            assert e.parser == "epub"


class TestFileReadError:
    """Tests for FileReadError."""

    def test_can_be_raised(self):
        """Test that FileReadError can be raised."""
        with pytest.raises(FileReadError):
            raise FileReadError("File not found")

    def test_inherits_from_omniparser_error(self):
        """Test proper inheritance."""
        assert issubclass(FileReadError, OmniparserError)

    def test_message_preserved(self):
        """Test that error message is preserved."""
        msg = "Cannot read file: permission denied"
        with pytest.raises(FileReadError, match=msg):
            raise FileReadError(msg)

    def test_can_be_caught_as_omniparser_error(self):
        """Test that FileReadError can be caught as OmniparserError."""
        try:
            raise FileReadError("Test")
        except OmniparserError as e:
            assert isinstance(e, FileReadError)


class TestNetworkError:
    """Tests for NetworkError."""

    def test_can_be_raised(self):
        """Test that NetworkError can be raised."""
        with pytest.raises(NetworkError):
            raise NetworkError("Connection failed")

    def test_inherits_from_omniparser_error(self):
        """Test proper inheritance."""
        assert issubclass(NetworkError, OmniparserError)

    def test_message_preserved(self):
        """Test that error message is preserved."""
        msg = "Connection timeout: https://example.com"
        with pytest.raises(NetworkError, match=msg):
            raise NetworkError(msg)

    def test_can_be_caught_as_omniparser_error(self):
        """Test that NetworkError can be caught as OmniparserError."""
        try:
            raise NetworkError("Test")
        except OmniparserError as e:
            assert isinstance(e, NetworkError)


class TestValidationError:
    """Tests for ValidationError."""

    def test_can_be_raised(self):
        """Test that ValidationError can be raised."""
        with pytest.raises(ValidationError):
            raise ValidationError("Invalid input")

    def test_inherits_from_omniparser_error(self):
        """Test proper inheritance."""
        assert issubclass(ValidationError, OmniparserError)

    def test_message_preserved(self):
        """Test that error message is preserved."""
        msg = "Invalid file path: must be absolute"
        with pytest.raises(ValidationError, match=msg):
            raise ValidationError(msg)

    def test_can_be_caught_as_omniparser_error(self):
        """Test that ValidationError can be caught as OmniparserError."""
        try:
            raise ValidationError("Test")
        except OmniparserError as e:
            assert isinstance(e, ValidationError)


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_all_exceptions_catchable_as_omniparser_error(self):
        """Test that all exceptions can be caught as OmniparserError."""
        exceptions = [
            UnsupportedFormatError("test"),
            ParsingError("test"),
            FileReadError("test"),
            NetworkError("test"),
            ValidationError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, OmniparserError)

    def test_all_exceptions_catchable_as_exception(self):
        """Test that all exceptions can be caught as base Exception."""
        exceptions = [
            OmniparserError("test"),
            UnsupportedFormatError("test"),
            ParsingError("test"),
            FileReadError("test"),
            NetworkError("test"),
            ValidationError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, Exception)

    def test_specific_exceptions_not_related(self):
        """Test that specific exception types are not instances of each other."""
        unsupported = UnsupportedFormatError("test")
        parsing = ParsingError("test")
        file_read = FileReadError("test")
        network = NetworkError("test")
        validation = ValidationError("test")

        # UnsupportedFormatError is not other types
        assert not isinstance(unsupported, ParsingError)
        assert not isinstance(unsupported, FileReadError)
        assert not isinstance(unsupported, NetworkError)
        assert not isinstance(unsupported, ValidationError)

        # ParsingError is not other types
        assert not isinstance(parsing, UnsupportedFormatError)
        assert not isinstance(parsing, FileReadError)
        assert not isinstance(parsing, NetworkError)
        assert not isinstance(parsing, ValidationError)

        # FileReadError is not other types
        assert not isinstance(file_read, UnsupportedFormatError)
        assert not isinstance(file_read, ParsingError)
        assert not isinstance(file_read, NetworkError)
        assert not isinstance(file_read, ValidationError)

        # NetworkError is not other types
        assert not isinstance(network, UnsupportedFormatError)
        assert not isinstance(network, ParsingError)
        assert not isinstance(network, FileReadError)
        assert not isinstance(network, ValidationError)

        # ValidationError is not other types
        assert not isinstance(validation, UnsupportedFormatError)
        assert not isinstance(validation, ParsingError)
        assert not isinstance(validation, FileReadError)
        assert not isinstance(validation, NetworkError)

    def test_exception_hierarchy_depth(self):
        """Test that exception hierarchy has correct depth."""
        # All specific exceptions are 2 levels deep: Exception -> OmniparserError -> Specific
        exceptions = [
            UnsupportedFormatError,
            ParsingError,
            FileReadError,
            NetworkError,
            ValidationError,
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, OmniparserError)
            assert issubclass(exc_class, Exception)
            assert issubclass(OmniparserError, Exception)


class TestExceptionUsagePatterns:
    """Tests for common exception usage patterns."""

    def test_selective_exception_handling(self):
        """Test handling specific exceptions while letting others propagate."""

        def risky_operation(error_type: str):
            if error_type == "unsupported":
                raise UnsupportedFormatError("Format not supported")
            elif error_type == "parsing":
                raise ParsingError("Parse failed")
            elif error_type == "file":
                raise FileReadError("Cannot read")

        # Catch only UnsupportedFormatError
        with pytest.raises(ParsingError):
            try:
                risky_operation("parsing")
            except UnsupportedFormatError:
                pass  # This won't catch ParsingError

        # Catch multiple specific types
        caught = None
        try:
            risky_operation("file")
        except (UnsupportedFormatError, FileReadError) as e:
            caught = e

        assert isinstance(caught, FileReadError)

    def test_catch_all_omniparser_errors(self):
        """Test catching all Omniparser errors with base exception."""
        errors_caught = []

        for error in [
            UnsupportedFormatError("test"),
            ParsingError("test"),
            FileReadError("test"),
            NetworkError("test"),
            ValidationError("test"),
        ]:
            try:
                raise error
            except OmniparserError as e:
                errors_caught.append(type(e).__name__)

        assert len(errors_caught) == 5
        assert "UnsupportedFormatError" in errors_caught
        assert "ParsingError" in errors_caught
        assert "FileReadError" in errors_caught
        assert "NetworkError" in errors_caught
        assert "ValidationError" in errors_caught

    def test_reraise_with_additional_context(self):
        """Test re-raising exceptions with additional context."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise ParsingError("Failed to parse", parser="epub", original_error=e)
        except ParsingError as e:
            assert e.parser == "epub"
            assert isinstance(e.original_error, ValueError)
            assert str(e.original_error) == "Original error"

    def test_exception_str_representation(self):
        """Test string representation of exceptions."""
        error = ParsingError("Document is malformed")
        assert str(error) == "Document is malformed"

        error_with_context = ParsingError(
            "Failed at chapter 3", parser="epub", original_error=ValueError("Bad XML")
        )
        assert "Failed at chapter 3" in str(error_with_context)
