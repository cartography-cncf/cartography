import json
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import httpx
import pytest

from cartography.intel.gcp.artifact_registry import supply_chain
from cartography.intel.gcp.artifact_registry.supply_chain import _build_layer_dicts
from cartography.intel.gcp.artifact_registry.supply_chain import (
    _extract_parent_image_from_spdx_sbom,
)
from cartography.intel.gcp.artifact_registry.supply_chain import (
    _extract_source_from_spdx_sbom,
)
from cartography.intel.gcp.artifact_registry.supply_chain import (
    _fetch_attestation_provenance,
)
from cartography.intel.gcp.artifact_registry.supply_chain import (
    _fetch_legacy_sbom_provenance,
)
from cartography.intel.gcp.artifact_registry.supply_chain import _process_single_image
from cartography.intel.gcp.artifact_registry.supply_chain import _TokenManager
from cartography.intel.gcp.artifact_registry.supply_chain import GAR_PROVENANCE_VERSION
from cartography.intel.supply_chain import extract_layers_from_oci_config
from cartography.intel.supply_chain import extract_provenance_from_oci_config
from tests.data.gcp.artifact_registry import MOCK_BUILDKIT_ATTESTATION_ARTIFACT
from tests.data.gcp.artifact_registry import MOCK_BUILDKIT_ATTESTATION_DIGEST
from tests.data.gcp.artifact_registry import MOCK_BUILDKIT_ATTESTATION_MANIFEST
from tests.data.gcp.artifact_registry import MOCK_BUILDKIT_ATTESTATION_MANIFEST_URL
from tests.data.gcp.artifact_registry import MOCK_BUILDKIT_INDEX_ARTIFACT
from tests.data.gcp.artifact_registry import MOCK_BUILDKIT_PROVENANCE_BLOB_URL
from tests.data.gcp.artifact_registry import MOCK_BUILDKIT_PROVENANCE_STATEMENT
from tests.data.gcp.artifact_registry import mock_ko_spdx_sbom
from tests.data.gcp.artifact_registry import MOCK_SINGLE_IMAGE_CONFIG
from tests.data.gcp.artifact_registry import (
    mock_single_image_config_with_inherited_labels,
)
from tests.data.gcp.artifact_registry import mock_single_image_config_without_labels
from tests.data.gcp.artifact_registry import MOCK_SINGLE_IMAGE_MANIFEST
from tests.data.gcp.artifact_registry import mock_spdx_parent_image_sbom
from tests.data.gcp.artifact_registry import mock_spdx_sbom
from tests.data.gcp.artifact_registry import MOCK_SPDX_SBOM_MANIFEST
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_DIGEST_SBOM_BLOB_URL
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_DIGEST_SBOM_MANIFEST_URL
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_IMAGE_CONFIG_URL
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_IMAGE_DIGEST
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_IMAGE_DIGEST_HEX
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_IMAGE_MANIFEST_URL
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_IMAGE_REFERRERS_URL
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_IMAGE_URI
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_MISSING_SBOM_URI
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_PARENT_IMAGE_DIGEST
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_PARENT_IMAGE_URI
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_SBOM_BLOB_URL
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_SBOM_MANIFEST_URL
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_SBOM_URI

# ---------------------------------------------------------------------------
# OCI label provenance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source_label, expected_source_uri, expected_source_path_uri",
    [
        ("https://github.com/foo/bar.git", "https://github.com/foo/bar", None),
        (
            "https://github.com/foo/bar/tree/main/services/api/",
            "https://github.com/foo/bar",
            "https://github.com/foo/bar/tree/main/services/api",
        ),
        (
            "https://gitlab.example.com/foo/sub/bar/-/tree/main/services/api",
            "https://gitlab.example.com/foo/sub/bar",
            "https://gitlab.example.com/foo/sub/bar/-/tree/main/services/api",
        ),
        (
            "https://github.com/foo/bar/blob/main/services/api/Dockerfile",
            "https://github.com/foo/bar",
            "https://github.com/foo/bar/blob/main/services/api/Dockerfile",
        ),
        (
            "https://gitlab.example.com/foo/bar/-/blob/main/Dockerfile",
            "https://gitlab.example.com/foo/bar",
            "https://gitlab.example.com/foo/bar/-/blob/main/Dockerfile",
        ),
        (
            "https://github.com/foo/bar/tree/main/examples/-/tree/x",
            "https://github.com/foo/bar",
            "https://github.com/foo/bar/tree/main/examples/-/tree/x",
        ),
        ("https://github.com/tree/bar", "https://github.com/tree/bar", None),
        (
            "https://github.com/foo/bar.git/tree/main/services/api",
            "https://github.com/foo/bar",
            "https://github.com/foo/bar/tree/main/services/api",
        ),
        (
            "git@github.com:foo/bar/tree/main/services/api",
            "https://github.com/foo/bar",
            "https://github.com/foo/bar/tree/main/services/api",
        ),
        (
            "https://github.com/foo/bar/tree/main",
            "https://github.com/foo/bar",
            "https://github.com/foo/bar/tree/main",
        ),
    ],
    ids=[
        "dot-git",
        "github-folder",
        "gitlab-folder",
        "github-file",
        "gitlab-file",
        "github-folder-named-dash",
        "owner-named-tree",
        "dot-git-folder",
        "ssh-folder",
        "branch-root",
    ],
)
def test_extract_provenance_from_oci_config_reads_labels(
    source_label, expected_source_uri, expected_source_path_uri
):
    config = {
        "config": {
            "Labels": {
                "org.opencontainers.image.source": source_label,
                "org.opencontainers.image.revision": "deadbeef",
            },
        },
    }

    provenance = extract_provenance_from_oci_config(config)

    assert provenance["source_uri"] == expected_source_uri
    assert provenance.get("source_path_uri") == expected_source_path_uri
    assert provenance["source_revision"] == "deadbeef"


@pytest.mark.parametrize(
    "config",
    [{"config": {}}, {"config": None}, {"config": {"Labels": None}}],
    ids=["no-labels", "null-config", "null-labels"],
)
def test_extract_provenance_from_oci_config_no_labels_returns_empty(config):
    assert extract_provenance_from_oci_config(config) == {}


@pytest.mark.parametrize(
    "config",
    [
        {"rootfs": {"diff_ids": None}, "history": None},
        {"rootfs": None},
        {},
    ],
    ids=["null-diff-ids-and-history", "null-rootfs", "missing"],
)
def test_extract_layers_from_oci_config_without_layers_returns_empty(config):
    assert extract_layers_from_oci_config(config) == ([], [])


def test_extract_layers_from_oci_config_reads_null_history_entry_as_unknown():
    config = {
        "rootfs": {"diff_ids": ["sha256:layer"]},
        "history": [None],
    }

    assert extract_layers_from_oci_config(config) == (
        ["sha256:layer"],
        [{"created_by": "", "empty_layer": False}],
    )


# ---------------------------------------------------------------------------
# SPDX SBOM provenance
# ---------------------------------------------------------------------------


def test_extract_source_from_spdx_sbom_reads_described_package_download_location():
    provenance = _extract_source_from_spdx_sbom(
        mock_spdx_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST),
    )

    assert provenance == {"source_uri": "https://github.com/example/widgets"}


def test_extract_source_from_spdx_sbom_reads_described_package_golang_purl():
    sbom = mock_spdx_sbom(
        MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
        packages=[
            {
                "name": "github.com/example/widgets",
                "SPDXID": "SPDXRef-RootPackage",
                "downloadLocation": "NOASSERTION",
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": (
                            "pkg:golang/github.com/example/widgets@v0.0.0"
                            "?type=module"
                        ),
                    }
                ],
            }
        ],
    )

    provenance = _extract_source_from_spdx_sbom(sbom)

    assert provenance == {"source_uri": "https://github.com/example/widgets"}


def test_extract_source_from_spdx_sbom_reads_expected_source_package():
    provenance = _extract_source_from_spdx_sbom(
        mock_ko_spdx_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST),
        subject_digest=MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
        expected_source_uri="https://github.com/example/widgets",
    )

    assert provenance == {"source_uri": "https://github.com/example/widgets"}


def test_extract_source_from_spdx_sbom_rejects_missing_expected_source_package():
    provenance = _extract_source_from_spdx_sbom(
        mock_ko_spdx_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST),
        subject_digest=MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
        expected_source_uri="https://github.com/example/other",
    )

    assert provenance == {}


def test_extract_source_from_spdx_sbom_rejects_expected_source_without_subject_match():
    provenance = _extract_source_from_spdx_sbom(
        mock_ko_spdx_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST),
        expected_source_uri="https://github.com/example/widgets",
    )

    assert provenance == {}


def test_extract_source_from_spdx_sbom_reads_ko_dependency_when_subject_matches():
    provenance = _extract_source_from_spdx_sbom(
        mock_ko_spdx_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST),
        subject_digest=MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
    )

    assert provenance == {"source_uri": "https://github.com/example/widgets"}


def test_extract_source_from_spdx_sbom_rejects_ko_dependency_when_subject_mismatches():
    provenance = _extract_source_from_spdx_sbom(
        mock_ko_spdx_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST),
        subject_digest="sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    )

    assert provenance == {}


def test_extract_source_from_spdx_sbom_ignores_dependency_only_packages():
    sbom = mock_spdx_sbom(
        MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
        packages=[
            {
                "name": "root",
                "SPDXID": "SPDXRef-RootPackage",
                "downloadLocation": "NOASSERTION",
            },
            {
                "name": "dependency",
                "SPDXID": "SPDXRef-Dependency",
                "downloadLocation": "https://github.com/example/dependency",
            },
        ],
    )

    provenance = _extract_source_from_spdx_sbom(sbom)

    assert provenance == {}


