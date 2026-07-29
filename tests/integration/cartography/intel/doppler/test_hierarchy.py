from unittest.mock import patch

import requests

import cartography.intel.doppler.configs
import cartography.intel.doppler.environments
import cartography.intel.doppler.projects
import cartography.intel.doppler.secrets
import cartography.intel.doppler.service_tokens
import cartography.intel.doppler.trusted_ips
import cartography.intel.doppler.workplace
import tests.data.doppler.doppler as data
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_WORKPLACE_ID = "wp1"


def _common():
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.doppler.com/v3",
        "WORKPLACE_ID": TEST_WORKPLACE_ID,
    }


@patch.object(
    cartography.intel.doppler.trusted_ips, "get", return_value=(data.TRUSTED_IPS, True)
)
@patch.object(
    cartography.intel.doppler.service_tokens,
    "get",
    return_value=(data.SERVICE_TOKENS, True),
)
@patch.object(
    cartography.intel.doppler.secrets, "get", return_value=(data.SECRETS, True)
)
@patch.object(cartography.intel.doppler.configs, "get", return_value=data.CONFIGS)
@patch.object(
    cartography.intel.doppler.environments, "get", return_value=data.ENVIRONMENTS
)
@patch.object(cartography.intel.doppler.projects, "get", return_value=data.PROJECTS)
@patch.object(cartography.intel.doppler.workplace, "get", return_value=data.WORKPLACE)
def test_doppler_hierarchy(
    mock_wp, mock_proj, mock_env, mock_conf, mock_sec, mock_tok, mock_ip, neo4j_session
):
    # Arrange
    api_session = requests.Session()
    common = _common()

    # Act
    workplace_id = cartography.intel.doppler.workplace.sync(
        neo4j_session, api_session, common
    )
    assert workplace_id == TEST_WORKPLACE_ID
    project_slugs = cartography.intel.doppler.projects.sync(
        neo4j_session, api_session, common
    )
    cartography.intel.doppler.environments.sync(
        neo4j_session, api_session, project_slugs, common
    )
    configs = cartography.intel.doppler.configs.sync(
        neo4j_session, api_session, project_slugs, common
    )
    cartography.intel.doppler.secrets.sync(neo4j_session, api_session, configs, common)
    cartography.intel.doppler.service_tokens.sync(
        neo4j_session, api_session, configs, common
    )
    cartography.intel.doppler.trusted_ips.sync(
        neo4j_session, api_session, configs, common
    )

    # Assert: tenant root
    assert check_nodes(neo4j_session, "DopplerWorkplace", ["id", "name"]) == {
        ("wp1", "Acme")
    }

    # Assert: project -> RESOURCE -> workplace
    assert check_rels(
        neo4j_session,
        "DopplerProject",
        "id",
        "DopplerWorkplace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {("p1", "wp1")}

    # Assert: config in environment, config belongs to project
    assert check_rels(
        neo4j_session,
        "DopplerProject",
        "slug",
        "DopplerConfig",
        "id",
        "HAS_CONFIG",
        rel_direction_right=True,
    ) == {("backend", "backend/dev")}
    assert check_rels(
        neo4j_session,
        "DopplerConfig",
        "id",
        "DopplerEnvironment",
        "id",
        "IN_ENVIRONMENT",
        rel_direction_right=True,
    ) == {("backend/dev", "backend/dev")}

    # Assert: secret name (no value) contained in config
    assert check_nodes(neo4j_session, "DopplerSecret", ["id", "name"]) == {
        ("backend/dev/DATABASE_URL", "DATABASE_URL")
    }
    assert check_rels(
        neo4j_session,
        "DopplerConfig",
        "id",
        "DopplerSecret",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {("backend/dev", "backend/dev/DATABASE_URL")}

    # Assert: service token + trusted ip on config
    assert check_rels(
        neo4j_session,
        "DopplerConfig",
        "id",
        "DopplerServiceToken",
        "id",
        "HAS_TOKEN",
        rel_direction_right=True,
    ) == {("backend/dev", "st1")}
    assert check_rels(
        neo4j_session,
        "DopplerConfig",
        "id",
        "DopplerTrustedIP",
        "id",
        "TRUSTS",
        rel_direction_right=True,
    ) == {("backend/dev", "backend/dev/10.0.0.0/8")}


def test_doppler_secret_has_no_value():
    # Guard: the secret model must never expose a raw/computed value property.
    from cartography.models.doppler.secret import DopplerSecretNodeProperties

    prop_names = set(vars(DopplerSecretNodeProperties()))
    assert not prop_names & {"raw", "computed", "value"}
