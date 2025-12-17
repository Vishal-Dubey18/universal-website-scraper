"""
tests/test_utils.py - Unit tests for utility functions
"""
import pytest
from backend.scraper.utils import (
    is_valid_url,
    clean_url,
    make_absolute_url,
    truncate_text,
    extract_domain,
    is_same_domain,
    sanitize_text,
)


class TestURLValidation:
    """Test URL validation functions"""
    
    def test_is_valid_url_with_http(self):
        """Valid HTTP URLs should pass"""
        assert is_valid_url("http://example.com") is True
    
    def test_is_valid_url_with_https(self):
        """Valid HTTPS URLs should pass"""
        assert is_valid_url("https://example.com") is True
    
    def test_is_valid_url_without_scheme(self):
        """URLs without scheme should fail"""
        assert is_valid_url("example.com") is False
    
    def test_is_valid_url_invalid_scheme(self):
        """URLs with invalid schemes should fail"""
        assert is_valid_url("ftp://example.com") is False
    
    def test_is_valid_url_empty_string(self):
        """Empty string should fail"""
        assert is_valid_url("") is False


class TestURLCleaning:
    """Test URL cleaning functions"""
    
    def test_clean_url_with_scheme(self):
        """URL with scheme should not be modified"""
        assert clean_url("https://example.com/path") == "https://example.com/path"
    
    def test_clean_url_without_scheme(self):
        """URL without scheme should add https://"""
        assert clean_url("example.com") == "https://example.com"
    
    def test_clean_url_trailing_slash(self):
        """Trailing slashes should be removed"""
        assert clean_url("https://example.com/") == "https://example.com"
    
    def test_clean_url_with_whitespace(self):
        """Leading/trailing whitespace should be stripped"""
        assert clean_url("  https://example.com  ") == "https://example.com"


class TestAbsoluteURLs:
    """Test absolute URL conversion"""
    
    def test_make_absolute_url_relative(self):
        """Relative URLs should be converted to absolute"""
        result = make_absolute_url("/page", "https://example.com")
        assert result == "https://example.com/page"
    
    def test_make_absolute_url_already_absolute(self):
        """Already absolute URLs should be returned as-is"""
        assert make_absolute_url("https://other.com", "https://example.com") == "https://other.com"
    
    def test_make_absolute_url_protocol_relative(self):
        """Protocol-relative URLs should get https:"""
        result = make_absolute_url("//cdn.example.com/img.jpg", "https://example.com")
        assert result.startswith("https://")


class TestTextProcessing:
    """Test text processing functions"""
    
    def test_truncate_text_no_truncation_needed(self):
        """Short text should not be truncated"""
        text, truncated = truncate_text("hello", 100)
        assert text == "hello"
        assert truncated is False
    
    def test_truncate_text_truncation_needed(self):
        """Long text should be truncated"""
        text, truncated = truncate_text("hello world", 5)
        assert truncated is True
        assert "..." in text
    
    def test_sanitize_text_multiple_spaces(self):
        """Multiple spaces should be collapsed"""
        result = sanitize_text("hello   world")
        assert result == "hello world"
    
    def test_sanitize_text_newlines(self):
        """Newlines should be replaced with spaces"""
        result = sanitize_text("hello\nworld")
        assert result == "hello world"
    
    def test_sanitize_text_empty_string(self):
        """Empty string should return empty string"""
        assert sanitize_text("") == ""


class TestDomainExtraction:
    """Test domain extraction functions"""
    
    def test_extract_domain_simple(self):
        """Simple domains should be extracted"""
        assert extract_domain("https://example.com/path") == "example.com"
    
    def test_extract_domain_with_subdomain(self):
        """Subdomains should be extracted"""
        assert extract_domain("https://sub.example.com") == "sub.example.com"
    
    def test_is_same_domain_identical(self):
        """Identical domains should match"""
        assert is_same_domain("https://example.com/a", "https://example.com/b") is True
    
    def test_is_same_domain_www_variant(self):
        """www variants should match"""
        assert is_same_domain("https://www.example.com", "https://example.com") is True
    
    def test_is_same_domain_different(self):
        """Different domains should not match"""
        assert is_same_domain("https://example.com", "https://other.com") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