def test_extract_source_from_spdx_sbom_requires_one_described_repo():
    sbom = mock_spdx_sbom(
        MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
        document_describes=["SPDXRef-RootPackage", "SPDXRef-OtherRoot"],
        packages=[
            {
                "name": "root",
                "SPDXID": "SPDXRef-RootPackage",
                "downloadLocation": "https://github.com/example/widgets",
            },
            {
                "name": "other",
                "SPDXID": "SPDXRef-OtherRoot",
                "downloadLocation": "https://github.com/example/other",
            },
        ],
    )

    provenance = _extract_source_from_spdx_sbom(sbom)

    assert provenance == {}


def test_extract_source_from_spdx_sbom_accepts_generic_document_identity():
    sbom = mock_spdx_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST)
    sbom["name"] = "sbom.spdx.json"
    sbom["documentNamespace"] = "https://example.test/sbom/generic"

    provenance = _extract_source_from_spdx_sbom(sbom)

    assert provenance == {"source_uri": "https://github.com/example/widgets"}


def test_extract_parent_image_from_spdx_sbom_reads_descendant_relationship():
    provenance = _extract_parent_image_from_spdx_sbom(
        mock_spdx_parent_image_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST),
        MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
    )

    assert provenance == {
        "parent_image_uri": MOCK_SUPPLY_CHAIN_PARENT_IMAGE_URI,
        "parent_image_digest": MOCK_SUPPLY_CHAIN_PARENT_IMAGE_DIGEST,
    }


def test_extract_parent_image_from_spdx_sbom_falls_back_to_variant_relationship():
    provenance = _extract_parent_image_from_spdx_sbom(
        mock_spdx_parent_image_sbom(
            MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
            relationship_type="VARIANT_OF",
        ),
        MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
    )

    assert provenance["parent_image_digest"] == MOCK_SUPPLY_CHAIN_PARENT_IMAGE_DIGEST


def test_extract_parent_image_from_spdx_sbom_prefers_descendant_relationship():
    sbom = mock_spdx_parent_image_sbom(
        MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
        relationship_type="DESCENDANT_OF",
    )
    sbom["packages"].append(
        {
            "name": "registry.example.test/variant-parent",
            "SPDXID": "SPDXRef-Package-variant-parent",
            "downloadLocation": "NOASSERTION",
            "externalRefs": [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": "purl",
                    "referenceLocator": (
                        "pkg:oci/variant-parent@sha256:"
                        "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
                    ),
                },
            ],
        }
    )
    sbom["relationships"].append(
        {
            "spdxElementId": "SPDXRef-Package-subject-image",
            "relationshipType": "VARIANT_OF",
            "relatedSpdxElement": "SPDXRef-Package-variant-parent",
        }
    )

    provenance = _extract_parent_image_from_spdx_sbom(
        sbom,
        MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
    )

    assert provenance["parent_image_digest"] == MOCK_SUPPLY_CHAIN_PARENT_IMAGE_DIGEST


def test_extract_parent_image_from_spdx_sbom_rejects_subject_mismatch():
    provenance = _extract_parent_image_from_spdx_sbom(
        mock_spdx_parent_image_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST),
        "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    )

    assert provenance == {}


def test_extract_parent_image_from_spdx_sbom_rejects_non_image_package():
    sbom = mock_spdx_parent_image_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST)
    sbom["packages"][1]["externalRefs"][0][
        "referenceLocator"
    ] = "pkg:golang/github.com/example/base@v1.0.0"

    provenance = _extract_parent_image_from_spdx_sbom(
        sbom,
        MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
    )

    assert provenance == {}


def test_extract_parent_image_from_spdx_sbom_rejects_self_reference():
    provenance = _extract_parent_image_from_spdx_sbom(
        mock_spdx_parent_image_sbom(
            MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
            parent_image_digest=MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
        ),
        MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
    )

    assert provenance == {}


def test_extract_parent_image_from_spdx_sbom_rejects_ambiguous_parents():
    sbom = mock_spdx_parent_image_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST)
    sbom["packages"].append(
        {
            "name": "registry.example.test/other-base",
            "SPDXID": "SPDXRef-Package-other-parent",
            "downloadLocation": "NOASSERTION",
            "externalRefs": [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": "purl",
                    "referenceLocator": (
                        "pkg:docker/other-base@sha256:"
                        "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
                    ),
                },
            ],
        }
    )
    sbom["relationships"].append(
        {
            "spdxElementId": "SPDXRef-Package-subject-image",
            "relationshipType": "DESCENDANT_OF",
            "relatedSpdxElement": "SPDXRef-Package-other-parent",
        }
    )

    provenance = _extract_parent_image_from_spdx_sbom(
        sbom,
        MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
    )

    assert provenance == {}


def test_extract_parent_image_from_spdx_sbom_rejects_ambiguous_descendant_even_with_variant():
    sbom = mock_spdx_parent_image_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST)
    sbom["packages"].extend(
        [
            {
                "name": "registry.example.test/other-base",
                "SPDXID": "SPDXRef-Package-other-parent",
                "downloadLocation": "NOASSERTION",
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": (
                            "pkg:docker/other-base@sha256:"
                            "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
                        ),
                    },
                ],
            },
            {
                "name": "registry.example.test/variant-base",
                "SPDXID": "SPDXRef-Package-variant-parent",
                "downloadLocation": "NOASSERTION",
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": (
                            "pkg:oci/variant-base@sha256:"
                            "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
                        ),
                    },
                ],
            },
        ],
    )
    sbom["relationships"].extend(
        [
            {
                "spdxElementId": "SPDXRef-Package-subject-image",
                "relationshipType": "DESCENDANT_OF",
                "relatedSpdxElement": "SPDXRef-Package-other-parent",
            },
            {
                "spdxElementId": "SPDXRef-Package-subject-image",
                "relationshipType": "VARIANT_OF",
                "relatedSpdxElement": "SPDXRef-Package-variant-parent",
            },
        ],
    )

    provenance = _extract_parent_image_from_spdx_sbom(
        sbom,
        MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
    )

    assert provenance == {}


# ---------------------------------------------------------------------------
# Layer history alignment
# ---------------------------------------------------------------------------


def test_build_layer_dicts_aligns_history_skipping_empty_layers():
    enrichments = [
        {
            "id": "img-1",
            "layer_diff_ids": ["sha256:a", "sha256:b"],
            "layer_history": [
                {"created_by": "FROM scratch", "empty_layer": False},
                {"created_by": "ENV X=1", "empty_layer": True},
                {"created_by": "RUN apt-get install foo", "empty_layer": False},
            ],
        },
    ]

    layers = {layer["diff_id"]: layer for layer in _build_layer_dicts(enrichments)}

    assert layers["sha256:a"]["history"] == "FROM scratch"
    assert layers["sha256:b"]["history"] == "RUN apt-get install foo"
    assert layers["sha256:a"]["next_diff_ids"] == ["sha256:b"]
    assert layers["sha256:b"]["next_diff_ids"] == []


def test_build_layer_dicts_keeps_all_shared_layer_successors():
    # Arrange
    enrichments = [
        {"layer_diff_ids": ["sha256:a", "sha256:b"]},
        {"layer_diff_ids": ["sha256:a", "sha256:c"]},
    ]

    # Act
    layers = {layer["diff_id"]: layer for layer in _build_layer_dicts(enrichments)}

    # Assert
    assert layers["sha256:a"]["next_diff_ids"] == ["sha256:b", "sha256:c"]


def test_build_layer_dicts_creates_layer_when_history_truncated():
    enrichments = [
        {
            "id": "img-1",
            "layer_diff_ids": ["sha256:a", "sha256:b"],
            "layer_history": [
                {"created_by": "FROM scratch", "empty_layer": False},
            ],
        },
    ]

    layers = {layer["diff_id"]: layer for layer in _build_layer_dicts(enrichments)}

    assert set(layers.keys()) == {"sha256:a", "sha256:b"}
    assert layers["sha256:b"]["history"] is None


def test_build_layer_dicts_prefers_populated_history_on_collision():
    enrichments = [
        {
            "id": "img-no-history",
            "layer_diff_ids": ["sha256:a"],
            "layer_history": [],
        },
        {
            "id": "img-with-history",
            "layer_diff_ids": ["sha256:a"],
            "layer_history": [
                {"created_by": "RUN apt-get install foo", "empty_layer": False},
            ],
        },
    ]

    layers = _build_layer_dicts(enrichments)

    assert len(layers) == 1
    assert layers[0]["history"] == "RUN apt-get install foo"


def test_build_layer_dicts_keeps_first_populated_history_on_collision():
    enrichments = [
        {
            "id": "img-1",
            "layer_diff_ids": ["sha256:a"],
            "layer_history": [
                {"created_by": "RUN first", "empty_layer": False},
            ],
        },
        {
            "id": "img-2",
            "layer_diff_ids": ["sha256:a"],
            "layer_history": [
                {"created_by": "RUN second", "empty_layer": False},
            ],
        },
    ]

    layers = _build_layer_dicts(enrichments)

    assert layers[0]["history"] == "RUN first"


# ---------------------------------------------------------------------------
# Cleanup gating in sync()
# ---------------------------------------------------------------------------


