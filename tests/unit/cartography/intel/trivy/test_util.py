"""
Unit tests for cartography.intel.trivy.util module.

Tests the package normalization functions used for cross-tool matching
between Trivy and Syft.
"""

from cartography.intel.trivy.util import make_normalized_package_id
from cartography.intel.trivy.util import normalize_package_name
from cartography.intel.trivy.util import parse_purl


class TestParsePurl:
    """Tests for parse_purl function."""

    def test_parse_purl_with_namespace(self):
        result = parse_purl("pkg:deb/debian/gcc-12-base@12.2.0-14")
        assert result == {
            "type": "deb",
            "namespace": "debian",
            "name": "gcc-12-base",
            "version": "12.2.0-14",
        }

    def test_parse_purl_none_and_empty(self):
        assert parse_purl(None) is None
        assert parse_purl("") is None

    def test_parse_purl_invalid(self):
        assert parse_purl("npm/express@4.18.2") is None


class TestNormalizePackageName:
    """Tests for normalize_package_name function."""

    def test_normalize_python_pep503(self):
        """PEP 503: lowercase + replace runs of [._-] with single dash."""
        assert normalize_package_name("PyNaCl", "pypi") == "pynacl"
        assert normalize_package_name("jaraco.context", "pypi") == "jaraco-context"
        assert normalize_package_name("jaraco_context", "pypi") == "jaraco-context"
        assert normalize_package_name("foo._-bar", "python-pkg") == "foo-bar"

    def test_normalize_npm_lowercase(self):
        assert normalize_package_name("Express", "npm") == "express"
        assert normalize_package_name("body-parser", "npm") == "body-parser"

    def test_normalize_other_lowercase(self):
        assert normalize_package_name("GCC-12-Base", "deb") == "gcc-12-base"
        assert normalize_package_name("Package", "") == "package"


class TestMakeNormalizedPackageId:
    """Tests for make_normalized_package_id function."""

    def test_from_purl(self):
        assert (
            make_normalized_package_id(purl="pkg:npm/express@4.18.2")
            == "npm|express|4.18.2"
        )

    def test_from_purl_pypi_normalizes(self):
        assert (
            make_normalized_package_id(purl="pkg:pypi/PyNaCl@1.5.0")
            == "pypi|pynacl|1.5.0"
        )
        assert (
            make_normalized_package_id(purl="pkg:pypi/jaraco.context@4.3.0")
            == "pypi|jaraco-context|4.3.0"
        )

    def test_from_purl_includes_namespace(self):
        assert (
            make_normalized_package_id(
                purl="pkg:deb/debian/gcc-12-base@12.2.0-14?arch=amd64"
            )
            == "deb|debian/gcc-12-base|12.2.0-14"
        )

    def test_scoped_npm_vs_unscoped(self):
        scoped = make_normalized_package_id(purl="pkg:npm/%40types/node@18.0.0")
        unscoped = make_normalized_package_id(purl="pkg:npm/node@18.0.0")
        assert scoped == "npm|@types/node|18.0.0"
        assert unscoped == "npm|node|18.0.0"
        assert scoped != unscoped

    def test_fallback_to_components(self):
        result = make_normalized_package_id(
            name="Express", version="4.18.2", pkg_type="npm"
        )
        assert result == "npm|express|4.18.2"

    def test_purl_preferred_over_components(self):
        result = make_normalized_package_id(
            purl="pkg:npm/express@4.18.2",
            name="different-name",
            version="1.0.0",
            pkg_type="pypi",
        )
        assert result == "npm|express|4.18.2"

    def test_invalid_purl_falls_back(self):
        result = make_normalized_package_id(
            purl="invalid-purl",
            name="express",
            version="4.18.2",
            pkg_type="npm",
        )
        assert result == "npm|express|4.18.2"

    def test_missing_components_returns_none(self):
        assert make_normalized_package_id() is None
        assert make_normalized_package_id(name="express") is None
        assert make_normalized_package_id(name="express", version="4.18.2") is None
