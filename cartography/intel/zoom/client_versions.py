import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.zoom.client import ZoomClient
from cartography.models.zoom.client_version import ZoomClientVersionSchema
from cartography.util import timeit


@timeit
def sync(
    session: neo4j.Session, client: ZoomClient, account_id: str, update_tag: int
) -> None:
    versions = client.get("/metrics/client_versions")["client_versions"]
    data = {
        f"{account_id}:client_version:{version['client_version']}": {
            "id": f"{account_id}:client_version:{version['client_version']}",
            "client_version": version["client_version"],
            "total_count": version.get("total_count"),
        }
        for version in versions
    }
    load(
        session,
        ZoomClientVersionSchema(),
        list(data.values()),
        ACCOUNT_ID=account_id,
        lastupdated=update_tag,
    )
    GraphJob.from_node_schema(
        ZoomClientVersionSchema(), {"ACCOUNT_ID": account_id, "UPDATE_TAG": update_tag}
    ).run(session)