@pytest.fixture
def patched_sync(monkeypatch):
    """Patch async fetch + neo4j writes; spy on cleanup invocations."""
    cleanup_runs = []

    fake_job = MagicMock()
    fake_job.run = MagicMock(side_effect=lambda session: cleanup_runs.append(session))

    monkeypatch.setattr(
        supply_chain.GraphJob,
        "from_node_schema",
        MagicMock(return_value=fake_job),
    )
    monkeypatch.setattr(
        supply_chain.GraphJob,
        "from_matchlink",
        MagicMock(return_value=fake_job),
    )
    monkeypatch.setattr(
        supply_chain,
        "run_scoped_analysis_job",
        MagicMock(side_effect=lambda name, session, params: cleanup_runs.append(name)),
    )
    monkeypatch.setattr(
        supply_chain,
        "load_image_provenance",
        MagicMock(side_effect=lambda _session, updates, _project, _tag: updates),
    )
    monkeypatch.setattr(supply_chain, "load_image_layers", MagicMock())
    monkeypatch.setattr(supply_chain, "load_image_layer_relationships", MagicMock())
    monkeypatch.setattr(
        supply_chain,
        "get_complete_layer_digests",
        MagicMock(return_value=set()),
    )
    monkeypatch.setattr(supply_chain, "refresh_layer_closures", MagicMock())
    monkeypatch.setattr(
        supply_chain,
        "_get_provenance_complete_names",
        MagicMock(return_value=set()),
    )
    monkeypatch.setattr(
        supply_chain,
        "_get_layer_graph_complete_names",
        MagicMock(return_value=set()),
    )
    monkeypatch.setattr(supply_chain, "load_repository_image_provenance", MagicMock())
    monkeypatch.setattr(supply_chain, "load_missing_built_from", MagicMock())

    def _set_enrichments(enrichments, fetch_failures=0):
        async def _fake_fetch(*_args, **_kwargs):
            return enrichments, fetch_failures, {}

        monkeypatch.setattr(supply_chain, "_fetch_all_image_provenance", _fake_fetch)

    return _set_enrichments, cleanup_runs


def test_sync_loads_provenance_and_layers_with_split_phases(patched_sync):
    set_enrichments, _cleanup_runs = patched_sync
    enrichments = [
        {
            "digest": "sha256:img-1",
            "type": "image",
            "media_type": "application/vnd.oci.image.manifest.v1+json",
            "source_uri": "https://github.com/foo/bar",
            "source_revision": "deadbeef",
            "source_file": "Dockerfile",
            "layer_diff_ids": ["sha256:a", "sha256:b"],
            "layer_history": [
                {"created_by": "FROM scratch", "empty_layer": False},
                {"created_by": "RUN build", "empty_layer": False},
            ],
        },
        {
            "digest": "sha256:img-2",
            "type": "image",
            "layer_diff_ids": ["sha256:a"],
            "layer_history": [],
        },
    ]
    set_enrichments(enrichments=enrichments, fetch_failures=0)
    neo4j_session = MagicMock()

    supply_chain.sync(
        neo4j_session=neo4j_session,
        credentials=MagicMock(),
        docker_artifacts_raw=[{"name": "img"}],
        project_id="proj",
        update_tag=1,
        common_job_parameters={},
        cleanup_safe=True,
    )

    supply_chain.load_image_provenance.assert_called_once_with(
        neo4j_session,
        [
            {
                "digest": "sha256:img-1",
                "type": "image",
                "media_type": "application/vnd.oci.image.manifest.v1+json",
                "source_uri": "https://github.com/foo/bar",
                "source_revision": "deadbeef",
                "source_file": "Dockerfile",
                "parent_image_uri": None,
                "parent_image_digest": None,
                "layer_diff_ids": ["sha256:a", "sha256:b"],
                "architecture": None,
                "os": None,
                "os_version": None,
                "os_features": None,
                "variant": None,
                "provenance_from_slsa": False,
            },
            {
                "digest": "sha256:img-2",
                "type": "image",
                "media_type": None,
                "source_uri": None,
                "source_revision": None,
                "source_file": None,
                "parent_image_uri": None,
                "parent_image_digest": None,
                "layer_diff_ids": ["sha256:a"],
                "architecture": None,
                "os": None,
                "os_version": None,
                "os_features": None,
                "variant": None,
                "provenance_from_slsa": False,
            },
        ],
        "proj",
        1,
    )
    supply_chain.load_image_layers.assert_called_once()
    layer_call_args = supply_chain.load_image_layers.call_args.args
    assert layer_call_args[0] == neo4j_session
    assert {layer["diff_id"] for layer in layer_call_args[1]} == {
        "sha256:a",
        "sha256:b",
    }
    assert layer_call_args[2:] == ("proj", 1)
    supply_chain.load_image_layer_relationships.assert_called_once_with(
        neo4j_session,
        supply_chain.load_image_provenance.call_args.args[1],
        1,
    )


def test_load_image_provenance_preserves_existing_values(monkeypatch):
    load_nodes_without_relationships = MagicMock()
    load_matchlinks_with_progress = MagicMock()
    monkeypatch.setattr(
        supply_chain,
        "load_nodes_without_relationships",
        load_nodes_without_relationships,
    )
    monkeypatch.setattr(
        supply_chain,
        "load_matchlinks_with_progress",
        load_matchlinks_with_progress,
    )
    neo4j_session = MagicMock()
    neo4j_session.execute_read.return_value = [
        {
            "digest": "sha256:img-1",
            "type": "image",
            "media_type": "application/vnd.oci.image.manifest.v1+json",
            "architecture": "amd64",
            "os": "linux",
            "os_version": None,
            "os_features": None,
            "variant": "v8",
            "source_uri": "https://github.com/foo/bar",
            "source_revision": "deadbeef",
            "source_file": "Dockerfile",
            "parent_image_uri": "pkg:oci/base@sha256:parent",
            "parent_image_digest": "sha256:parent",
            "layer_diff_ids": ["sha256:a"],
        },
    ]
    updates = [
        {
            "digest": "sha256:img-1",
            "type": "image",
            "media_type": "application/vnd.oci.image.manifest.v1+json",
            "architecture": None,
            "os": None,
            "os_version": None,
            "os_features": None,
            "variant": None,
            "source_uri": None,
            "source_revision": None,
            "source_file": None,
            "parent_image_uri": None,
            "parent_image_digest": None,
            "layer_diff_ids": None,
        },
    ]

    supply_chain.load_image_provenance(neo4j_session, updates, "proj", 1)

    neo4j_session.execute_read.assert_called_once()
    load_nodes_without_relationships.assert_called_once()
    call = load_nodes_without_relationships.call_args
    assert call.args[0] == neo4j_session
    assert call.args[1].__class__.__name__ == "GCPArtifactRegistryImageProvenanceSchema"
    assert call.args[2] == [
        {
            "digest": "sha256:img-1",
            "type": "image",
            "media_type": "application/vnd.oci.image.manifest.v1+json",
            "architecture": "amd64",
            "os": "linux",
            "os_version": None,
            "os_features": None,
            "variant": "v8",
            "source_uri": "https://github.com/foo/bar",
            "source_revision": "deadbeef",
            "source_file": "Dockerfile",
            "parent_image_uri": "pkg:oci/base@sha256:parent",
            "parent_image_digest": "sha256:parent",
            "layer_diff_ids": ["sha256:a"],
        },
    ]
    load_matchlinks_with_progress.assert_called_once()
    assert "provenance updates" in call.kwargs["progress_description"]
    assert call.kwargs["lastupdated"] == 1
    assert call.kwargs["PROJECT_ID"] == "proj"


def test_load_image_layers_sends_one_next_pair_per_row(monkeypatch):
    load_nodes_without_relationships = MagicMock()
    load_matchlinks_with_progress = MagicMock()
    load = MagicMock()
    monkeypatch.setattr(
        supply_chain,
        "load_nodes_without_relationships",
        load_nodes_without_relationships,
    )
    monkeypatch.setattr(
        supply_chain,
        "load_matchlinks_with_progress",
        load_matchlinks_with_progress,
    )
    monkeypatch.setattr(supply_chain, "load", load)
    neo4j_session = MagicMock()
    layers = [
        {
            "diff_id": "sha256:a",
            "history": "FROM scratch",
            "next_diff_ids": ["sha256:b", "sha256:c"],
        },
    ]

    supply_chain.load_image_layers(neo4j_session, layers, "proj", 1)

    load_nodes_without_relationships.assert_called_once()
    node_call = load_nodes_without_relationships.call_args
    assert node_call.args[0] == neo4j_session
    assert node_call.args[1].__class__.__name__ == "GCPArtifactRegistryImageLayerSchema"
    assert node_call.args[2] == layers
    assert "image layer nodes" in node_call.kwargs["progress_description"]

    load_matchlinks_with_progress.assert_called_once()
    rel_call = load_matchlinks_with_progress.call_args
    assert rel_call.args[0] == neo4j_session
    assert rel_call.args[1].__class__.__name__ == (
        "GCPArtifactRegistryProjectToImageLayerRel"
    )
    assert rel_call.args[2] == layers
    assert "RESOURCE relationships" in rel_call.kwargs["progress_description"]
    assert rel_call.kwargs["lastupdated"] == 1
    assert rel_call.kwargs["PROJECT_ID"] == "proj"
    assert rel_call.kwargs["_sub_resource_label"] == "GCPProject"
    assert rel_call.kwargs["_sub_resource_id"] == "proj"

    load.assert_called_once()
    next_call = load.call_args
    assert next_call.args[1].__class__.__name__ == (
        "GCPArtifactRegistryImageLayerNextRelSchema"
    )
    assert next_call.args[2] == [
        {"diff_id": "sha256:a", "next_diff_ids": ["sha256:b"]},
        {"diff_id": "sha256:a", "next_diff_ids": ["sha256:c"]},
    ]


