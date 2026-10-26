from typing import Any
from unittest.mock import patch

import pytest

import cartography.intel.databricks
from cartography.config import Config
from tests.data.databricks.ingestion import CLUSTER
from tests.data.databricks.ingestion import CLUSTERS_URI
from tests.data.databricks.ingestion import WORKSPACE_A_HOST
from tests.data.databricks.ingestion import WORKSPACE_A_ID
from tests.integration.util import check_nodes

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
