"""Unit tests for SBOM parser functions."""

from cartography.intel.sbom.parser import extract_ecosystem_from_purl
from cartography.intel.sbom.parser import extract_image_digest
from cartography.intel.sbom.parser import extract_name_version_from_purl
from cartography.intel.sbom.parser import get_direct_dependencies
from cartography.intel.sbom.parser import make_trivy_package_id
from cartography.intel.sbom.parser import transform_sbom_dependencies
from cartography.intel.sbom.parser import transform_sbom_packages
from cartography.intel.sbom.parser import validate_cyclonedx_sbom
from tests.data.sbom.cyclonedx_sample import CYCLONEDX_SBOM_SAMPLE
from tests.data.sbom.cyclonedx_sample import EXPECTED_DEPENDENCY_RELS
from tests.data.sbom.cyclonedx_sample import EXPECTED_DIRECT_DEPS
from tests.data.sbom.cyclonedx_sample import EXPECTED_PACKAGE_IDS
from tests.data.sbom.cyclonedx_sample import INVALID_SBOM_MISSING_FORMAT
from tests.data.sbom.cyclonedx_sample import INVALID_SBOM_WRONG_FORMAT
from tests.data.sbom.cyclonedx_sample import MINIMAL_SBOM
from tests.data.sbom.cyclonedx_sample import SBOM_NO_DEPENDENCIES
from tests.data.sbom.cyclonedx_sample import TEST_IMAGE_DIGEST


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


class TestExtractImageDigest:
    """Tests for extract_image_digest function."""

    def test_extract_from_trivy_property(self):
        """Test extraction from aquasecurity:trivy:RepoDigest property."""
        digest = extract_image_digest(CYCLONEDX_SBOM_SAMPLE)
        assert digest == TEST_IMAGE_DIGEST

    def test_extract_from_cdxgen_bom_ref(self):
        """Test extraction from cdxgen/trivy bom-ref format (pkg:oci/repo@sha256:digest)."""
        sbom = {
            "metadata": {
                "component": {
                    "bom-ref": "pkg:oci/205930638578.dkr.ecr.us-east-1.amazonaws.com/my-app@sha256:a2c3be95e7f6d7c365ac0c921e5d724f62d7cd801759e18270aad7541a30e207",
                    "type": "container",
                    "name": "205930638578.dkr.ecr.us-east-1.amazonaws.com/my-app",
                    "purl": "pkg:oci/205930638578.dkr.ecr.us-east-1.amazonaws.com/my-app@sha256%3Aa2c3be95e7f6d7c365ac0c921e5d724f62d7cd801759e18270aad7541a30e207",
                },
            },
        }
        digest = extract_image_digest(sbom)
        assert (
            digest
            == "sha256:a2c3be95e7f6d7c365ac0c921e5d724f62d7cd801759e18270aad7541a30e207"
        )

    def test_extract_from_url_encoded_purl(self):
        """Test extraction from URL-encoded purl (sha256%3A...)."""
        sbom = {
            "metadata": {
                "component": {
                    "purl": "pkg:oci/my-repo@sha256%3Aabc123def456",
                    "properties": [],
                },
            },
        }
        digest = extract_image_digest(sbom)
        assert digest == "sha256:abc123def456"

    def test_extract_from_oci_image_property(self):
        """Test extraction from oci:image:RepoDigest property."""
        sbom = {
            "metadata": {
                "component": {
                    "properties": [
                        {
                            "name": "oci:image:RepoDigest",
                            "value": "my-repo@sha256:xyz789abc",
                        }
                    ],
                },
            },
        }
        digest = extract_image_digest(sbom)
        assert digest == "sha256:xyz789abc"

    def test_extract_from_hash(self):
        """Test extraction from component hash."""
        sbom = {
            "metadata": {
                "component": {
                    "hashes": [
                        {"alg": "SHA-256", "content": "abc123def456"},
                    ],
                },
            },
        }
        digest = extract_image_digest(sbom)
        assert digest == "sha256:abc123def456"

    def test_no_digest_returns_none(self):
        """Test that missing digest returns None."""
        sbom = {"metadata": {}}
        digest = extract_image_digest(sbom)
        assert digest is None

    def test_empty_sbom_returns_none(self):
        """Test that empty SBOM returns None."""
        digest = extract_image_digest({})
        assert digest is None