def test_build_image_layer_relationship_dicts_skips_manifest_lists():
    # Act
    relationships = supply_chain._build_image_layer_relationship_dicts(
        [
            {
                "digest": "sha256:image",
                "type": "image",
                "layer_diff_ids": ["sha256:a", "sha256:b"],
            },
            {
                "digest": "sha256:index",
                "type": "manifest_list",
                "layer_diff_ids": ["sha256:ignored"],
            },
        ],
    )

    # Assert
    assert relationships == [
        {
            "digest": "sha256:image",
            "layer_diff_ids": ["sha256:a", "sha256:b"],
            "head_layer_diff_id": "sha256:a",
            "tail_layer_diff_id": "sha256:b",
        },
    ]


@pytest.mark.parametrize(
    "docker_artifacts_raw",
    [
        [{"name": "img"}],
        # A project whose last image is gone still removes its stale layer links.
        [],
    ],
    ids=["images", "no_images"],
)
def test_sync_runs_cleanup_when_safe_and_no_failures(
    patched_sync, docker_artifacts_raw
):
    set_enrichments, cleanup_runs = patched_sync
    set_enrichments(enrichments=[], fetch_failures=0)

    supply_chain.sync(
        neo4j_session=MagicMock(),
        credentials=MagicMock(),
        docker_artifacts_raw=docker_artifacts_raw,
        project_id="proj",
        update_tag=1,
        common_job_parameters={},
        cleanup_safe=True,
    )

    assert "gcp_artifact_registry_orphan_image_layer_cleanup.json" in cleanup_runs
    assert len(cleanup_runs) == 2


def test_sync_skips_cleanup_when_fetch_failures(patched_sync):
    set_enrichments, cleanup_runs = patched_sync
    set_enrichments(enrichments=[], fetch_failures=3)

    supply_chain.sync(
        neo4j_session=MagicMock(),
        credentials=MagicMock(),
        docker_artifacts_raw=[{"name": "img"}],
        project_id="proj",
        update_tag=1,
        common_job_parameters={},
        cleanup_safe=True,
    )

    assert cleanup_runs == []


def test_sync_skips_cleanup_when_discovery_unsafe(patched_sync):
    set_enrichments, cleanup_runs = patched_sync
    set_enrichments(
        enrichments=[
            {"digest": "sha256:img", "source_uri": "https://github.com/foo/bar"}
        ],
        fetch_failures=0,
    )

    supply_chain.sync(
        neo4j_session=MagicMock(),
        credentials=MagicMock(),
        docker_artifacts_raw=[{"name": "img"}],
        project_id="proj",
        update_tag=1,
        common_job_parameters={},
        cleanup_safe=False,
    )

    assert cleanup_runs == []


def _single_image(name_suffix, digest_char):
    digest = "sha256:" + digest_char * 64
    return {
        "name": f"projects/p/locations/l/repositories/r/dockerImages/{name_suffix}@{digest}",
        "uri": f"us-docker.pkg.dev/p/r/i@{digest}",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
    }


@pytest.mark.parametrize(
    ("cleanup_safe", "expected_stamps", "expected_layer_graph_stamps"),
    [
        (
            True,
            {"new": GAR_PROVENANCE_VERSION, "failed": None},
            {"new", "provenance-only"},
        ),
        # Discovery was incomplete, so SBOM tags in unlisted repositories went
        # unseen: the pass only clears stamps.
        (False, {"failed": None}, set()),
    ],
    ids=["complete_discovery", "incomplete_discovery"],
)
def test_sync_checks_layers_only_without_a_layer_graph_stamp(
    patched_sync,
    monkeypatch,
    cleanup_safe,
    expected_stamps,
    expected_layer_graph_stamps,
):
    # Arrange: one artifact with both stamps, one stamped before layer graph
    # stamps existed whose layers check out, one never enriched, and one whose
    # fetch fails.
    trusted = _single_image("trusted", "a")
    provenance_only = _single_image("provenance-only", "b")
    new = _single_image("new", "c")
    failed = _single_image("failed", "f")
    artifacts = [trusted, provenance_only, new, failed]
    names = {
        trusted["name"]: "trusted",
        provenance_only["name"]: "provenance-only",
        new["name"]: "new",
        failed["name"]: "failed",
    }
    supply_chain._get_provenance_complete_names.return_value = {
        trusted["name"],
        provenance_only["name"],
    }
    supply_chain._get_layer_graph_complete_names.return_value = {trusted["name"]}
    supply_chain.get_complete_layer_digests.return_value = {"sha256:" + "b" * 64}
    fetch = AsyncMock(
        return_value=(
            [],
            0,
            {new["name"]: GAR_PROVENANCE_VERSION, failed["name"]: None},
        ),
    )
    monkeypatch.setattr(supply_chain, "_fetch_all_image_provenance", fetch)
    neo4j_session = MagicMock()
    writes = []
    for step in (
        "load_image_layer_relationships",
        "load_missing_built_from",
        "load_repository_image_provenance",
    ):
        getattr(supply_chain, step).side_effect = (
            lambda *_args, step=step, **_kwargs: writes.append(step)
        )

    # Act
    supply_chain.sync(
        neo4j_session=neo4j_session,
        credentials=MagicMock(),
        docker_artifacts_raw=artifacts,
        project_id="proj",
        update_tag=1,
        common_job_parameters={},
        cleanup_safe=cleanup_safe,
    )

    # Assert
    assert supply_chain.get_complete_layer_digests.call_args.args[2] == {
        "sha256:" + "b" * 64,
        "sha256:" + "c" * 64,
        "sha256:" + "f" * 64,
    }
    assert fetch.await_args.kwargs["complete_digests"] == {
        "sha256:" + "a" * 64,
        "sha256:" + "b" * 64,
    }
    stamp_args = supply_chain.load_repository_image_provenance.call_args
    assert {names[n]: v for n, v in stamp_args.args[2].items()} == expected_stamps
    assert {
        names[n] for n in stamp_args.kwargs["layer_graph_names"]
    } == expected_layer_graph_stamps
    # A stamp lets later syncs skip the artifact, so it lands after its chunk's
    # enrichment writes.
    assert writes == [
        "load_image_layer_relationships",
        "load_repository_image_provenance",
        "load_missing_built_from",
    ]


def test_sync_reads_sboms_from_other_image_paths(patched_sync, monkeypatch):
    # Arrange: one chunk per image path, and the SBOM sits in another path, as
    # ko publishes it.
    monkeypatch.setattr(supply_chain, "ENRICHMENT_CHUNK_SIZE", 1)
    subject = _single_image("subject", "d")
    sbom = {
        "name": "projects/p/locations/l/repositories/r/dockerImages/sbom@sha256:"
        + "e" * 64,
        "uri": "us-docker.pkg.dev/p/r/sbom@sha256:" + "e" * 64,
        "tags": ["sha256-" + "d" * 64 + ".sbom"],
    }
    sbom_lookups = {}

    async def _fetch(_credentials, artifacts, _project_id, **kwargs):
        for artifact in artifacts:
            sbom_lookups[artifact["name"]] = kwargs["sbom_artifacts_by_digest"]
        return [], 0, {}

    monkeypatch.setattr(supply_chain, "_fetch_all_image_provenance", _fetch)

    # Act
    supply_chain.sync(
        neo4j_session=MagicMock(),
        credentials=MagicMock(),
        docker_artifacts_raw=[subject, sbom],
        project_id="proj",
        update_tag=1,
        common_job_parameters={},
    )

    # Assert
    assert sbom_lookups[subject["name"]]["sha256:" + "d" * 64] == [sbom]


def test_sync_keeps_finished_chunks_when_a_later_chunk_fails(patched_sync, monkeypatch):
    # Arrange: one chunk per image path. Image i has two artifacts, which an index
    # and its platform images would need read together.
    monkeypatch.setattr(supply_chain, "ENRICHMENT_CHUNK_SIZE", 1)
    first = {
        "name": "projects/p/locations/l/repositories/r/dockerImages/i@sha256:1111111111111111111111111111111111111111111111111111111111111111",
        "uri": "us-docker.pkg.dev/p/r/i@sha256:1111111111111111111111111111111111111111111111111111111111111111",
    }
    second = {
        "name": "projects/p/locations/l/repositories/r/dockerImages/i@sha256:2222222222222222222222222222222222222222222222222222222222222222",
        "uri": "us-docker.pkg.dev/p/r/i@sha256:2222222222222222222222222222222222222222222222222222222222222222",
    }
    other_repository = {
        "name": "projects/p/locations/l/repositories/r/dockerImages/j@sha256:3333333333333333333333333333333333333333333333333333333333333333",
        "uri": "us-docker.pkg.dev/p/r/j@sha256:3333333333333333333333333333333333333333333333333333333333333333",
    }

    async def _fetch(_credentials, artifacts, _project_id, **_kwargs):
        if other_repository in artifacts:
            raise RuntimeError("registry unavailable")
        return [], 0, {first["name"]: GAR_PROVENANCE_VERSION}

    monkeypatch.setattr(supply_chain, "_fetch_all_image_provenance", _fetch)
    neo4j_session = MagicMock()

    # Act
    with pytest.raises(RuntimeError):
        supply_chain.sync(
            neo4j_session=neo4j_session,
            credentials=MagicMock(),
            docker_artifacts_raw=[first, second, other_repository],
            project_id="proj",
            update_tag=1,
            common_job_parameters={},
        )

    # Assert
    supply_chain.load_repository_image_provenance.assert_called_once_with(
        neo4j_session,
        [first, second],
        {first["name"]: GAR_PROVENANCE_VERSION},
        "proj",
        1,
        layer_graph_names={first["name"]},
    )


