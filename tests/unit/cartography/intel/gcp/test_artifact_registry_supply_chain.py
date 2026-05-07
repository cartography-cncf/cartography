import json
from unittest.mock import MagicMock

import httpx
import pytest

from cartography.intel.gcp.artifact_registry import supply_chain
from cartography.intel.gcp.artifact_registry.supply_chain import _build_layer_dicts
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
from cartography.intel.supply_chain import extract_provenance_from_oci_config
from tests.data.gcp.artifact_registry import mock_ko_spdx_sbom
from tests.data.gcp.artifact_registry import MOCK_SINGLE_IMAGE_CONFIG
from tests.data.gcp.artifact_registry import mock_single_image_config_without_labels
from tests.data.gcp.artifact_registry import MOCK_SINGLE_IMAGE_MANIFEST
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
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_SBOM_BLOB_URL
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_SBOM_MANIFEST_URL
from tests.data.gcp.artifact_registry import MOCK_SUPPLY_CHAIN_SBOM_URI

# ---------------------------------------------------------------------------
# OCI label provenance
# ---------------------------------------------------------------------------


def test_extract_provenance_from_oci_config_reads_labels():
    config = {
        "config": {
            "Labels": {
                "org.opencontainers.image.source": "https://github.com/foo/bar.git",
                "org.opencontainers.image.revision": "deadbeef",
            },
        },
    }

    provenance = extract_provenance_from_oci_config(config)

    assert provenance["source_uri"] == "https://github.com/foo/bar"
    assert provenance["source_revision"] == "deadbeef"


def test_extract_provenance_from_oci_config_no_labels_returns_empty():
    assert extract_provenance_from_oci_config({"config": {}}) == {}


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
    monkeypatch.setattr(supply_chain, "load_image_provenance", MagicMock())
    monkeypatch.setattr(supply_chain, "load_image_layers", MagicMock())

    def _set_enrichments(enrichments, fetch_failures=0):
        async def _fake_fetch(*_args, **_kwargs):
            return enrichments, fetch_failures

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
                "layer_diff_ids": ["sha256:a", "sha256:b"],
                "architecture": None,
                "os": None,
                "os_version": None,
                "os_features": None,
                "variant": None,
            },
            {
                "digest": "sha256:img-2",
                "type": "image",
                "media_type": None,
                "source_uri": None,
                "source_revision": None,
                "source_file": None,
                "layer_diff_ids": ["sha256:a"],
                "architecture": None,
                "os": None,
                "os_version": None,
                "os_features": None,
                "variant": None,
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


def test_load_image_provenance_preserves_existing_values(monkeypatch):
    load_nodes_without_relationships = MagicMock()
    monkeypatch.setattr(
        supply_chain,
        "load_nodes_without_relationships",
        load_nodes_without_relationships,
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
            "layer_diff_ids": ["sha256:a"],
        },
    ]
    assert "provenance updates" in call.kwargs["progress_description"]
    assert call.kwargs["lastupdated"] == 1
    assert call.kwargs["PROJECT_ID"] == "proj"


def test_load_image_layers_uses_node_and_matchlink_progress_loaders(monkeypatch):
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
    layers = [{"diff_id": "sha256:a", "history": "FROM scratch"}]

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


def test_sync_runs_cleanup_when_safe_and_no_failures(patched_sync):
    set_enrichments, cleanup_runs = patched_sync
    set_enrichments(enrichments=[], fetch_failures=0)

    supply_chain.sync(
        neo4j_session=MagicMock(),
        credentials=MagicMock(),
        docker_artifacts_raw=[{"name": "img"}],
        project_id="proj",
        update_tag=1,
        common_job_parameters={},
        cleanup_safe=True,
    )

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
