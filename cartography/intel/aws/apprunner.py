import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.apprunner import AppRunnerServiceSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_apprunner_services(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "apprunner",
        region_name=region,
        config=get_botocore_config(),
    )
    services: List[Dict[str, Any]] = []
    kwargs: Dict[str, Any] = {}
    while True:
        response = client.list_services(**kwargs)
        services.extend(response.get("ServiceSummaryList", []))
        next_token = response.get("NextToken")
        if not next_token:
            break
        kwargs["NextToken"] = next_token

    described_services: List[Dict[str, Any]] = []
    for service in services:
        service_arn = service["ServiceArn"]
        desc_response = client.describe_service(ServiceArn=service_arn)
        described_services.append(desc_response["Service"])
    return described_services


def transform_apprunner_services(
    services: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Transform AppRunner services by flattening nested configuration fields
    for loading into the graph.
    """
    transformed: List[Dict[str, Any]] = []
    for svc in services:
        svc = dict(svc)

        source_config = svc.get("SourceConfiguration", {})
        image_repo = source_config.get("ImageRepository", {})
        svc["ImageIdentifier"] = image_repo.get("ImageIdentifier")
        svc["AutoDeploymentsEnabled"] = source_config.get("AutoDeploymentsEnabled")
        auth_config = source_config.get("AuthenticationConfiguration", {})
        svc["AccessRoleArn"] = auth_config.get("AccessRoleArn")

        instance_config = svc.get("InstanceConfiguration", {})
        svc["Cpu"] = instance_config.get("Cpu")
        svc["Memory"] = instance_config.get("Memory")
        svc["InstanceRoleArn"] = instance_config.get("InstanceRoleArn")

        network_config = svc.get("NetworkConfiguration", {})
        egress_config = network_config.get("EgressConfiguration", {})
        svc["EgressType"] = egress_config.get("EgressType")
        ingress_config = network_config.get("IngressConfiguration", {})
        svc["IsPubliclyAccessible"] = ingress_config.get("IsPubliclyAccessible")

        transformed.append(svc)
    return transformed


@timeit
def load_apprunner_services(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading AppRunner {len(data)} services for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        AppRunnerServiceSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Running AppRunner cleanup job.")
    cleanup_job = GraphJob.from_node_schema(
        AppRunnerServiceSchema(), common_job_parameters
    )
    cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            f"Syncing AppRunner for region '{region}' in account '{current_aws_account_id}'.",
        )

        services = get_apprunner_services(boto3_session, region)

        transformed_services = transform_apprunner_services(services)

        load_apprunner_services(
            neo4j_session,
            transformed_services,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
