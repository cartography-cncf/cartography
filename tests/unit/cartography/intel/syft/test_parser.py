"""
Unit tests for cartography.intel.syft.parser module.
"""

import pytest

from cartography.intel.syft.parser import get_image_digest_from_syft
from cartography.intel.syft.parser import SyftValidationError
from cartography.intel.syft.parser import transform_artifacts
from cartography.intel.syft.parser import transform_dependencies
from cartography.intel.syft.parser import validate_syft_json
from tests.data.syft.syft_sample import EXPECTED_DEPENDENCIES
from tests.data.syft.syft_sample import EXPECTED_SYFT_PACKAGES
from tests.data.syft.syft_sample import SYFT_INVALID_ARTIFACTS_NOT_LIST
from tests.data.syft.syft_sample import SYFT_INVALID_NO_ARTIFACTS
from tests.data.syft.syft_sample import SYFT_INVALID_RELATIONSHIPS_NOT_LIST
from tests.data.syft.syft_sample import SYFT_MINIMAL_VALID
from tests.data.syft.syft_sample import SYFT_SAMPLE


class TestValidateSyftJson:
    """Tests for validate_syft_json function."""

    def test_valid_syft_json(self):
        """Test that valid Syft JSON passes validation."""
        # Should not raise
        validate_syft_json(SYFT_SAMPLE)

    def test_valid_minimal_syft_json(self):
        """Test that minimal valid Syft JSON passes validation."""
        # Should not raise
        validate_syft_json(SYFT_MINIMAL_VALID)

    def test_invalid_not_dict(self):
        """Test that non-dict input raises SyftValidationError."""
        with pytest.raises(SyftValidationError, match="must be a dictionary"):
            validate_syft_json([])

    def test_invalid_missing_artifacts(self):
        """Test that missing artifacts field raises SyftValidationError."""
        with pytest.raises(SyftValidationError, match="missing required 'artifacts'"):
            validate_syft_json(SYFT_INVALID_NO_ARTIFACTS)

    def test_invalid_artifacts_not_list(self):
        """Test that non-list artifacts field raises SyftValidationError."""
        with pytest.raises(
            SyftValidationError, match="'artifacts' field must be a list"
        ):
            validate_syft_json(SYFT_INVALID_ARTIFACTS_NOT_LIST)

    def test_invalid_relationships_not_list(self):
        """Test that non-list artifactRelationships raises SyftValidationError."""
        with pytest.raises(
            SyftValidationError, match="'artifactRelationships' field must be a list"
        ):
            validate_syft_json(SYFT_INVALID_RELATIONSHIPS_NOT_LIST)


class TestTransformDependencies:
    """Tests for transform_dependencies function."""

    def test_transform_dependencies(self):
        """Test transforming Syft relationships to DEPENDS_ON data."""
        dependencies = transform_dependencies(SYFT_SAMPLE)

        # Convert to set of tuples for easier assertion
        deps_set = {(d["source_id"], d["target_id"]) for d in dependencies}

        assert deps_set == EXPECTED_DEPENDENCIES

    def test_transform_dependencies_empty(self):
        """Test with no relationships."""
        data = {"artifacts": [], "artifactRelationships": []}
        dependencies = transform_dependencies(data)
        assert dependencies == []

    def test_transform_dependencies_ignores_non_artifact_parents(self):
        """Test that relationships where parent is not an artifact are ignored."""
        data = {
            "artifacts": [
                {"id": "a", "name": "pkg-a", "version": "1.0.0", "type": "npm"},
                {"id": "b", "name": "pkg-b", "version": "2.0.0", "type": "npm"},
            ],
            "artifactRelationships": [
                # This is a dependency of a non-artifact (e.g., the image)
                {
                    "parent": "image-root",  # not an artifact
                    "child": "a",
                    "type": "dependency-of",
                },
                # This is a valid dependency between artifacts:
                # {parent: a, child: b} means b depends on a
                {"parent": "a", "child": "b", "type": "dependency-of"},
            ],
        }
        dependencies = transform_dependencies(data)

        # Only the artifact-to-artifact dependency should be included
        # b depends on a, so: (b)-[:DEPENDS_ON]->(a) using normalized IDs
        assert len(dependencies) == 1
        assert dependencies[0]["source_id"] == "npm|pkg-b|2.0.0"  # b is the dependent
        assert dependencies[0]["target_id"] == "npm|pkg-a|1.0.0"  # a is the dependency

    def test_transform_dependencies_ignores_non_dependency_types(self):
        """Test that non-dependency-of relationship types are ignored."""
        data = {
            "artifacts": [
                {"id": "a", "name": "pkg-a", "version": "1.0.0", "type": "npm"},
                {"id": "b", "name": "pkg-b", "version": "2.0.0", "type": "npm"},
            ],
            "artifactRelationships": [
                {"parent": "a", "child": "b", "type": "contains"},  # not dependency-of
                {"parent": "a", "child": "b", "type": "ownership"},  # not dependency-of
            ],
        }
        dependencies = transform_dependencies(data)
        assert dependencies == []


