import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.airbyte.util import AirbyteClient
from cartography.intel.airbyte.util import list_to_string
from cartography.models.airbyte.connection import AirbyteConnectionSchema
from cartography.models.airbyte.stream import AirbyteStreamSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: AirbyteClient,
    org_id: str,
    workspace_ids: List[str],
    common_job_parameters: Dict[str, Any],
) -> None:
    connections = get(api_session, workspace_ids)
    transformed_connections, transformed_streams = transform(connections)
    load_connections(
        neo4j_session,
        transformed_connections,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    load_streams(
        neo4j_session, transformed_streams, org_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: AirbyteClient,
    workspace_ids: List[str],
) -> List[Dict[str, Any]]:
    return api_session.get(
        "/connections",
        {"workspaceIds": ",".join(workspace_ids)} if workspace_ids else None,
    )


def transform(
    connections: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    transformed_connections = []
    transformed_streams = []
    for connection in connections:
        connection["tags_ids"] = [tag["tagId"] for tag in connection.get("tags", [])]
        transformed_connections.append(connection)
        for stream in connection.get("configurations", {}).get("streams", []):
            formated_stream = {
                "connectionId": connection["connectionId"],
                "streamId": f"{connection['connectionId']}_{stream['name']}",
                "name": stream["name"],
                "syncMode": stream["syncMode"],
                "cursorField": list_to_string(stream.get("cursorField", [])),
                "primaryKey": list_to_string(stream.get("primaryKey", [])),
                "includeFiles": stream.get("includeFiles", False),
                "selectedFields": list_to_string(stream.get("selectedFields", [])),
                "mappers": list_to_string(stream.get("mappers", [])),
            }
            transformed_streams.append(formated_stream)
    return transformed_connections, transformed_streams


@timeit
def load_connections(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Airbyte Connections into Neo4j.", len(data))
    load(
        neo4j_session,
        AirbyteConnectionSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def load_streams(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Airbyte Streams into Neo4j.", len(data))
    load(
        neo4j_session,
        AirbyteStreamSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(AirbyteStreamSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(AirbyteConnectionSchema(), common_job_parameters).run(
        neo4j_session
    )
