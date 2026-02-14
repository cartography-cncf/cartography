"""
Unit tests for cartography.intel.trivy.util module.

Tests the package normalization functions used for cross-tool matching
between Trivy and Syft.
"""

import pytest

from cartography.intel.trivy.util import make_normalized_package_id
from cartography.intel.trivy.util import normalize_package_name
from cartography.intel.trivy.util import parse_purl


class TestParsePurl:
    """Tests for parse_purl function."""

    def test_parse_purl_npm(self):
        """Test parsing npm PURL."""
        result = parse_purl("pkg:npm/express@4.18.2")
        assert result == {
            "type": "npm",
            "namespace": None,
            "name": "express",
            "version": "4.18.2",
        }

    def test_parse_purl_pypi(self):
        """Test parsing PyPI PURL."""
        result = parse_purl("pkg:pypi/requests@2.28.0")
        assert result == {
            "type": "pypi",
            "namespace": None,
            "name": "requests",
            "version": "2.28.0",
        }

    def test_parse_purl_deb_with_namespace(self):
        """Test parsing Debian PURL with namespace."""
        result = parse_purl("pkg:deb/debian/gcc-12-base@12.2.0-14")
        assert result == {
            "type": "deb",
            "namespace": "debian",
            "name": "gcc-12-base",
            "version": "12.2.0-14",
        }

    def test_parse_purl_with_qualifiers(self):
        """Test parsing PURL with qualifiers (should be stripped)."""
        result = parse_purl(
            "pkg:deb/debian/gcc-12-base@12.2.0-14?arch=amd64&distro=debian-12.8"
        )
        assert result == {
            "type": "deb",
            "namespace": "debian",
            "name": "gcc-12-base",
            "version": "12.2.0-14",
        }

    def test_parse_purl_url_encoded(self):
        """Test parsing PURL with URL-encoded characters."""
        # %2B is URL-encoded +
        result = parse_purl("pkg:deb/debian/krb5-locales@1.20.1-2%2Bdeb12u2")
        assert result == {
            "type": "deb",
            "namespace": "debian",
            "name": "krb5-locales",
            "version": "1.20.1-2+deb12u2",  # Decoded
        }

    def test_parse_purl_no_version(self):
        """Test parsing PURL without version."""
        result = parse_purl("pkg:npm/lodash")
        assert result == {
            "type": "npm",
            "namespace": None,
            "name": "lodash",
            "version": None,
        }

    def test_parse_purl_scoped_npm(self):
        """Test parsing scoped npm PURL (e.g., @types/node)."""
        result = parse_purl("pkg:npm/%40types/node@18.0.0")
        assert result == {
            "type": "npm",
            "namespace": "@types",
            "name": "node",
            "version": "18.0.0",
        }

    def test_parse_purl_invalid_no_prefix(self):
        """Test parsing invalid PURL without pkg: prefix."""
        result = parse_purl("npm/express@4.18.2")
        assert result is None

    def test_parse_purl_invalid_no_slash(self):
        """Test parsing invalid PURL without type separator."""
        result = parse_purl("pkg:express@4.18.2")
        assert result is None

    def test_parse_purl_empty(self):
        """Test parsing empty string."""
        result = parse_purl("")
        assert result is None

    def test_parse_purl_none(self):
        """Test parsing None."""
        result = parse_purl(None)
        assert result is None


