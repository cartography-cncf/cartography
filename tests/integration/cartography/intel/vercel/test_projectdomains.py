from unittest.mock import patch

import requests

import cartography.intel.vercel.projectdomains
import tests.data.vercel.projectdomains
from tests.integration.cartography.intel.vercel.test_domains import (
    _ensure_local_neo4j_has_test_domains,
)
from tests.integration.cartography.intel.vercel.test_projects import (
    _ensure_local_neo4j_has_test_projects,
)
from tests.integration.cartography.intel.vercel.test_teams import (
    _ensure_local_neo4j_has_test_teams,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TEAM_ID = "team_abc123"
TEST_BASE_URL = "https://api.fake-vercel.com"
TEST_PROJECT_ID = "prj_abc"


@patch.object(
    cartography.intel.vercel.projectdomains,
    "get",
    return_value=tests.data.vercel.projectdomains.VERCEL_PROJECT_DOMAINS,
)
def test_load_vercel_project_domains(mock_api, neo4j_session):
    """
    Ensure that per-project domains upsert VercelDomain nodes and create
    HAS_DOMAIN relationships from VercelProject with per-project properties.
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "TEAM_ID": TEST_TEAM_ID,
        "project_id": TEST_PROJECT_ID,
    }
    _ensure_local_neo4j_has_test_teams(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)
    # Pre-seed one of the team-level domains so we can assert the node is
    # not clobbered by the project-domain upsert.
    _ensure_local_neo4j_has_test_domains(neo4j_session)

    # Act
    cartography.intel.vercel.projectdomains.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        project_id=TEST_PROJECT_ID,
    )

    # Assert: both project-attached domains exist as VercelDomain nodes.
    # "example.com" was already pre-seeded by the team-level domains sync;
    # "www.example.com" is only referenced by the project, so it should be
    # upserted here with minimal fields.
    domain_ids = check_nodes(neo4j_session, "VercelDomain", ["id"])
    assert ("example.com",) in domain_ids
    assert ("www.example.com",) in domain_ids

    # Assert team-level fields survive the project-domain upsert
    team_domain = neo4j_session.run(
        "MATCH (d:VercelDomain {id: 'example.com'}) "
        "RETURN d.service_type AS service_type, d.verified AS verified",
    ).single()
    assert team_domain["service_type"] == "zeit.world"

    # Assert HAS_DOMAIN relationships from project to domains
    expected_rels = {
        (TEST_PROJECT_ID, "example.com"),
        (TEST_PROJECT_ID, "www.example.com"),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelProject",
            "id",
            "VercelDomain",
            "id",
            "HAS_DOMAIN",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert per-project properties are set on the relationship
    rel_props = neo4j_session.run(
        """
        MATCH (p:VercelProject {id: $pid})-[r:HAS_DOMAIN]->(d:VercelDomain {id: 'www.example.com'})
        RETURN r.redirect AS redirect, r.redirect_status_code AS status_code
        """,
        pid=TEST_PROJECT_ID,
    ).single()
    assert rel_props["redirect"] == "example.com"
    assert rel_props["status_code"] == 308
