from typing import Any
from unittest.mock import patch

import pytest

import cartography.intel.databricks
from cartography.config import Config
from tests.data.databricks.ingestion import catalog
from tests.data.databricks.ingestion import CATALOG_GRANT
from tests.data.databricks.ingestion import catalog_grant_uri
from tests.data.databricks.ingestion import CATALOGS_URI
from tests.data.databricks.ingestion import CLUSTER
from tests.data.databricks.ingestion import CLUSTERS_URI
from tests.data.databricks.ingestion import METASTORE_ID
from tests.data.databricks.ingestion import METASTORE_RESPONSES
from tests.data.databricks.ingestion import METASTORE_SUMMARY_URI
from tests.data.databricks.ingestion import USER
from tests.data.databricks.ingestion import USERS_URI
from tests.data.databricks.ingestion import WORKSPACE_A_HOST
from tests.data.databricks.ingestion import WORKSPACE_A_ID
from tests.data.databricks.ingestion import WORKSPACE_B_HOST
from tests.data.databricks.ingestion import WORKSPACE_B_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

OLD_TAG = 1
NEW_TAG = 2
# The one workspace endpoint whose empty answer is a list rather than a dict.
LIST_URIS = {"/api/2.0/preview/sql/data_sources"}


class FakeWorkspaceClient:
    """Answers each request from canned responses; unlisted URIs are empty.

    A response that is an exception is raised instead, to fail a sync partway.
    """

    def __init__(self, host: str, responses: dict[str, Any]) -> None:
        self.host = host
        self._responses = responses

    def _respond(self, uri: str, empty: Any) -> Any:
        response = self._responses.get(uri, empty)
        if isinstance(response, Exception):
            raise response
        return response

    def get(self, uri: str, params: dict | None = None) -> Any:
        return self._respond(uri, [] if uri in LIST_URIS else {})

    def uc_list(self, uri: str, key: str, params: dict | None = None) -> list:
        return self._respond(uri, [])

    def scim_list(self, uri: str) -> list:
        return self._respond(uri, [])


def _ingest(
    neo4j_session,
    host: str,
    responses: dict[str, Any],
    update_tag: int,
    skip_cleanup: bool = False,
) -> Any:
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        databricks_workspace_url=host,
        databricks_token="fake-token",
        databricks_skip_cleanup=skip_cleanup,
    )
    with patch.object(
        cartography.intel.databricks,
        "DatabricksWorkspaceClient",
        return_value=FakeWorkspaceClient(host, responses),
    ):
        return cartography.intel.databricks.start_databricks_ingestion(
            neo4j_session, config
        )


def _cluster_ids(neo4j_session):
    return check_nodes(neo4j_session, "DatabricksCluster", ["cluster_id"])


