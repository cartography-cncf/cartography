"""
Unit tests for cartography.intel.syft.parser module.
"""

from cartography.intel.syft.parser import transform_artifacts
from tests.data.syft.syft_sample import EXPECTED_SYFT_PACKAGES
from tests.data.syft.syft_sample import SYFT_SAMPLE


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

    def test_transform_artifacts_ignores_non_dependency_types(self):
        """Test that non-dependency-of relationship types are ignored."""
        data = {
            "artifacts": [
                {"id": "a", "name": "pkg-a", "version": "1.0.0", "type": "npm"},
                {"id": "b", "name": "pkg-b", "version": "2.0.0", "type": "npm"},
            ],
            "artifactRelationships": [
                {"parent": "a", "child": "b", "type": "contains"},
                {"parent": "a", "child": "b", "type": "ownership"},
            ],
        }
        packages = transform_artifacts(data)
        # Both packages created, but no dependency_ids
        assert len(packages) == 2
        for pkg in packages:
            assert pkg["dependency_ids"] == []

    def test_transform_artifacts_ignores_non_artifact_parents(self):
        """Test that relationships where parent is not an artifact are ignored."""
        data = {
            "artifacts": [
                {"id": "a", "name": "pkg-a", "version": "1.0.0", "type": "npm"},
                {"id": "b", "name": "pkg-b", "version": "2.0.0", "type": "npm"},
            ],
            "artifactRelationships": [
                {
                    "parent": "image-root",  # not an artifact
                    "child": "a",
                    "type": "dependency-of",
                },
                # b depends on a
                {"parent": "a", "child": "b", "type": "dependency-of"},
            ],
        }
        packages = transform_artifacts(data)
        pkg_by_id = {p["id"]: p for p in packages}

        # b depends on a
        assert pkg_by_id["npm|pkg-b|2.0.0"]["dependency_ids"] == ["npm|pkg-a|1.0.0"]
        # a has no deps (image-root is not an artifact)
        assert pkg_by_id["npm|pkg-a|1.0.0"]["dependency_ids"] == []