def test_sync_without_layer_graph_keeps_provenance_and_removes_layer_links(
    patched_sync, monkeypatch
):
    # Arrange: a failed fetch would normally hold back the layer link cleanup.
    set_enrichments, cleanup_runs = patched_sync
    set_enrichments(
        enrichments=[
            {
                "digest": "sha256:img",
                "source_uri": "https://github.com/foo/bar",
                "layer_diff_ids": ["sha256:a", "sha256:b"],
            }
        ],
        fetch_failures=1,
    )

    # Act
    supply_chain.sync(
        neo4j_session=MagicMock(),
        credentials=MagicMock(),
        docker_artifacts_raw=[{"name": "img"}],
        project_id="proj",
        update_tag=1,
        common_job_parameters={},
        sync_layer_graph=False,
    )

    # Assert
    provenance_update = supply_chain.load_image_provenance.call_args.args[1][0]
    assert (provenance_update["source_uri"], provenance_update["layer_diff_ids"]) == (
        "https://github.com/foo/bar",
        ["sha256:a", "sha256:b"],
    )
    supply_chain.get_complete_layer_digests.assert_not_called()
    supply_chain.load_image_layers.assert_not_called()
    supply_chain.load_image_layer_relationships.assert_not_called()
    assert cleanup_runs == ["gcp_artifact_registry_orphan_image_layer_cleanup.json"]


@pytest.mark.asyncio
async def test_cached_digest_rechecks_provenance_without_fetching_config(monkeypatch):
    config_fetch = AsyncMock()
    provenance_fetch = AsyncMock(
        return_value={"source_uri": "https://github.com/example/repository"},
    )
    monkeypatch.setattr(supply_chain, "_fetch_image_config", config_fetch)
    monkeypatch.setattr(
        supply_chain,
        "_fetch_attestation_provenance",
        provenance_fetch,
    )

    result, fetch_failed = await _process_single_image(
        MagicMock(),
        _fake_token_manager(),
        {
            "name": MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME,
            "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
        },
        fetch_config=False,
    )

    config_fetch.assert_not_awaited()
    provenance_fetch.assert_awaited_once()
    assert fetch_failed is False
    assert result == {
        "digest": MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
        "source_uri": "https://github.com/example/repository",
        "provenance_from_slsa": True,
    }


def test_gcp_layer_graph_uses_indexed_layer_id():
    assert supply_chain.GCP_ARTIFACT_REGISTRY_LAYER_GRAPH.layer_id_property == "id"


# ---------------------------------------------------------------------------
# OCI config extraction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_single_image_extracts_platform_from_oci_config():
    client = _FakeClient(
        {
            MOCK_SUPPLY_CHAIN_IMAGE_MANIFEST_URL: _FakeResponse(
                200,
                json_body=MOCK_SINGLE_IMAGE_MANIFEST,
                headers={"Docker-Content-Digest": MOCK_SUPPLY_CHAIN_IMAGE_DIGEST},
            ),
            MOCK_SUPPLY_CHAIN_IMAGE_CONFIG_URL: _FakeResponse(
                200,
                json_body=MOCK_SINGLE_IMAGE_CONFIG,
            ),
        },
    )

    result, fetch_failed = await _process_single_image(
        client,
        _fake_token_manager(),
        {
            "name": MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME,
            "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
        },
    )

    assert fetch_failed is False
    assert result == {
        "digest": MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
        "type": "image",
        "media_type": "application/vnd.oci.image.manifest.v1+json",
        "architecture": "arm64",
        "os": "linux",
        "variant": "v8",
        "source_uri": "https://github.com/example/widgets",
        "source_revision": "0123456789abcdef",
        "layer_diff_ids": [
            "sha256:2222222222222222222222222222222222222222222222222222222222222222",
        ],
        "layer_history": [
            {
                "created_by": "COPY app /app",
                "empty_layer": False,
            },
        ],
    }


@pytest.mark.asyncio
async def test_process_single_image_falls_back_to_digest_specific_spdx_sbom():
    client = _FakeClient(
        {
            MOCK_SUPPLY_CHAIN_IMAGE_MANIFEST_URL: _FakeResponse(
                200,
                json_body=MOCK_SINGLE_IMAGE_MANIFEST,
                headers={"Docker-Content-Digest": MOCK_SUPPLY_CHAIN_IMAGE_DIGEST},
            ),
            MOCK_SUPPLY_CHAIN_IMAGE_CONFIG_URL: _FakeResponse(
                200,
                json_body=mock_single_image_config_without_labels(),
            ),
            MOCK_SUPPLY_CHAIN_IMAGE_REFERRERS_URL: _FakeResponse(
                200,
                json_body={"manifests": []},
            ),
            MOCK_SUPPLY_CHAIN_DIGEST_SBOM_MANIFEST_URL: _FakeResponse(
                200,
                json_body=MOCK_SPDX_SBOM_MANIFEST,
            ),
            MOCK_SUPPLY_CHAIN_DIGEST_SBOM_BLOB_URL: _FakeResponse(
                200,
                json_body=mock_ko_spdx_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST),
            ),
        },
    )

    result, fetch_failed = await _process_single_image(
        client,
        _fake_token_manager(),
        {
            "name": MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME,
            "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
        },
        {
            MOCK_SUPPLY_CHAIN_IMAGE_DIGEST: [
                {
                    "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
                    "tags": [
                        f"sha256-{MOCK_SUPPLY_CHAIN_IMAGE_DIGEST_HEX}.sbom",
                    ],
                }
            ]
        },
    )

    assert fetch_failed is False
    assert result["digest"] == MOCK_SUPPLY_CHAIN_IMAGE_DIGEST
    assert result["source_uri"] == "https://github.com/example/widgets"
    assert result["layer_diff_ids"] == [
        "sha256:2222222222222222222222222222222222222222222222222222222222222222",
    ]
    assert MOCK_SUPPLY_CHAIN_DIGEST_SBOM_MANIFEST_URL in client.calls


@pytest.mark.asyncio
async def test_process_single_image_extracts_parent_from_spdx_sbom():
    client = _FakeClient(
        {
            MOCK_SUPPLY_CHAIN_IMAGE_MANIFEST_URL: _FakeResponse(
                200,
                json_body=MOCK_SINGLE_IMAGE_MANIFEST,
                headers={"Docker-Content-Digest": MOCK_SUPPLY_CHAIN_IMAGE_DIGEST},
            ),
            MOCK_SUPPLY_CHAIN_IMAGE_CONFIG_URL: _FakeResponse(
                200,
                json_body=mock_single_image_config_without_labels(),
            ),
            MOCK_SUPPLY_CHAIN_IMAGE_REFERRERS_URL: _FakeResponse(
                200,
                json_body={"manifests": []},
            ),
            MOCK_SUPPLY_CHAIN_DIGEST_SBOM_MANIFEST_URL: _FakeResponse(
                200,
                json_body=MOCK_SPDX_SBOM_MANIFEST,
            ),
            MOCK_SUPPLY_CHAIN_DIGEST_SBOM_BLOB_URL: _FakeResponse(
                200,
                json_body=mock_spdx_parent_image_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST),
            ),
        },
    )

    result, fetch_failed = await _process_single_image(
        client,
        _fake_token_manager(),
        {
            "name": MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME,
            "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
        },
        {
            MOCK_SUPPLY_CHAIN_IMAGE_DIGEST: [
                {
                    "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
                    "tags": [
                        f"sha256-{MOCK_SUPPLY_CHAIN_IMAGE_DIGEST_HEX}.sbom",
                    ],
                }
            ]
        },
    )

    assert fetch_failed is False
    assert result["digest"] == MOCK_SUPPLY_CHAIN_IMAGE_DIGEST
    assert result["parent_image_uri"] == MOCK_SUPPLY_CHAIN_PARENT_IMAGE_URI
    assert result["parent_image_digest"] == MOCK_SUPPLY_CHAIN_PARENT_IMAGE_DIGEST
    assert "source_uri" not in result


@pytest.mark.asyncio
async def test_process_single_image_returns_parent_only_spdx_provenance():
    client = _FakeClient(
        {
            MOCK_SUPPLY_CHAIN_IMAGE_MANIFEST_URL: _FakeResponse(
                200,
                json_body=MOCK_SINGLE_IMAGE_MANIFEST,
                headers={"Docker-Content-Digest": MOCK_SUPPLY_CHAIN_IMAGE_DIGEST},
            ),
            MOCK_SUPPLY_CHAIN_IMAGE_CONFIG_URL: _FakeResponse(
                200,
                json_body={"config": {"Labels": {}}},
            ),
            MOCK_SUPPLY_CHAIN_IMAGE_REFERRERS_URL: _FakeResponse(
                200,
                json_body={"manifests": []},
            ),
            MOCK_SUPPLY_CHAIN_DIGEST_SBOM_MANIFEST_URL: _FakeResponse(
                200,
                json_body=MOCK_SPDX_SBOM_MANIFEST,
            ),
            MOCK_SUPPLY_CHAIN_DIGEST_SBOM_BLOB_URL: _FakeResponse(
                200,
                json_body=mock_spdx_parent_image_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST),
            ),
        },
    )

    result, fetch_failed = await _process_single_image(
        client,
        _fake_token_manager(),
        {
            "name": MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME,
            "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
        },
        {
            MOCK_SUPPLY_CHAIN_IMAGE_DIGEST: [
                {
                    "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
                    "tags": [
                        f"sha256-{MOCK_SUPPLY_CHAIN_IMAGE_DIGEST_HEX}.sbom",
                    ],
                }
            ]
        },
    )

    assert fetch_failed is False
    assert result == {
        "digest": MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
        "type": "image",
        "media_type": "application/vnd.oci.image.manifest.v1+json",
        "layer_diff_ids": [],
        "parent_image_uri": MOCK_SUPPLY_CHAIN_PARENT_IMAGE_URI,
        "parent_image_digest": MOCK_SUPPLY_CHAIN_PARENT_IMAGE_DIGEST,
    }


