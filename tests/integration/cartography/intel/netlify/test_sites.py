from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j
import requests

import cartography.intel.netlify.deploykeys
import cartography.intel.netlify.sites
import tests.data.netlify.deploykeys
import tests.data.netlify.sites
from tests.integration.cartography.intel.netlify.common import common_job_parameters
from tests.integration.cartography.intel.netlify.common import (
    create_test_netlify_account,
)
from tests.integration.cartography.intel.netlify.common import find_secret_in_graph
from tests.integration.cartography.intel.netlify.common import TEST_ACCOUNT_ID
from tests.integration.cartography.intel.netlify.common import TEST_BASE_URL
from tests.integration.cartography.intel.netlify.common import TEST_GIT_SITE_ID
from tests.integration.cartography.intel.netlify.common import TEST_SITE_ID
from tests.integration.cartography.intel.netlify.common import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

_REPO_FULLNAME = "exampleorg/example-git-site"
_DEPLOY_KEY_ID = "6b6b79a3aab81353de5d314f"


def _seed_join_targets(neo4j_session: neo4j.Session) -> None:
    """
    Create the nodes the site's best-effort edges point at.

    Both edges resolve through an OPTIONAL MATCH, so without these the site still loads and the
    edges are simply absent, which is what a Netlify-only deployment sees.
    """
    neo4j_session.run(
        """
        MERGE (r:GitHubRepository{fullname: $fullname})
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag, r.id = $fullname
        MERGE (k:NetlifyDeployKey{id: $key_id})
        ON CREATE SET k.firstseen = timestamp()
        SET k.lastupdated = $update_tag
        """,
        fullname=_REPO_FULLNAME,
        key_id=_DEPLOY_KEY_ID,
        update_tag=TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_test_sites(neo4j_session: neo4j.Session) -> None:
    cartography.intel.netlify.sites.load_netlify_sites(
        neo4j_session,
        cartography.intel.netlify.sites.transform_netlify_sites(
            tests.data.netlify.sites.NETLIFY_SITES_WITH_GIT,
        ),
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def test_sync_netlify_sites(neo4j_session: neo4j.Session) -> None:
    # Arrange
    create_test_netlify_account(neo4j_session)
    _seed_join_targets(neo4j_session)

    # Act: the entry point fetches the site list and loads the deploy keys first, so this takes
    # the already-fetched payloads.
    cartography.intel.netlify.sites.sync_netlify_sites(
        neo4j_session,
        tests.data.netlify.sites.NETLIFY_SITES_WITH_GIT,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert Nodes
    assert check_nodes(neo4j_session, "NetlifySite", ["id", "name", "state"]) == {
        (TEST_SITE_ID, "example-site", "current"),
        (TEST_GIT_SITE_ID, "example-git-site", "current"),
    }

    # Assert build_settings was flattened onto the git-connected site
    assert check_nodes(
        neo4j_session,
        "NetlifySite",
        ["id", "repo_path", "build_command", "publish_dir", "repo_public"],
    ) == {
        (TEST_SITE_ID, None, None, None, None),
        (TEST_GIT_SITE_ID, _REPO_FULLNAME, "npm run build", "dist", False),
    }

    # Assert Relationships
    assert check_rels(
        neo4j_session,
        "NetlifyAccount",
        "id",
        "NetlifySite",
        "id",
        "RESOURCE",
    ) == {
        (TEST_ACCOUNT_ID, TEST_SITE_ID),
        (TEST_ACCOUNT_ID, TEST_GIT_SITE_ID),
    }
    assert check_rels(
        neo4j_session,
        "NetlifySite",
        "id",
        "GitHubRepository",
        "fullname",
        "DEPLOYED_FROM",
    ) == {(TEST_GIT_SITE_ID, _REPO_FULLNAME)}
    assert check_rels(
        neo4j_session,
        "NetlifySite",
        "id",
        "NetlifyDeployKey",
        "id",
        "USES_DEPLOY_KEY",
    ) == {(TEST_GIT_SITE_ID, _DEPLOY_KEY_ID)}

    # Assert the ontology label and its projected properties
    assert check_nodes(
        neo4j_session,
        "ComputeService",
        ["id", "_ont_name", "_ont_status", "_ont_source"],
    ) == {
        (TEST_SITE_ID, "example-site", "active", "netlify"),
        (TEST_GIT_SITE_ID, "example-git-site", "active", "netlify"),
    }


def test_transform_netlify_sites_drops_the_jwt_secret() -> None:
    """
    `jwt_secret` signs Netlify Identity tokens, so only its presence may be ingested.
    """
    transformed = cartography.intel.netlify.sites.transform_netlify_sites(
        tests.data.netlify.sites.NETLIFY_SITES_WITH_GIT,
    )
    by_id = {site["id"]: site for site in transformed}

    assert by_id[TEST_GIT_SITE_ID]["has_jwt_secret"] is True
    assert by_id[TEST_SITE_ID]["has_jwt_secret"] is False


def test_netlify_site_never_stores_the_jwt_secret(
    neo4j_session: neo4j.Session,
) -> None:
    """
    Belt and braces: assert against the graph itself, not just the transform. `jwt_secret` is
    still a key on the transformed dict, so a future model that declares a PropertyRef for it
    would start persisting it, and this is what would catch that.
    """
    create_test_netlify_account(neo4j_session)
    _ensure_local_neo4j_has_test_sites(neo4j_session)

    assert find_secret_in_graph(neo4j_session, "super-secret-signing-key") == []


def test_first_sync_on_a_clean_graph_links_the_deploy_key(
    neo4j_session: neo4j.Session,
) -> None:
    """
    The site's USES_DEPLOY_KEY edge is resolved by a MATCH when the site row is written, so the key
    node has to exist first. This runs the entry point's real order on a clean graph with nothing
    pre-created, which is what test_sync_netlify_sites above cannot show because it seeds the key.
    """
    # Arrange: a genuinely empty graph, only the tenant
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_test_netlify_account(neo4j_session)
    sites = tests.data.netlify.sites.NETLIFY_SITES_WITH_GIT

    # Act: deploy keys before sites, as _sync_one_account does
    with patch.object(
        cartography.intel.netlify.deploykeys,
        "get_netlify_deploy_keys",
        return_value=tests.data.netlify.deploykeys.NETLIFY_DEPLOY_KEYS,
    ):
        cartography.intel.netlify.deploykeys.sync_netlify_deploy_keys(
            neo4j_session,
            MagicMock(spec=requests.Session),
            TEST_BASE_URL,
            TEST_ACCOUNT_ID,
            sites,
            TEST_UPDATE_TAG,
            common_job_parameters(),
        )
    cartography.intel.netlify.sites.sync_netlify_sites(
        neo4j_session,
        sites,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert: the edge exists on the very first sync
    assert check_rels(
        neo4j_session,
        "NetlifySite",
        "id",
        "NetlifyDeployKey",
        "id",
        "USES_DEPLOY_KEY",
    ) == {(TEST_GIT_SITE_ID, _DEPLOY_KEY_ID)}