def test_skip_cleanup_defers_pruning_to_cleanup_databricks(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _ingest(
        neo4j_session,
        WORKSPACE_A_HOST,
        {CLUSTERS_URI: {"clusters": [CLUSTER]}},
        OLD_TAG,
    )

    result = _ingest(neo4j_session, WORKSPACE_A_HOST, {}, NEW_TAG, skip_cleanup=True)

    assert _cluster_ids(neo4j_session) == {(CLUSTER["cluster_id"],)}
    cartography.intel.databricks.cleanup_databricks(neo4j_session, NEW_TAG, [result])
    assert _cluster_ids(neo4j_session) == set()


def test_failed_load_prunes_nothing(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _ingest(
        neo4j_session,
        WORKSPACE_A_HOST,
        {CLUSTERS_URI: {"clusters": [CLUSTER]}},
        OLD_TAG,
    )
    # The metastore lookup runs after clusters load, so the run fails midway.
    failing = {"/api/2.1/unity-catalog/metastore_summary": RuntimeError("boom")}

    with pytest.raises(RuntimeError):
        _ingest(neo4j_session, WORKSPACE_A_HOST, failing, NEW_TAG)

    assert _cluster_ids(neo4j_session) == {(CLUSTER["cluster_id"],)}
    assert check_nodes(neo4j_session, "DatabricksWorkspace", ["id"]) == {
        (WORKSPACE_A_ID,)
    }


def _catalog_id(name: str) -> str:
    return f"{METASTORE_ID}/{name}"


def _visible_catalogs(neo4j_session):
    return check_rels(
        neo4j_session,
        "DatabricksCatalog",
        "id",
        "DatabricksWorkspace",
        "id",
        "VISIBLE_IN",
    )


def test_failed_workspace_keeps_its_metastore_data(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    shared = {**METASTORE_RESPONSES, CATALOGS_URI: [catalog("shared")]}
    a_old = _ingest(neo4j_session, WORKSPACE_A_HOST, shared, OLD_TAG, True)
    b_old = _ingest(
        neo4j_session,
        WORKSPACE_B_HOST,
        {
            **shared,
            CLUSTERS_URI: {"clusters": [CLUSTER]},
            USERS_URI: [USER],
            catalog_grant_uri("shared"): CATALOG_GRANT,
        },
        OLD_TAG,
        True,
    )
    cartography.intel.databricks.cleanup_databricks(
        neo4j_session, OLD_TAG, [a_old, b_old]
    )

    # A now lists only catalog x. B fails before listing anything, so the
    # metastore it shares with A must not be cleaned this round.
    a_new = _ingest(
        neo4j_session,
        WORKSPACE_A_HOST,
        {**METASTORE_RESPONSES, CATALOGS_URI: [catalog("x")]},
        NEW_TAG,
        True,
    )
    with pytest.raises(RuntimeError):
        _ingest(
            neo4j_session,
            WORKSPACE_B_HOST,
            {METASTORE_SUMMARY_URI: RuntimeError("boom")},
            NEW_TAG,
            True,
        )
    cartography.intel.databricks.cleanup_databricks(
        neo4j_session, NEW_TAG, [a_new], skip_metastore_ids={METASTORE_ID}
    )

    assert check_nodes(neo4j_session, "DatabricksCatalog", ["id"]) == {
        (_catalog_id("shared"),),
        (_catalog_id("x"),),
    }
    assert _visible_catalogs(neo4j_session) == {
        (_catalog_id("shared"), WORKSPACE_B_ID),
        (_catalog_id("x"), WORKSPACE_A_ID),
    }
    assert check_rels(
        neo4j_session,
        "DatabricksUser",
        "user_name",
        "DatabricksCatalog",
        "id",
        "HAS_PRIVILEGE",
    ) == {(USER["userName"], _catalog_id("shared"))}
    assert check_rels(
        neo4j_session,
        "DatabricksWorkspace",
        "id",
        "DatabricksMetastore",
        "id",
        "ASSIGNED_METASTORE",
    ) == {(WORKSPACE_A_ID, METASTORE_ID), (WORKSPACE_B_ID, METASTORE_ID)}
    assert _cluster_ids(neo4j_session) == {(CLUSTER["cluster_id"],)}


def test_metastore_object_pruned_only_when_no_workspace_lists_it(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    old_a = {**METASTORE_RESPONSES, CATALOGS_URI: [catalog("shared"), catalog("a")]}
    shared = {**METASTORE_RESPONSES, CATALOGS_URI: [catalog("shared")]}
    results = [
        _ingest(neo4j_session, WORKSPACE_A_HOST, old_a, OLD_TAG, True),
        _ingest(neo4j_session, WORKSPACE_B_HOST, shared, OLD_TAG, True),
    ]
    cartography.intel.databricks.cleanup_databricks(neo4j_session, OLD_TAG, results)

    results = [
        _ingest(neo4j_session, WORKSPACE_A_HOST, METASTORE_RESPONSES, NEW_TAG, True),
        _ingest(neo4j_session, WORKSPACE_B_HOST, shared, NEW_TAG, True),
    ]
    cartography.intel.databricks.cleanup_databricks(neo4j_session, NEW_TAG, results)

    assert check_nodes(neo4j_session, "DatabricksCatalog", ["id"]) == {
        (_catalog_id("shared"),),
    }
    assert _visible_catalogs(neo4j_session) == {
        (_catalog_id("shared"), WORKSPACE_B_ID),
    }


def test_cleanup_drops_legacy_workspace_resource_edges(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    responses = {**METASTORE_RESPONSES, CATALOGS_URI: [catalog("shared")]}
    _ingest(neo4j_session, WORKSPACE_A_HOST, responses, OLD_TAG)
    # The edge every Unity Catalog object had before it moved to the metastore.
    neo4j_session.run(
        "MATCH (w:DatabricksWorkspace {id: $w}), (c:DatabricksCatalog) "
        "MERGE (w)-[r:RESOURCE]->(c) SET r.lastupdated = $tag",
        w=WORKSPACE_A_ID,
        tag=OLD_TAG,
    )

    _ingest(neo4j_session, WORKSPACE_A_HOST, responses, NEW_TAG)

    assert (
        check_rels(
            neo4j_session,
            "DatabricksWorkspace",
            "id",
            "DatabricksCatalog",
            "id",
            "RESOURCE",
        )
        == set()
    )