class TestTransformArtifacts:
    """Tests for transform_artifacts function."""

    def test_transform_artifacts_produces_expected_ids(self):
        """Test that all artifacts produce correct normalized IDs."""
        packages = transform_artifacts(SYFT_SAMPLE)
        ids = {p["id"] for p in packages}
        assert ids == EXPECTED_SYFT_PACKAGES

    def test_transform_artifacts_dependency_ids(self):
        """Test that dependency_ids lists are correct per package."""
        packages = transform_artifacts(SYFT_SAMPLE)
        pkg_by_id = {p["id"]: p for p in packages}

        # express depends on body-parser and accepts
        assert set(pkg_by_id["npm|express|4.18.2"]["dependency_ids"]) == {
            "npm|body-parser|1.20.1",
            "npm|accepts|1.3.8",
        }
        # body-parser depends on bytes
        assert pkg_by_id["npm|body-parser|1.20.1"]["dependency_ids"] == [
            "npm|bytes|3.1.2",
        ]
        # bytes, accepts, lodash have no dependencies
        assert pkg_by_id["npm|bytes|3.1.2"]["dependency_ids"] == []
        assert pkg_by_id["npm|accepts|1.3.8"]["dependency_ids"] == []
        assert pkg_by_id["npm|lodash|4.17.21"]["dependency_ids"] == []

    def test_transform_artifacts_properties(self):
        """Test that package properties are mapped correctly."""
        packages = transform_artifacts(SYFT_SAMPLE)
        pkg_by_id = {p["id"]: p for p in packages}

        express = pkg_by_id["npm|express|4.18.2"]
        assert express["name"] == "express"
        assert express["version"] == "4.18.2"
        assert express["type"] == "npm"
        assert express["purl"] == "pkg:npm/express@4.18.2"
        assert express["language"] == "javascript"
        assert express["found_by"] == "javascript-package-cataloger"
        assert express["normalized_id"] == "npm|express|4.18.2"

    def test_transform_artifacts_empty(self):
        """Test with empty artifacts."""
        data = {"artifacts": [], "artifactRelationships": []}
        packages = transform_artifacts(data)
        assert packages == []

    def test_transform_artifacts_skips_missing_name_version(self):
        """Test that artifacts missing name or version are skipped."""
        data = {
            "artifacts": [
                {"id": "a", "name": "pkg-a", "version": "", "type": "npm"},
                {"id": "b", "name": "", "version": "1.0.0", "type": "npm"},
                {"id": "c", "name": "pkg-c", "version": "1.0.0", "type": "npm"},
            ],
            "artifactRelationships": [],
        }
        packages = transform_artifacts(data)
        assert len(packages) == 1
        assert packages[0]["name"] == "pkg-c"


class TestGetImageDigestFromSyft:
    """Tests for get_image_digest_from_syft function."""

    def test_get_image_digest(self):
        """Test extracting image digest from Syft source metadata."""
        digest = get_image_digest_from_syft(SYFT_SAMPLE)
        assert (
            digest
            == "sha256:0000000000000000000000000000000000000000000000000000000000000000"
        )

    def test_get_image_digest_from_repo_digests(self):
        """Test extracting digest from repoDigests."""
        data = {"source": {"target": {"repoDigests": ["myimage@sha256:abcdef123456"]}}}
        digest = get_image_digest_from_syft(data)
        assert digest == "sha256:abcdef123456"

    def test_get_image_digest_not_found(self):
        """Test when no digest is available."""
        data = {"source": {"target": {}}}
        digest = get_image_digest_from_syft(data)
        assert digest is None

    def test_get_image_digest_no_source(self):
        """Test when source is missing."""
        data = {"artifacts": []}
        digest = get_image_digest_from_syft(data)
        assert digest is None