class TestNormalizePackageName:
    """Tests for normalize_package_name function."""

    def test_normalize_python_lowercase(self):
        """Test Python package normalization - lowercase."""
        assert normalize_package_name("Requests", "python") == "requests"
        assert normalize_package_name("PyNaCl", "pypi") == "pynacl"

    def test_normalize_python_separators(self):
        """Test Python package normalization - PEP 503 separator handling."""
        # PEP 503: replace runs of [._-] with single dash
        assert normalize_package_name("jaraco.context", "pypi") == "jaraco-context"
        assert normalize_package_name("jaraco_context", "pypi") == "jaraco-context"
        assert normalize_package_name("jaraco-context", "pypi") == "jaraco-context"

    def test_normalize_python_multiple_separators(self):
        """Test Python package with multiple consecutive separators."""
        assert normalize_package_name("foo..bar", "pypi") == "foo-bar"
        assert normalize_package_name("foo__bar", "python") == "foo-bar"
        assert normalize_package_name("foo._-bar", "python-pkg") == "foo-bar"

    def test_normalize_npm_lowercase(self):
        """Test npm package normalization - lowercase only."""
        assert normalize_package_name("Express", "npm") == "express"
        assert normalize_package_name("LODASH", "node") == "lodash"

    def test_normalize_npm_preserves_separators(self):
        """Test npm package normalization - preserves separators."""
        # npm doesn't follow PEP 503, just lowercase
        assert normalize_package_name("body-parser", "npm") == "body-parser"
        assert normalize_package_name("Body_Parser", "node-pkg") == "body_parser"

    def test_normalize_deb_lowercase(self):
        """Test Debian package normalization - lowercase."""
        assert normalize_package_name("GCC-12-Base", "deb") == "gcc-12-base"

    def test_normalize_apk_lowercase(self):
        """Test Alpine package normalization - lowercase."""
        assert normalize_package_name("LibSSL", "apk") == "libssl"

    def test_normalize_unknown_type_lowercase(self):
        """Test unknown package type - defaults to lowercase."""
        assert normalize_package_name("MyPackage", "unknown") == "mypackage"

    def test_normalize_empty_type(self):
        """Test normalization with empty/None type."""
        assert normalize_package_name("Package", "") == "package"
        assert normalize_package_name("Package", None) == "package"


class TestMakeNormalizedPackageId:
    """Tests for make_normalized_package_id function."""

    def test_make_id_from_purl_npm(self):
        """Test creating ID from npm PURL."""
        result = make_normalized_package_id(purl="pkg:npm/express@4.18.2")
        assert result == "npm|express|4.18.2"

    def test_make_id_from_purl_pypi(self):
        """Test creating ID from PyPI PURL with normalization."""
        result = make_normalized_package_id(purl="pkg:pypi/PyNaCl@1.5.0")
        assert result == "pypi|pynacl|1.5.0"

    def test_make_id_from_purl_pypi_with_dots(self):
        """Test creating ID from PyPI PURL with dots in name."""
        result = make_normalized_package_id(purl="pkg:pypi/jaraco.context@4.3.0")
        assert result == "pypi|jaraco-context|4.3.0"

    def test_make_id_from_purl_deb(self):
        """Test creating ID from Debian PURL (includes namespace)."""
        result = make_normalized_package_id(
            purl="pkg:deb/debian/gcc-12-base@12.2.0-14?arch=amd64"
        )
        assert result == "deb|debian/gcc-12-base|12.2.0-14"

    def test_make_id_from_purl_scoped_npm(self):
        """Test scoped npm packages include namespace to avoid collisions."""
        scoped = make_normalized_package_id(purl="pkg:npm/%40types/node@18.0.0")
        unscoped = make_normalized_package_id(purl="pkg:npm/node@18.0.0")
        assert scoped == "npm|@types/node|18.0.0"
        assert unscoped == "npm|node|18.0.0"
        assert scoped != unscoped

    def test_make_id_from_components(self):
        """Test creating ID from individual components (fallback)."""
        result = make_normalized_package_id(
            name="Express",
            version="4.18.2",
            pkg_type="npm",
        )
        assert result == "npm|express|4.18.2"

    def test_make_id_from_components_pypi(self):
        """Test creating ID from PyPI components with normalization."""
        result = make_normalized_package_id(
            name="jaraco.context",
            version="4.3.0",
            pkg_type="pypi",
        )
        assert result == "pypi|jaraco-context|4.3.0"

    def test_make_id_purl_preferred_over_components(self):
        """Test that PURL is preferred over components when both provided."""
        result = make_normalized_package_id(
            purl="pkg:npm/express@4.18.2",
            name="different-name",
            version="1.0.0",
            pkg_type="pypi",
        )
        # PURL should take precedence
        assert result == "npm|express|4.18.2"

    def test_make_id_invalid_purl_falls_back_to_components(self):
        """Test fallback to components when PURL is invalid."""
        result = make_normalized_package_id(
            purl="invalid-purl",
            name="express",
            version="4.18.2",
            pkg_type="npm",
        )
        assert result == "npm|express|4.18.2"

    def test_make_id_purl_no_version_falls_back_to_components(self):
        """Test fallback when PURL has no version."""
        result = make_normalized_package_id(
            purl="pkg:npm/lodash",  # No version
            name="lodash",
            version="4.17.21",
            pkg_type="npm",
        )
        # Should fall back to components since PURL has no version
        assert result == "npm|lodash|4.17.21"

    def test_make_id_missing_required_components(self):
        """Test returns None when required components are missing."""
        assert make_normalized_package_id(name="express") is None
        assert make_normalized_package_id(version="4.18.2") is None
        assert make_normalized_package_id(pkg_type="npm") is None
        assert make_normalized_package_id(name="express", version="4.18.2") is None

    def test_make_id_empty_inputs(self):
        """Test returns None with no inputs."""
        assert make_normalized_package_id() is None


