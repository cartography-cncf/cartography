"""Unit tests for SBOM parser functions."""

from cartography.intel.sbom.parser import extract_name_version_from_purl
from cartography.intel.sbom.parser import make_trivy_package_id
from cartography.intel.sbom.parser import transform_sbom_dependencies
from cartography.intel.sbom.parser import validate_cyclonedx_sbom
from tests.data.sbom.cyclonedx_sample import CYCLONEDX_SBOM_SAMPLE
from tests.data.sbom.cyclonedx_sample import EXPECTED_DEPENDENCY_RELS
from tests.data.sbom.cyclonedx_sample import INVALID_SBOM_MISSING_FORMAT
from tests.data.sbom.cyclonedx_sample import INVALID_SBOM_WRONG_FORMAT
from tests.data.sbom.cyclonedx_sample import MINIMAL_SBOM


class TestMakeTrivyPackageId:
    """Tests for make_trivy_package_id function."""

    def test_basic_id(self):
        """Test basic ID generation."""
        assert make_trivy_package_id("lodash", "4.17.21") == "4.17.21|lodash"

    def test_complex_version(self):
        """Test with complex version string."""
        assert (
            make_trivy_package_id("openssl", "1.1.1k-1+deb11u1")
            == "1.1.1k-1+deb11u1|openssl"
        )

    def test_namespaced_package(self):
        """Test with package name containing special chars."""
        assert make_trivy_package_id("@types/node", "18.0.0") == "18.0.0|@types/node"


class TestExtractNameVersionFromPurl:
    """Tests for extract_name_version_from_purl function."""

    def test_npm_purl(self):
        """Test npm purl extraction."""
        result = extract_name_version_from_purl("pkg:npm/lodash@4.17.21")
        assert result == ("lodash", "4.17.21")

    def test_purl_with_qualifiers(self):
        """Test purl with qualifiers."""
        result = extract_name_version_from_purl("pkg:pypi/requests@2.28.0?arch=amd64")
        assert result == ("requests", "2.28.0")

    def test_purl_with_namespace(self):
        """Test purl with namespace."""
        result = extract_name_version_from_purl(
            "pkg:maven/org.apache.commons/commons-lang3@3.12.0"
        )
        assert result == ("commons-lang3", "3.12.0")

    def test_deb_purl(self):
        """Test debian purl."""
        result = extract_name_version_from_purl("pkg:deb/debian/openssl@1.1.1k")
        assert result == ("openssl", "1.1.1k")

    def test_url_encoded_purl(self):
        """Test URL-encoded purl."""
        result = extract_name_version_from_purl("pkg:pypi/urllib3@1.26.9%2Bsecurity")
        assert result == ("urllib3", "1.26.9+security")

    def test_none_purl(self):
        """Test None purl returns None."""
        assert extract_name_version_from_purl(None) is None

    def test_empty_purl(self):
        """Test empty purl returns None."""
        assert extract_name_version_from_purl("") is None

    def test_purl_without_version(self):
        """Test purl without version returns None."""
        assert extract_name_version_from_purl("pkg:npm/lodash") is None


class TestValidateCyclonedxSbom:
    """Tests for validate_cyclonedx_sbom function."""

    def test_valid_sbom(self):
        """Test that a valid SBOM passes validation."""
        assert validate_cyclonedx_sbom(CYCLONEDX_SBOM_SAMPLE) is True

    def test_minimal_sbom(self):
        """Test that a minimal valid SBOM passes validation."""
        assert validate_cyclonedx_sbom(MINIMAL_SBOM) is True

    def test_invalid_missing_format(self):
        """Test that SBOM without bomFormat fails validation."""
        assert validate_cyclonedx_sbom(INVALID_SBOM_MISSING_FORMAT) is False

    def test_invalid_wrong_format(self):
        """Test that SBOM with wrong bomFormat fails validation."""
        assert validate_cyclonedx_sbom(INVALID_SBOM_WRONG_FORMAT) is False

    def test_invalid_not_dict(self):
        """Test that non-dict input fails validation."""
        assert validate_cyclonedx_sbom([]) is False
        assert validate_cyclonedx_sbom("string") is False
        assert validate_cyclonedx_sbom(None) is False

    def test_missing_components(self):
        """Test that SBOM without components fails validation."""
        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "components": [],
        }
        assert validate_cyclonedx_sbom(sbom) is False


class TestTransformSbomDependencies:
    """Tests for transform_sbom_dependencies function."""

    def test_transforms_dependency_relationships(self):
        """Test that dependency relationships are transformed."""
        deps = transform_sbom_dependencies(CYCLONEDX_SBOM_SAMPLE)

        # Should have 3 relationships:
        # express -> accepts, express -> body-parser, accepts -> mime-types
        assert len(deps) == 3

    def test_dependency_format_trivy(self):
        """Test that dependencies have Trivy-compatible IDs."""
        deps = transform_sbom_dependencies(CYCLONEDX_SBOM_SAMPLE)

        # Convert to set for comparison
        dep_rels = {(d["source_id"], d["depends_on_id"]) for d in deps}

        # Check expected relationships with Trivy format IDs
        assert dep_rels == EXPECTED_DEPENDENCY_RELS

    def test_no_dependencies_returns_empty(self):
        """Test that SBOM without dependencies returns empty list."""
        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "components": [
                {
                    "bom-ref": "pkg",
                    "name": "test",
                    "version": "1.0.0",
                    "purl": "pkg:npm/test@1.0.0",
                },
            ],
            "dependencies": [],
        }
        deps = transform_sbom_dependencies(sbom)
        assert deps == []
