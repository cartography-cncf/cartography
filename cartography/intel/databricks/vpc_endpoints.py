from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks._account_scope import account_scoped_id
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.models.databricks.vpc_endpoint import DatabricksVpcEndpointSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksAccountClient,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    endpoints = get(api_session)
    transformed = transform(endpoints, account_id)
    load_vpc_endpoints(
        neo4j_session, transformed, account_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksAccountClient) -> list[dict[str, Any]]:
    return api_session.get(api_session.account_uri("/vpc-endpoints")) or []


@timeit
def transform(endpoints: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for e in endpoints:
        vpc_endpoint_id = e["vpc_endpoint_id"]
        # The AWS-side endpoint id lives under aws_vpc_endpoint depending on the
        # API version; fall back to the top-level field for older shapes.
        aws_vpc_endpoint_id = (e.get("aws_vpc_endpoint") or {}).get(
            "vpc_endpoint_id"
        ) or e.get("aws_vpc_endpoint_id")
        result.append(
            {
                "id": account_scoped_id(account_id, vpc_endpoint_id),
                "vpc_endpoint_id": vpc_endpoint_id,
                "vpc_endpoint_name": e.get("vpc_endpoint_name"),
                "aws_endpoint_service_id": e.get("aws_endpoint_service_id"),
                "region": e.get("region"),
                "aws_vpc_endpoint_id": aws_vpc_endpoint_id,
            }
        )
    return result


@timeit
def load_vpc_endpoints(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksVpcEndpointSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksVpcEndpointSchema(), common_job_parameters).run(
        neo4j_session
    )
