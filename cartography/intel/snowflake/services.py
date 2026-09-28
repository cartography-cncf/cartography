"""Snowflake services: Snowpark Container Services workloads.

Services are listed per schema, and each service then has three sub-listings: its
running containers, the endpoints it exposes and the service roles that gate access to
them. Together they answer what code is running in the account, which image it came
from, and whether anything it serves is reachable from the internet.

``get`` returns one bundle per service, pairing the raw service payload with the schema
it was found in and with its three sub-listings, so ``transform`` can key every child on
its service without re-deriving anything.
"""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.names import external_access_integration_ids
from cartography.intel.snowflake.names import name_list
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import sf_path_segment
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import untag_image_path
from cartography.models.snowflake.service import SnowflakeServiceContainerSchema
from cartography.models.snowflake.service import SnowflakeServiceEndpointSchema
from cartography.models.snowflake.service import SnowflakeServiceRoleSchema
from cartography.models.snowflake.service import SnowflakeServiceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_schema_services(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Services of one schema, or None when the role cannot read that schema."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/services",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        logger.warning(
            "Cannot list services of Snowflake schema %s.%s (permission denied); they "
            "will be missing from the graph.",
            database_name,
            schema_name,
        )
        return None


@timeit
def get_service_sublisting(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
    service_name: str,
    sublisting: str,
) -> list[dict[str, Any]] | None:
    """One service sub-listing (``containers``, ``endpoints`` or ``roles``), or None.

    The three sub-resources differ only by the trailing path segment, so they share one
    fetcher rather than three copies of the same error handling.
    """
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}"
            f"/services/{sf_path_segment(service_name)}/{sublisting}",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        logger.warning(
            "Cannot list %s of Snowflake service %s.%s.%s (permission denied); they "
            "will be missing from the graph.",
            sublisting,
            database_name,
            schema_name,
            service_name,
        )
        return None


