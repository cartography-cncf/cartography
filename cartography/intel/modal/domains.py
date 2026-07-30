import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.modal.util import list_domains
from cartography.intel.modal.util import ModalClient
from cartography.models.modal.domain import ModalDomainDNSRecordSchema
from cartography.models.modal.domain import ModalDomainSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    client: ModalClient,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """Ingest the workspace's custom domains and their validation DNS records.

    Workspace-scoped: `DomainList` is workspace-wide, not per environment. On workspaces
    without the custom-domains add-on the adapter returns an empty list, so this is a no-op
    there rather than a failure.
    """
    workspace_id = common_job_parameters["WORKSPACE_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    raw = await list_domains(client)
    domains = transform(raw)
    load_domains(neo4j_session, domains, workspace_id, update_tag)

    records = transform_records(raw)
    load_dns_records(neo4j_session, records, workspace_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
    return domains


def transform(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # `dns_records` is a nested list consumed by transform_records; it must not reach the node
    # loader, which only handles scalars and lists of scalars.
    return [
        {key: value for key, value in domain.items() if key != "dns_records"}
        for domain in raw
    ]


def transform_records(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for domain in raw:
        for record in domain.get("dns_records") or []:
            records.append(
                {
                    # Modal gives these records no id of their own.
                    "id": f"{domain['id']}/{record.get('type')}/{record.get('name')}",
                    "type": record.get("type"),
                    "name": record.get("name"),
                    "value": record.get("value"),
                    "domain_id": domain["id"],
                }
            )
    return records


@timeit
def load_domains(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalDomainSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def load_dns_records(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalDomainDNSRecordSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    # Records before domains: the record cleanup is scoped through the workspace, but keeping
    # child-before-parent order matches every other cleanup in this module.
    GraphJob.from_node_schema(ModalDomainDNSRecordSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ModalDomainSchema(), common_job_parameters).run(
        neo4j_session
    )
