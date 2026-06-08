"""
Unit tests for cartography.intel.syft.parser module.
"""

from cartography.intel.syft.parser import _extract_image_digests
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
        assert express["ImageDigestCandidates"] == [
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ]

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

    def test_extract_image_digests_from_current_source_metadata(self):
        data = {
            "source": {
                "id": "sha256:source",
                "name": "alpine",
                "version": "3.19",
                "type": "image",
                "metadata": {
                    "manifestDigest": "sha256:platform",
                    "repoDigests": ["alpine@sha256:index"],
                },
            },
        }

        assert _extract_image_digests(data) == [
            "sha256:platform",
            "sha256:index",
        ]

    def test_extract_image_digests_ignores_source_version_and_target(self):
        data = {
            "source": {
                "type": "image",
                "version": "sha256:not-image-metadata",
                "target": {
                    "digest": "sha256:ignored-target",
                    "manifestDigest": "sha256:ignored-manifest",
                    "repoDigests": ["repo.example/app@sha256:ignored-repo"],
                },
                "metadata": {
                    "manifestDigest": "sha256:metadata",
                    "repoDigests": ["repo.example/app@sha256:repo"],
                },
            },
        }

        assert _extract_image_digests(data) == [
            "sha256:metadata",
            "sha256:repo",
        ]

    def test_extract_image_digests_returns_empty_without_metadata_digests(self):
        data = {
            "source": {
                "type": "image",
                "metadata": {
                    "manifestDigest": "not-a-digest",
                    "repoDigests": ["alpine:3.19", "alpine@not-a-digest"],
                },
            },
        }

        assert _extract_image_digests(data) == []

    def test_transform_artifacts_warns_when_image_source_has_no_digest_candidates(
        self,
        caplog,
    ):
        data = {
            "artifacts": [
                {"id": "a", "name": "pkg-a", "version": "1.0.0", "type": "npm"},
            ],
            "artifactRelationships": [],
            "source": {
                "type": "image",
                "metadata": {},
            },
        }

        packages = transform_artifacts(data)

        assert packages[0]["ImageDigestCandidates"] == []
        assert (
            "Syft image source did not include image digest candidates" in caplog.text
        )
