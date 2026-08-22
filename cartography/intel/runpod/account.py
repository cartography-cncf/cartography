import neo4j

from cartography.client.core.tx import load
from cartography.models.runpod.account import RunPodAccountSchema
from cartography.util import timeit


@timeit
def sync(neo4j_session: neo4j.Session, account_id: str, update_tag: int) -> None:
    load(
        neo4j_session,
        RunPodAccountSchema(),
        [{"id": account_id}],
        lastupdated=update_tag,
    )