@pytest.mark.asyncio
async def test_process_single_image_fetches_spdx_parent_when_config_has_source():
    client = _FakeClient(
        {
            MOCK_SUPPLY_CHAIN_IMAGE_MANIFEST_URL: _FakeResponse(
                200,
                json_body=MOCK_SINGLE_IMAGE_MANIFEST,
                headers={"Docker-Content-Digest": MOCK_SUPPLY_CHAIN_IMAGE_DIGEST},
            ),
            MOCK_SUPPLY_CHAIN_IMAGE_CONFIG_URL: _FakeResponse(
                200,
                json_body=MOCK_SINGLE_IMAGE_CONFIG,
            ),
            MOCK_SUPPLY_CHAIN_DIGEST_SBOM_MANIFEST_URL: _FakeResponse(
                200,
                json_body=MOCK_SPDX_SBOM_MANIFEST,
            ),
            MOCK_SUPPLY_CHAIN_DIGEST_SBOM_BLOB_URL: _FakeResponse(
                200,
                json_body=mock_spdx_parent_image_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST),
            ),
        },
    )

    result, fetch_failed = await _process_single_image(
        client,
        _fake_token_manager(),
        {
            "name": MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME,
            "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
        },
        {
            MOCK_SUPPLY_CHAIN_IMAGE_DIGEST: [
                {
                    "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
                    "tags": [
                        f"sha256-{MOCK_SUPPLY_CHAIN_IMAGE_DIGEST_HEX}.sbom",
                    ],
                }
            ]
        },
    )

    assert fetch_failed is False
    assert result["source_uri"] == "https://github.com/example/widgets"
    assert result["parent_image_digest"] == MOCK_SUPPLY_CHAIN_PARENT_IMAGE_DIGEST


@pytest.mark.asyncio
async def test_process_single_image_falls_back_to_tagged_spdx_sbom_artifact():
    client = _FakeClient(
        {
            MOCK_SUPPLY_CHAIN_IMAGE_MANIFEST_URL: _FakeResponse(
                200,
                json_body=MOCK_SINGLE_IMAGE_MANIFEST,
                headers={"Docker-Content-Digest": MOCK_SUPPLY_CHAIN_IMAGE_DIGEST},
            ),
            MOCK_SUPPLY_CHAIN_IMAGE_CONFIG_URL: _FakeResponse(
                200,
                json_body=mock_single_image_config_without_labels(),
            ),
            MOCK_SUPPLY_CHAIN_IMAGE_REFERRERS_URL: _FakeResponse(
                200,
                json_body={"manifests": []},
            ),
            MOCK_SUPPLY_CHAIN_SBOM_MANIFEST_URL: _FakeResponse(
                200,
                json_body=MOCK_SPDX_SBOM_MANIFEST,
            ),
            MOCK_SUPPLY_CHAIN_SBOM_BLOB_URL: _FakeResponse(
                200,
                json_body=mock_ko_spdx_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST),
            ),
        },
    )

    result, fetch_failed = await _process_single_image(
        client,
        _fake_token_manager(),
        {
            "name": MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME,
            "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
        },
        {
            MOCK_SUPPLY_CHAIN_IMAGE_DIGEST: [
                {
                    "uri": MOCK_SUPPLY_CHAIN_SBOM_URI,
                    "tags": [
                        f"sha256-{MOCK_SUPPLY_CHAIN_IMAGE_DIGEST_HEX}.sbom",
                    ],
                }
            ]
        },
    )

    assert fetch_failed is False
    assert result["digest"] == MOCK_SUPPLY_CHAIN_IMAGE_DIGEST
    assert result["source_uri"] == "https://github.com/example/widgets"
    assert MOCK_SUPPLY_CHAIN_DIGEST_SBOM_MANIFEST_URL not in client.calls


@pytest.mark.asyncio
async def test_process_single_image_tries_all_tagged_spdx_sbom_artifacts():
    client = _FakeClient(
        {
            MOCK_SUPPLY_CHAIN_IMAGE_MANIFEST_URL: _FakeResponse(
                200,
                json_body=MOCK_SINGLE_IMAGE_MANIFEST,
                headers={"Docker-Content-Digest": MOCK_SUPPLY_CHAIN_IMAGE_DIGEST},
            ),
            MOCK_SUPPLY_CHAIN_IMAGE_CONFIG_URL: _FakeResponse(
                200,
                json_body=mock_single_image_config_without_labels(),
            ),
            MOCK_SUPPLY_CHAIN_IMAGE_REFERRERS_URL: _FakeResponse(
                200,
                json_body={"manifests": []},
            ),
            MOCK_SUPPLY_CHAIN_SBOM_MANIFEST_URL: _FakeResponse(
                200,
                json_body=MOCK_SPDX_SBOM_MANIFEST,
            ),
            MOCK_SUPPLY_CHAIN_SBOM_BLOB_URL: _FakeResponse(
                200,
                json_body=mock_ko_spdx_sbom(MOCK_SUPPLY_CHAIN_IMAGE_DIGEST),
            ),
        },
    )

    result, fetch_failed = await _process_single_image(
        client,
        _fake_token_manager(),
        {
            "name": MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME,
            "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
        },
        {
            MOCK_SUPPLY_CHAIN_IMAGE_DIGEST: [
                {
                    "uri": MOCK_SUPPLY_CHAIN_MISSING_SBOM_URI,
                    "tags": [
                        f"sha256-{MOCK_SUPPLY_CHAIN_IMAGE_DIGEST_HEX}.sbom",
                    ],
                },
                {
                    "uri": MOCK_SUPPLY_CHAIN_SBOM_URI,
                    "tags": [
                        f"sha256-{MOCK_SUPPLY_CHAIN_IMAGE_DIGEST_HEX}.sbom",
                    ],
                },
            ]
        },
    )

    assert fetch_failed is False
    assert result["digest"] == MOCK_SUPPLY_CHAIN_IMAGE_DIGEST
    assert result["source_uri"] == "https://github.com/example/widgets"


@pytest.mark.asyncio
async def test_process_single_image_treats_missing_tagged_spdx_sbom_as_noop():
    client = _FakeClient(
        {
            MOCK_SUPPLY_CHAIN_IMAGE_MANIFEST_URL: _FakeResponse(
                200,
                json_body=MOCK_SINGLE_IMAGE_MANIFEST,
                headers={"Docker-Content-Digest": MOCK_SUPPLY_CHAIN_IMAGE_DIGEST},
            ),
            MOCK_SUPPLY_CHAIN_IMAGE_CONFIG_URL: _FakeResponse(
                200,
                json_body=mock_single_image_config_without_labels(),
            ),
            MOCK_SUPPLY_CHAIN_IMAGE_REFERRERS_URL: _FakeResponse(
                200,
                json_body={"manifests": []},
            ),
        },
    )

    result, fetch_failed = await _process_single_image(
        client,
        _fake_token_manager(),
        {
            "name": MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME,
            "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
        },
        {
            MOCK_SUPPLY_CHAIN_IMAGE_DIGEST: [
                {
                    "uri": MOCK_SUPPLY_CHAIN_SBOM_URI,
                    "tags": [
                        f"sha256-{MOCK_SUPPLY_CHAIN_IMAGE_DIGEST_HEX}.sbom",
                    ],
                }
            ]
        },
    )

    assert fetch_failed is False
    assert result["digest"] == MOCK_SUPPLY_CHAIN_IMAGE_DIGEST
    assert "source_uri" not in result


@pytest.mark.asyncio
async def test_process_single_image_skips_manifest_list():
    client = MagicMock()

    result, fetch_failed = await _process_single_image(
        client,
        _fake_token_manager(),
        {
            "name": MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME,
            "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
            "mediaType": "application/vnd.oci.image.index.v1+json",
        },
    )

    assert result is None
    assert fetch_failed is False
    client.get.assert_not_called()


# ---------------------------------------------------------------------------
# Referrers / DSSE attestation discovery
# ---------------------------------------------------------------------------


class _FakeResponse:
    def __init__(self, status_code, json_body=None, headers=None):
        self.status_code = status_code
        self._json = json_body
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"{self.status_code}",
                request=httpx.Request("GET", "https://example.test"),
                response=httpx.Response(self.status_code),
            )

    def json(self):
        return self._json


class _FakeClient:
    def __init__(self, responses_by_url):
        self._responses = responses_by_url
        self.calls = []

    async def get(self, url, headers=None, timeout=None):
        self.calls.append(url)
        if url not in self._responses:
            return _FakeResponse(404)
        return self._responses[url]


def _fake_credentials(token="abc", quota_project_id=None):
    """Build a MagicMock that mimics google-auth Credentials.apply()."""
    creds = MagicMock()
    creds.token = token
    creds.quota_project_id = quota_project_id

    def _apply(headers, token=None):
        headers["Authorization"] = f"Bearer {creds.token}"
        if creds.quota_project_id:
            headers["x-goog-user-project"] = creds.quota_project_id

    creds.apply.side_effect = _apply
    return creds


def _fake_token_manager():
    return _TokenManager(_fake_credentials())


