import json
from unittest.mock import MagicMock

import httpx
import pytest

from cartography.intel.gcp.artifact_registry import supply_chain
from cartography.intel.gcp.artifact_registry.supply_chain import _build_layer_dicts
from cartography.intel.gcp.artifact_registry.supply_chain import (
    _fetch_attestation_provenance,
)
from cartography.intel.gcp.artifact_registry.supply_chain import _TokenManager
from cartography.intel.supply_chain import extract_provenance_from_oci_config

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
    monkeypatch.setattr(supply_chain, "load", MagicMock())

    def _set_enrichments(enrichments, fetch_failures=0):
        async def _fake_fetch(*_args, **_kwargs):
            return enrichments, fetch_failures

        monkeypatch.setattr(supply_chain, "_fetch_all_image_provenance", _fake_fetch)

    return _set_enrichments, cleanup_runs


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

    assert len(cleanup_runs) == 1


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
        enrichments=[{"id": "img", "source_uri": "https://github.com/foo/bar"}],
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

    async def get(self, url, headers=None, timeout=None):
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
