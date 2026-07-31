from unittest.mock import patch

import requests

import cartography.intel.nullify.findings
import tests.data.nullify.findings
from tests.integration.cartography.intel.nullify.test_repositories import (
    _ensure_local_neo4j_has_test_repositories,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TENANT = "acme"

_FINDINGS_BY_PATH = {
    "/sast/findings": tests.data.nullify.findings.NULLIFY_SAST_FINDINGS,
    "/sca/dependencies/findings": tests.data.nullify.findings.NULLIFY_DEPENDENCY_FINDINGS,
    "/sca/containers/findings": tests.data.nullify.findings.NULLIFY_CONTAINER_FINDINGS,
    "/secrets/findings": tests.data.nullify.findings.NULLIFY_SECRET_FINDINGS,
    "/cspm/findings": tests.data.nullify.findings.NULLIFY_CSPM_FINDINGS,
}


def _fake_paginate(api_session, url, data_key, params=None):
    for path, findings in _FINDINGS_BY_PATH.items():
        if url.endswith(path):
            return findings
    raise AssertionError(f"unexpected findings URL: {url}")


@patch.object(
    cartography.intel.nullify.findings, "paginate", side_effect=_fake_paginate
)
def test_load_nullify_findings(mock_paginate, neo4j_session):
    # Arrange
    api_session = requests.Session()
    base_url = "https://api.acme.nullify.ai"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT,
        "BASE_URL": base_url,
    }
    _ensure_local_neo4j_has_test_repositories(neo4j_session)
    # Seed a CVE the dependency finding should link to.
    neo4j_session.run("MERGE (:CVE {id: 'CVE-2023-32681'})")
    neo4j_session.run("MERGE (:CVE {id: 'CVE-2022-0778'})")

    # Act
    for fn in (
        cartography.intel.nullify.findings.sync_sast_findings,
        cartography.intel.nullify.findings.sync_dependency_findings,
        cartography.intel.nullify.findings.sync_container_findings,
        cartography.intel.nullify.findings.sync_secret_findings,
        cartography.intel.nullify.findings.sync_cspm_findings,
    ):
        fn(
            neo4j_session,
            api_session,
            base_url,
            TEST_TENANT,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

    # Assert each finding type is present
    assert check_nodes(neo4j_session, "NullifySASTFinding", ["id"]) == {
        ("S1",),
        ("S2",),
    }
    assert check_nodes(neo4j_session, "NullifyDependencyFinding", ["id"]) == {("D1",)}
    assert check_nodes(
        neo4j_session,
        "NullifyContainerFinding",
        ["id", "image_reference", "image_digest"],
    ) == {("C1", "docker.io/library/openssl:1.1.1k", "sha256:deadbeef")}
    assert check_nodes(neo4j_session, "NullifySecretFinding", ["id"]) == {("SEC1",)}
    assert check_nodes(neo4j_session, "NullifyCSPMFinding", ["id"]) == {("CSPM1",)}

    # Assert findings are scoped to the tenant
    assert check_rels(
        neo4j_session,
        "NullifySASTFinding",
        "id",
        "NullifyTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {("S1", TEST_TENANT), ("S2", TEST_TENANT)}

    # Assert repo-scoped findings link to their NullifyRepository
    assert check_rels(
        neo4j_session,
        "NullifySASTFinding",
        "id",
        "NullifyRepository",
        "repository_id",
        "FOUND_IN",
        rel_direction_right=True,
    ) == {("S1", "R1"), ("S2", "R2")}

    assert check_rels(
        neo4j_session,
        "NullifySecretFinding",
        "id",
        "NullifyRepository",
        "repository_id",
        "FOUND_IN",
        rel_direction_right=True,
    ) == {("SEC1", "R1")}

    # Assert dependency + container findings link to CVEs
    assert check_rels(
        neo4j_session,
        "NullifyDependencyFinding",
        "id",
        "CVE",
        "id",
        "HAS_CVE",
        rel_direction_right=True,
    ) == {("D1", "CVE-2023-32681")}

    assert check_rels(
        neo4j_session,
        "NullifyContainerFinding",
        "id",
        "CVE",
        "id",
        "HAS_CVE",
        rel_direction_right=True,
    ) == {("C1", "CVE-2022-0778")}

    # CSPM findings hang off the tenant only (no repository linkage)
    assert check_rels(
        neo4j_session,
        "NullifyCSPMFinding",
        "id",
        "NullifyTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {("CSPM1", TEST_TENANT)}