@pytest.mark.asyncio
async def test_fetch_legacy_sbom_provenance_returns_empty_on_404():
    provenance = await _fetch_legacy_sbom_provenance(
        _FakeClient({}),
        _fake_token_manager(),
        registry="us-docker.pkg.dev",
        image_path="proj/repo/img",
        image_digest="sha256:deadbeef",
    )

    assert provenance == {}


@pytest.mark.asyncio
async def test_fetch_attestation_provenance_returns_empty_on_404():
    client = _FakeClient({})

    provenance = await _fetch_attestation_provenance(
        client,
        _fake_token_manager(),
        registry="us-docker.pkg.dev",
        image_path="proj/repo/img",
        image_digest="sha256:deadbeef",
    )

    assert provenance == {}


@pytest.mark.asyncio
async def test_fetch_attestation_provenance_decodes_dsse_envelope():
    import base64

    statement = {
        "predicate": {
            "buildDefinition": {
                "externalParameters": {
                    "source": "https://github.com/foo/bar.git",
                },
            },
        },
    }
    payload_b64 = base64.b64encode(json.dumps(statement).encode()).decode()

    referrers_url = (
        "https://us-docker.pkg.dev/v2/proj/repo/img/referrers/sha256:deadbeef"
    )
    att_manifest_url = (
        "https://us-docker.pkg.dev/v2/proj/repo/img/manifests/sha256:att1"
    )
    blob_url = "https://us-docker.pkg.dev/v2/proj/repo/img/blobs/sha256:layer1"

    responses = {
        referrers_url: _FakeResponse(
            200,
            json_body={
                "manifests": [
                    {
                        "artifactType": "application/vnd.dev.sigstore.bundle.v1+json.slsa-provenance",
                        "digest": "sha256:att1",
                    }
                ]
            },
        ),
        att_manifest_url: _FakeResponse(
            200,
            json_body={
                "layers": [
                    {
                        "mediaType": "application/vnd.in-toto+json",
                        "digest": "sha256:layer1",
                    }
                ]
            },
        ),
        blob_url: _FakeResponse(200, json_body={"payload": payload_b64}),
    }
    client = _FakeClient(responses)

    provenance = await _fetch_attestation_provenance(
        client,
        _fake_token_manager(),
        registry="us-docker.pkg.dev",
        image_path="proj/repo/img",
        image_digest="sha256:deadbeef",
    )

    assert provenance.get("source_uri") == "https://github.com/foo/bar"


# ---------------------------------------------------------------------------
# Token refresh on 401
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_json_refreshes_token_on_401():
    creds = _fake_credentials(token="first-token")

    def _refresh(_request):
        creds.token = "second-token"

    creds.refresh.side_effect = _refresh
    manager = _TokenManager(creds)

    calls = []

    async def fake_get(url, headers=None, timeout=None):
        calls.append(headers["Authorization"])
        if len(calls) == 1:
            return _FakeResponse(401)
        return _FakeResponse(200, json_body={"ok": True})

    client = MagicMock()
    client.get = fake_get

    result = await supply_chain._fetch_json(
        client, "https://example.test/v2/x", manager
    )

    assert result == {"ok": True}
    assert calls == ["Bearer first-token", "Bearer second-token"]
    assert manager.generation == 1


@pytest.mark.asyncio
async def test_fetch_json_applies_quota_project_header():
    creds = _fake_credentials(token="t", quota_project_id="my-quota-proj")
    manager = _TokenManager(creds)

    captured: dict[str, str] = {}

    async def fake_get(url, headers=None, timeout=None):
        captured.update(headers)
        return _FakeResponse(200, json_body={"ok": True})

    client = MagicMock()
    client.get = fake_get

    await supply_chain._fetch_json(client, "https://example.test/v2/x", manager)

    assert captured.get("Authorization") == "Bearer t"
    assert captured.get("x-goog-user-project") == "my-quota-proj"


# ---------------------------------------------------------------------------
# BuildKit attestations embedded in image indexes
# ---------------------------------------------------------------------------


EXPECTED_BUILDKIT_PROVENANCE = {
    "source_uri": "https://github.com/example-org/widgets",
    "source_revision": "1111111111111111111111111111111111111111",
    "source_file": "services/api/Dockerfile",
}


def test_embedded_attestation_refs_reads_unknown_platform_entries():
    refs = supply_chain._embedded_attestation_refs(
        [MOCK_BUILDKIT_INDEX_ARTIFACT],
        skip_subject_digests=set(),
    )

    assert refs == [
        (
            "us-central1-docker.pkg.dev",
            "test-project/docker-repo/widgets-api",
            MOCK_BUILDKIT_ATTESTATION_DIGEST,
        ),
    ]


def test_embedded_attestation_refs_skips_index_with_known_source_file():
    refs = supply_chain._embedded_attestation_refs(
        [MOCK_BUILDKIT_INDEX_ARTIFACT],
        skip_subject_digests={MOCK_SUPPLY_CHAIN_IMAGE_DIGEST},
    )

    assert refs == []


@pytest.mark.asyncio
async def test_fetch_embedded_attestation_provenance_maps_to_subject_digest():
    client = _FakeClient(
        {
            MOCK_BUILDKIT_ATTESTATION_MANIFEST_URL: _FakeResponse(
                200, json_body=MOCK_BUILDKIT_ATTESTATION_MANIFEST
            ),
            MOCK_BUILDKIT_PROVENANCE_BLOB_URL: _FakeResponse(
                200, json_body=MOCK_BUILDKIT_PROVENANCE_STATEMENT
            ),
        },
    )

    provenance = await supply_chain._fetch_embedded_attestation_provenance(
        client,
        _fake_token_manager(),
        "us-central1-docker.pkg.dev",
        "test-project/docker-repo/widgets-api",
        MOCK_BUILDKIT_ATTESTATION_DIGEST,
    )

    assert provenance == {MOCK_SUPPLY_CHAIN_IMAGE_DIGEST: EXPECTED_BUILDKIT_PROVENANCE}


@pytest.mark.asyncio
async def test_fetch_embedded_attestation_provenance_ignores_non_slsa_layers():
    manifest = json.loads(json.dumps(MOCK_BUILDKIT_ATTESTATION_MANIFEST))
    manifest["layers"][0]["annotations"] = {
        "in-toto.io/predicate-type": "https://spdx.dev/Document",
    }
    client = _FakeClient(
        {
            MOCK_BUILDKIT_ATTESTATION_MANIFEST_URL: _FakeResponse(
                200, json_body=manifest
            ),
        },
    )

    provenance = await supply_chain._fetch_embedded_attestation_provenance(
        client,
        _fake_token_manager(),
        "us-central1-docker.pkg.dev",
        "test-project/docker-repo/widgets-api",
        MOCK_BUILDKIT_ATTESTATION_DIGEST,
    )

    assert provenance == {}
    assert MOCK_BUILDKIT_PROVENANCE_BLOB_URL not in client.calls


@pytest.mark.asyncio
async def test_fetch_embedded_attestation_provenance_returns_empty_on_404():
    provenance = await supply_chain._fetch_embedded_attestation_provenance(
        _FakeClient({}),
        _fake_token_manager(),
        "us-central1-docker.pkg.dev",
        "test-project/docker-repo/widgets-api",
        MOCK_BUILDKIT_ATTESTATION_DIGEST,
    )

    assert provenance == {}