@timeit
def get(
    client: SnowflakeClient, schemas: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Return one bundle per readable service plus whether everything was read."""
    bundles: list[dict[str, Any]] = []
    complete = True

    for schema in schemas:
        database_name = schema["database_name"]
        schema_name = schema["name"]
        services = get_schema_services(client, database_name, schema_name)
        if services is None:
            complete = False
            continue

        for service in services:
            service_name = service["name"]
            sublistings: dict[str, list[dict[str, Any]]] = {}
            for sublisting in ("containers", "endpoints", "roles"):
                rows = get_service_sublisting(
                    client, database_name, schema_name, service_name, sublisting
                )
                if rows is None:
                    complete = False
                sublistings[sublisting] = rows or []
            bundles.append(
                {
                    "database_name": database_name,
                    "schema_name": schema_name,
                    "service": service,
                    "containers": sublistings["containers"],
                    "endpoints": sublistings["endpoints"],
                    "roles": sublistings["roles"],
                },
            )
    return bundles, complete


def transform(
    bundles: list[dict[str, Any]],
    account_id: str,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Return ``(services, containers, endpoints, service roles)``."""
    services: list[dict[str, Any]] = []
    containers: list[dict[str, Any]] = []
    endpoints: list[dict[str, Any]] = []
    service_roles: list[dict[str, Any]] = []

    for bundle in bundles:
        database_name = bundle["database_name"]
        schema_name = bundle["schema_name"]
        service = bundle["service"]
        name = service["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        service_id = sf_id(account_id, "service", qualified_name)
        compute_pool = service.get("compute_pool") or None
        query_warehouse = service.get("query_warehouse") or None
        external_access_integrations = name_list(
            service.get("external_access_integrations")
        )
        services.append(
            {
                "id": service_id,
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": sf_id(
                    account_id, "schema", sf_fqn(database_name, schema_name)
                ),
                "status": service.get("status"),
                "compute_pool": compute_pool,
                # Null when the field is absent, which suppresses the edge rather
                # than pointing it at a nonexistent node.
                "compute_pool_id": (
                    sf_id(account_id, "compute_pool", sf_fqn(compute_pool))
                    if compute_pool
                    else None
                ),
                "spec_digest": service.get("spec_digest"),
                "dns_name": service.get("dns_name"),
                "current_instances": service.get("current_instances"),
                "target_instances": service.get("target_instances"),
                "min_instances": service.get("min_instances"),
                "max_instances": service.get("max_instances"),
                "auto_resume": service.get("auto_resume"),
                "is_job": service.get("is_job"),
                "is_upgrading": service.get("is_upgrading"),
                "query_warehouse": query_warehouse,
                "query_warehouse_id": (
                    sf_id(account_id, "warehouse", sf_fqn(query_warehouse))
                    if query_warehouse
                    else None
                ),
                "external_access_integrations": external_access_integrations,
                "external_access_integration_ids": external_access_integration_ids(
                    external_access_integrations,
                    account_id,
                ),
                "owner": service.get("owner"),
                "comment": service.get("comment"),
                "created_on": iso_to_datetime(service.get("created_on")),
            },
        )

        for container in bundle["containers"]:
            container_name = container["container_name"]
            instance_id = str(container["instance_id"])
            containers.append(
                {
                    # The instance id is part of the key: a service scaled to several
                    # instances runs the same container name once per instance, and
                    # keying on the name alone would collapse them onto one node.
                    "id": sf_id(
                        account_id,
                        "service_container",
                        f"{qualified_name}.{sf_fqn(container_name)}#{instance_id}",
                    ),
                    "name": container_name,
                    "instance_id": instance_id,
                    "service_name": qualified_name,
                    "parent_service_id": service_id,
                    "status": container.get("status"),
                    "image_name": container.get("image_name"),
                    "untagged_image_path": untag_image_path(
                        container.get("image_name")
                    ),
                    "image_digest": container.get("image_digest"),
                    "restart_count": container.get("restart_count"),
                    "message": container.get("message"),
                    "start_time": iso_to_datetime(container.get("start_time")),
                },
            )

        for endpoint in bundle["endpoints"]:
            endpoint_name = endpoint["name"]
            endpoints.append(
                {
                    "id": sf_id(
                        account_id,
                        "service_endpoint",
                        f"{qualified_name}.{sf_fqn(endpoint_name)}",
                    ),
                    "name": endpoint_name,
                    "service_name": qualified_name,
                    "parent_service_id": service_id,
                    "port": endpoint.get("port"),
                    "port_range": endpoint.get("port_range"),
                    "protocol": endpoint.get("protocol"),
                    "is_public": endpoint.get("is_public"),
                    "ingress_url": endpoint.get("ingress_url"),
                },
            )

        for service_role in bundle["roles"]:
            role_name = service_role["name"]
            service_roles.append(
                {
                    "id": sf_id(
                        account_id,
                        "service_role",
                        f"{qualified_name}.{sf_fqn(role_name)}",
                    ),
                    "name": role_name,
                    "service_name": qualified_name,
                    "parent_service_id": service_id,
                    "comment": service_role.get("comment"),
                },
            )

    return services, containers, endpoints, service_roles


def load_services(
    neo4j_session: neo4j.Session,
    services: list[dict[str, Any]],
    containers: list[dict[str, Any]],
    endpoints: list[dict[str, Any]],
    service_roles: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeServiceSchema(),
        services,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )
    load(
        neo4j_session,
        SnowflakeServiceContainerSchema(),
        containers,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )
    load(
        neo4j_session,
        SnowflakeServiceEndpointSchema(),
        endpoints,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )
    load(
        neo4j_session,
        SnowflakeServiceRoleSchema(),
        service_roles,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeServiceContainerSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        SnowflakeServiceEndpointSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(SnowflakeServiceRoleSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(SnowflakeServiceSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake services, containers, endpoints and service roles.

    Runs after compute pools, warehouses, external access integrations and image
    repositories so every edge resolves on the first pass. Returns whether every schema
    and service could be read.
    """
    bundles, complete = get(client, schemas)
    services, containers, endpoints, service_roles = transform(
        bundles, client.account_id
    )
    logger.info(
        "Loading %d Snowflake services, %d containers, %d endpoints and %d service "
        "roles for account %s.",
        len(services),
        len(containers),
        len(endpoints),
        len(service_roles),
        client.account_id,
    )
    load_services(
        neo4j_session,
        services,
        containers,
        endpoints,
        service_roles,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    if not complete:
        logger.warning(
            "Some Snowflake services could not be fully listed; skipping cleanup so "
            "still-valid services and containers are not deleted.",
        )
    return complete