class TestCrossToolMatchingScenarios:
    """
    Integration-style tests verifying that Trivy and Syft would produce
    matching normalized IDs for the same package.
    """

    @pytest.mark.parametrize(
        "trivy_input,syft_input,expected_id",
        [
            # npm package - both tools report same format
            (
                {
                    "purl": "pkg:npm/express@4.18.2",
                    "name": "express",
                    "version": "4.18.2",
                    "pkg_type": "npm",
                },
                {
                    "purl": "pkg:npm/express@4.18.2",
                    "name": "express",
                    "version": "4.18.2",
                    "pkg_type": "npm",
                },
                "npm|express|4.18.2",
            ),
            # PyPI with case difference - PyNaCl vs pynacl
            (
                {
                    "purl": "pkg:pypi/PyNaCl@1.5.0",
                    "name": "PyNaCl",
                    "version": "1.5.0",
                    "pkg_type": "pypi",
                },
                {
                    "purl": "pkg:pypi/pynacl@1.5.0",
                    "name": "pynacl",
                    "version": "1.5.0",
                    "pkg_type": "pypi",
                },
                "pypi|pynacl|1.5.0",
            ),
            # PyPI with separator difference - jaraco.context vs jaraco-context
            (
                {
                    "purl": "pkg:pypi/jaraco.context@4.3.0",
                    "name": "jaraco.context",
                    "version": "4.3.0",
                    "pkg_type": "pypi",
                },
                {
                    "purl": "pkg:pypi/jaraco-context@4.3.0",
                    "name": "jaraco-context",
                    "version": "4.3.0",
                    "pkg_type": "pypi",
                },
                "pypi|jaraco-context|4.3.0",
            ),
            # Debian package with namespace
            (
                {
                    "purl": "pkg:deb/debian/libssl3@3.0.11-1",
                    "name": "libssl3",
                    "version": "3.0.11-1",
                    "pkg_type": "deb",
                },
                {
                    "purl": "pkg:deb/debian/libssl3@3.0.11-1",
                    "name": "libssl3",
                    "version": "3.0.11-1",
                    "pkg_type": "deb",
                },
                "deb|debian/libssl3|3.0.11-1",
            ),
        ],
    )
    def test_trivy_syft_produce_matching_ids(
        self, trivy_input, syft_input, expected_id
    ):
        """Verify Trivy and Syft inputs produce the same normalized ID."""
        trivy_id = make_normalized_package_id(**trivy_input)
        syft_id = make_normalized_package_id(**syft_input)

        assert trivy_id == expected_id
        assert syft_id == expected_id
        assert trivy_id == syft_id