class TestGetDirectDependencies:
    """Tests for get_direct_dependencies function."""

    def test_extracts_direct_deps_from_root(self):
        """Test that direct dependencies are identified from root component."""
        direct_deps = get_direct_dependencies(CYCLONEDX_SBOM_SAMPLE)
        assert direct_deps == EXPECTED_DIRECT_DEPS

    def test_no_dependencies_all_treated_as_direct(self):
        """Test that without dependency graph, all packages are direct."""
        direct_deps = get_direct_dependencies(SBOM_NO_DEPENDENCIES)
        # All components should be treated as direct
        assert "pkg:npm/pkg-a@1.0.0" in direct_deps
        assert "pkg:npm/pkg-b@2.0.0" in direct_deps

    def test_empty_dependencies_array(self):
        """Test handling of empty dependencies array."""
        sbom = {
            "components": [
                {"bom-ref": "pkg:test@1.0.0", "name": "test", "version": "1.0.0"},
            ],
            "dependencies": [],
        }
        direct_deps = get_direct_dependencies(sbom)
        assert "pkg:test@1.0.0" in direct_deps


class TestExtractEcosystemFromPurl:
    """Tests for extract_ecosystem_from_purl function."""

    def test_npm_purl(self):
        """Test npm purl parsing."""
        assert extract_ecosystem_from_purl("pkg:npm/lodash@4.17.21") == "npm"

    def test_pypi_purl(self):
        """Test pypi purl parsing."""
        assert extract_ecosystem_from_purl("pkg:pypi/requests@2.25.1") == "pypi"

    def test_maven_purl(self):
        """Test maven purl parsing."""
        assert (
            extract_ecosystem_from_purl(
                "pkg:maven/org.apache.commons/commons-lang3@3.12.0"
            )
            == "maven"
        )

    def test_docker_purl(self):
        """Test docker purl parsing."""
        assert extract_ecosystem_from_purl("pkg:docker/nginx@1.21") == "docker"

    def test_golang_purl(self):
        """Test golang purl parsing."""
        assert (
            extract_ecosystem_from_purl("pkg:golang/github.com/gin-gonic/gin@v1.7.0")
            == "golang"
        )

    def test_deb_purl(self):
        """Test debian package purl parsing."""
        assert extract_ecosystem_from_purl("pkg:deb/debian/openssl@1.1.1k") == "deb"

    def test_none_purl(self):
        """Test None purl returns None."""
        assert extract_ecosystem_from_purl(None) is None

    def test_empty_purl(self):
        """Test empty purl returns None."""
        assert extract_ecosystem_from_purl("") is None

    def test_invalid_purl(self):
        """Test invalid purl returns None."""
        assert extract_ecosystem_from_purl("not-a-purl") is None


class TestTransformSbomPackages:
    """Tests for transform_sbom_packages function."""

    def test_transforms_all_packages(self):
        """Test that all packages are transformed."""
        packages = transform_sbom_packages(CYCLONEDX_SBOM_SAMPLE)
        assert len(packages) == 5

    def test_package_id_format_trivy(self):
        """Test that package IDs are in Trivy format: {version}|{name}."""
        packages = transform_sbom_packages(CYCLONEDX_SBOM_SAMPLE)
        package_ids = {p["id"] for p in packages}

        # IDs should be in Trivy format: version|name
        assert package_ids == EXPECTED_PACKAGE_IDS

    def test_is_direct_flag(self):
        """Test that is_direct flag is correctly set."""
        packages = transform_sbom_packages(CYCLONEDX_SBOM_SAMPLE)
        pkg_map = {p["name"]: p for p in packages}

        # Direct dependencies
        assert pkg_map["express"]["is_direct"] is True
        assert pkg_map["lodash"]["is_direct"] is True

        # Transitive dependencies
        assert pkg_map["accepts"]["is_direct"] is False
        assert pkg_map["mime-types"]["is_direct"] is False
        assert pkg_map["body-parser"]["is_direct"] is False

    def test_ecosystem_extracted(self):
        """Test that ecosystem is extracted from purl."""
        packages = transform_sbom_packages(CYCLONEDX_SBOM_SAMPLE)
        for pkg in packages:
            assert pkg["ecosystem"] == "npm"

    def test_package_without_purl(self):
        """Test handling of packages without purl but with name and version."""
        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "components": [
                {
                    "bom-ref": "no-purl-pkg",
                    "type": "library",
                    "name": "no-purl",
                    "version": "1.0.0",
                },
            ],
        }
        packages = transform_sbom_packages(sbom)
        assert len(packages) == 1
        # ID should use Trivy format: version|name
        assert packages[0]["id"] == "1.0.0|no-purl"

    def test_trivy_compatible_fields(self):
        """Test that Trivy-compatible fields are included."""
        packages = transform_sbom_packages(CYCLONEDX_SBOM_SAMPLE)
        for pkg in packages:
            assert "PkgName" in pkg
            assert "InstalledVersion" in pkg
            assert pkg["PkgName"] == pkg["name"]
            assert pkg["InstalledVersion"] == pkg["version"]


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