@pytest.mark.asyncio
async def test_process_single_image_prefers_slsa_over_inherited_labels():
    client = _FakeClient(
        {
            MOCK_SUPPLY_CHAIN_IMAGE_MANIFEST_URL: _FakeResponse(
                200,
                json_body=MOCK_SINGLE_IMAGE_MANIFEST,
                headers={"Docker-Content-Digest": MOCK_SUPPLY_CHAIN_IMAGE_DIGEST},
            ),
            MOCK_SUPPLY_CHAIN_IMAGE_CONFIG_URL: _FakeResponse(
                200,
                json_body=mock_single_image_config_with_inherited_labels(),
            ),
        },
    )

    result, fetch_failed = await _process_single_image(
        client,
        _fake_token_manager(),
        {
            "name": MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME,
            "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
        },
        embedded_provenance={
            MOCK_SUPPLY_CHAIN_IMAGE_DIGEST: EXPECTED_BUILDKIT_PROVENANCE,
        },
    )

    assert fetch_failed is False
    assert result is not None
    assert {
        field: result.get(field)
        for field in ("source_uri", "source_revision", "source_file")
    } == EXPECTED_BUILDKIT_PROVENANCE
    assert result["provenance_from_slsa"] is True
    assert MOCK_SUPPLY_CHAIN_IMAGE_REFERRERS_URL not in client.calls


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "complete_digests",
        "provenance_complete_names",
        "embedded_provenance",
        "process_failed",
        "expected_processed",
        "expected_versions",
    ),
    [
        (
            set(),
            set(),
            {MOCK_SUPPLY_CHAIN_IMAGE_DIGEST: EXPECTED_BUILDKIT_PROVENANCE},
            False,
            [
                (
                    MOCK_SUPPLY_CHAIN_IMAGE_URI,
                    True,
                    {MOCK_SUPPLY_CHAIN_IMAGE_DIGEST: EXPECTED_BUILDKIT_PROVENANCE},
                ),
            ],
            {MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME: GAR_PROVENANCE_VERSION},
        ),
        (
            set(),
            set(),
            {},
            False,
            [(MOCK_SUPPLY_CHAIN_IMAGE_URI, True, {})],
            {MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME: GAR_PROVENANCE_VERSION},
        ),
        # Layers are complete but this repository image was never stamped: rerun
        # its referrer and SBOM lookups without refetching the config.
        (
            {MOCK_SUPPLY_CHAIN_IMAGE_DIGEST},
            set(),
            {},
            False,
            [(MOCK_SUPPLY_CHAIN_IMAGE_URI, False, {})],
            {MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME: GAR_PROVENANCE_VERSION},
        ),
        # A failed pass clears the stamp, so the next sync reads it again.
        (
            {MOCK_SUPPLY_CHAIN_IMAGE_DIGEST},
            set(),
            {},
            True,
            [(MOCK_SUPPLY_CHAIN_IMAGE_URI, False, {})],
            {MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME: None},
        ),
        (
            {MOCK_SUPPLY_CHAIN_IMAGE_DIGEST},
            {MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME},
            {},
            False,
            [],
            {},
        ),
        # A stamp does not stand in for missing layers.
        (
            set(),
            {MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME},
            {},
            False,
            [(MOCK_SUPPLY_CHAIN_IMAGE_URI, True, {})],
            {MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME: GAR_PROVENANCE_VERSION},
        ),
        (
            {MOCK_SUPPLY_CHAIN_IMAGE_DIGEST},
            {MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME},
            {MOCK_SUPPLY_CHAIN_IMAGE_DIGEST: EXPECTED_BUILDKIT_PROVENANCE},
            False,
            [
                (
                    MOCK_SUPPLY_CHAIN_IMAGE_URI,
                    False,
                    {MOCK_SUPPLY_CHAIN_IMAGE_DIGEST: EXPECTED_BUILDKIT_PROVENANCE},
                ),
            ],
            {MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME: GAR_PROVENANCE_VERSION},
        ),
    ],
    ids=[
        "new_digest_with_embedded_provenance",
        "new_digest",
        "complete_layers_without_stamp",
        "failed_pass",
        "stamped",
        "stamped_without_complete_layers",
        "stamped_with_embedded_provenance",
    ],
)
async def test_fetch_all_image_provenance_uses_embedded_attestations(
    monkeypatch,
    complete_digests,
    provenance_complete_names,
    embedded_provenance,
    process_failed,
    expected_processed,
    expected_versions,
):
    credentials = MagicMock()
    credentials.valid = True
    monkeypatch.setattr(supply_chain, "_resolve_credentials", lambda _: credentials)
    embedded_fetch = AsyncMock(return_value=embedded_provenance)
    monkeypatch.setattr(
        supply_chain,
        "_fetch_embedded_attestation_provenance",
        embedded_fetch,
    )
    processed = []

    async def _fake_process(_client, _token_manager, artifact, *_args, **kwargs):
        processed.append(
            (artifact["uri"], kwargs["fetch_config"], kwargs["embedded_provenance"]),
        )
        return None, process_failed

    monkeypatch.setattr(supply_chain, "_process_single_image", _fake_process)

    _, _, provenance_versions = await supply_chain._fetch_all_image_provenance(
        None,
        [
            MOCK_BUILDKIT_INDEX_ARTIFACT,
            MOCK_BUILDKIT_ATTESTATION_ARTIFACT,
            {
                "name": MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME,
                "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
            },
        ],
        "test-project",
        complete_digests=complete_digests,
        provenance_complete_names=provenance_complete_names,
    )

    embedded_fetch.assert_awaited_once()
    assert embedded_fetch.await_args.args[2:] == (
        "us-central1-docker.pkg.dev",
        "test-project/docker-repo/widgets-api",
        MOCK_BUILDKIT_ATTESTATION_DIGEST,
    )
    # The attestation manifest is never enriched as if it were a runnable image, and
    # a stamped repository image with complete layers is skipped unless embedded
    # provenance needs applying.
    assert processed == expected_processed
    assert provenance_versions == expected_versions


def test_load_image_provenance_slsa_replaces_label_source(monkeypatch):
    load_nodes_without_relationships = MagicMock()
    monkeypatch.setattr(
        supply_chain,
        "load_nodes_without_relationships",
        load_nodes_without_relationships,
    )
    monkeypatch.setattr(supply_chain, "load_matchlinks_with_progress", MagicMock())
    neo4j_session = MagicMock()
    neo4j_session.execute_read.return_value = [
        {
            "digest": MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
            "source_uri": "https://github.com/example-base/base-images",
            "source_revision": "2222222222222222222222222222222222222222",
            "source_file": None,
        },
    ]

    supply_chain.load_image_provenance(
        neo4j_session,
        [
            {
                "digest": MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
                **EXPECTED_BUILDKIT_PROVENANCE,
                "provenance_from_slsa": True,
            },
        ],
        "proj",
        1,
    )

    loaded = load_nodes_without_relationships.call_args.args[2]
    assert {
        field: loaded[0][field]
        for field in ("source_uri", "source_revision", "source_file")
    } == EXPECTED_BUILDKIT_PROVENANCE
    assert "provenance_from_slsa" not in loaded[0]


@pytest.mark.asyncio
async def test_process_single_image_prefers_referrers_slsa_over_labels(monkeypatch):
    client = _FakeClient(
        {
            MOCK_SUPPLY_CHAIN_IMAGE_MANIFEST_URL: _FakeResponse(
                200,
                json_body=MOCK_SINGLE_IMAGE_MANIFEST,
                headers={"Docker-Content-Digest": MOCK_SUPPLY_CHAIN_IMAGE_DIGEST},
            ),
            MOCK_SUPPLY_CHAIN_IMAGE_CONFIG_URL: _FakeResponse(
                200,
                json_body=mock_single_image_config_with_inherited_labels(),
            ),
        },
    )
    referrers_fetch = AsyncMock(return_value=EXPECTED_BUILDKIT_PROVENANCE)
    monkeypatch.setattr(supply_chain, "_fetch_attestation_provenance", referrers_fetch)

    result, fetch_failed = await _process_single_image(
        client,
        _fake_token_manager(),
        {
            "name": MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME,
            "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
        },
    )

    referrers_fetch.assert_awaited_once()
    assert fetch_failed is False
    assert result is not None
    assert {
        field: result.get(field)
        for field in ("source_uri", "source_revision", "source_file")
    } == EXPECTED_BUILDKIT_PROVENANCE
    assert result["provenance_from_slsa"] is True


@pytest.mark.asyncio
async def test_fetch_all_image_provenance_counts_attestation_failures(monkeypatch):
    credentials = MagicMock()
    credentials.valid = True
    monkeypatch.setattr(supply_chain, "_resolve_credentials", lambda _: credentials)
    monkeypatch.setattr(
        supply_chain,
        "_fetch_embedded_attestation_provenance",
        AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "503",
                request=httpx.Request("GET", "https://example.test"),
                response=httpx.Response(503),
            ),
        ),
    )
    processed = []

    async def _fake_process(_client, _token_manager, artifact, *_args, **kwargs):
        processed.append(kwargs["embedded_provenance"])
        return None, False

    monkeypatch.setattr(supply_chain, "_process_single_image", _fake_process)

    _, fetch_failures, _ = await supply_chain._fetch_all_image_provenance(
        None,
        [
            MOCK_BUILDKIT_INDEX_ARTIFACT,
            {
                "name": MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME,
                "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
            },
        ],
        "test-project",
    )

    assert fetch_failures == 1
    assert processed == [{}]


@pytest.mark.asyncio
async def test_fetch_all_image_provenance_skips_repository_after_403(
    monkeypatch,
    caplog,
):
    # Arrange
    credentials = MagicMock()
    credentials.valid = True
    monkeypatch.setattr(supply_chain, "_resolve_credentials", lambda _: credentials)
    denied_prefix = "/v2/test-project/denied-repo/"
    allowed_responses = {
        MOCK_SUPPLY_CHAIN_IMAGE_MANIFEST_URL: httpx.Response(
            200,
            json=MOCK_SINGLE_IMAGE_MANIFEST,
            headers={"Docker-Content-Digest": MOCK_SUPPLY_CHAIN_IMAGE_DIGEST},
        ),
        MOCK_SUPPLY_CHAIN_IMAGE_CONFIG_URL: httpx.Response(
            200,
            json=MOCK_SINGLE_IMAGE_CONFIG,
        ),
    }
    denied_requests = []

    def registry(request):
        if request.url.path.startswith(denied_prefix):
            denied_requests.append(request.url.path)
            return httpx.Response(403)
        return allowed_responses.get(str(request.url), httpx.Response(404))

    real_async_client = httpx.AsyncClient
    monkeypatch.setattr(
        supply_chain.httpx,
        "AsyncClient",
        lambda **kwargs: real_async_client(
            transport=httpx.MockTransport(registry),
            **kwargs,
        ),
    )
    denied_images = [
        {
            "uri": "us-central1-docker.pkg.dev/test-project/denied-repo/"
            f"image-{i}@sha256:{i:064x}",
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
        }
        for i in range(3)
    ]
    allowed_image = {
        "name": MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME,
        "uri": MOCK_SUPPLY_CHAIN_IMAGE_URI,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
    }

    # Act
    results, fetch_failures, _ = await supply_chain._fetch_all_image_provenance(
        None,
        [*denied_images, allowed_image],
        "test-project",
        max_concurrent=1,
    )

    # Assert
    assert denied_requests == [
        f"{denied_prefix}image-0/manifests/sha256:{0:064x}",
    ]
    assert [result["digest"] for result in results] == [
        MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
    ]
    assert fetch_failures == len(denied_images)
    assert [
        record.getMessage()
        for record in caplog.records
        if record.levelname == "WARNING"
    ] == [
        "Could not enrich 3 artifact(s) in Artifact Registry repository "
        "us-central1-docker.pkg.dev/test-project/denied-repo: access denied "
        "(HTTP 403).",
    ]
