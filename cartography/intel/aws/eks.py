import base64
import logging
import tempfile
from typing import Any

import boto3
import neo4j
import yaml
from botocore.signers import RequestSigner

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes import start_k8s_ingestion_with_parameters
from cartography.models.aws.eks.clusters import EKSClusterSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit
from cartography.util import join_url

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_eks_clusters(boto3_session: boto3.session.Session, region: str) -> list[str]:
    client = boto3_session.client("eks", region_name=region)
    clusters: list[str] = []
    paginator = client.get_paginator("list_clusters")
    for page in paginator.paginate():
        clusters.extend(page["clusters"])
    return clusters


@timeit
@aws_handle_regions
def get_eks_describe_cluster(
    boto3_session: boto3.session.Session,
    region: str,
    cluster_name: str,
) -> dict:
    client = boto3_session.client("eks", region_name=region)
    response = client.describe_cluster(name=cluster_name)
    return response["cluster"]


@timeit
def load_eks_clusters(
    neo4j_session: neo4j.Session,
    cluster_data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        EKSClusterSchema(),
        cluster_data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


def _process_logging(cluster: dict[str, Any]) -> bool:
    """
    Parse cluster.logging.clusterLogging to verify if
    at least one entry has audit logging set to Enabled.
    """
    logging: bool = False
    cluster_logging: Any = cluster.get("logging", {}).get("clusterLogging")
    if cluster_logging:
        logging = any(filter(lambda x: "audit" in x["types"] and x["enabled"], cluster_logging))  # type: ignore
    return logging


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Running EKS cluster cleanup")
    GraphJob.from_node_schema(EKSClusterSchema(), common_job_parameters).run(
        neo4j_session,
    )


def transform(cluster_data: dict[str, Any]) -> list[dict[str, Any]]:
    transformed_list: list[dict[str, Any]] = []
    for cluster_name, cluster_dict in cluster_data.items():
        transformed_dict = cluster_dict.copy()
        transformed_dict["ClusterLogging"] = _process_logging(transformed_dict)
        transformed_dict["ClusterEndpointPublic"] = transformed_dict.get(
            "resourcesVpcConfig",
            {},
        ).get(
            "endpointPublicAccess",
        )
        if "createdAt" in transformed_dict:
            transformed_dict["created_at"] = str(transformed_dict["createdAt"])
        transformed_list.append(transformed_dict)
    return transformed_list


@aws_handle_regions
def _get_eks_bearer_token(
    boto3_session: boto3.session.Session, cluster_id: str, region: str
) -> str:
    # EKS server rejects any tokens that have an expiration greater than 900 seconds
    STS_TOKEN_EXPIRES_IN = 900
    client = boto3_session.client("sts", region_name=region)
    service_id = client.meta.service_model.service_id

    signer = RequestSigner(
        service_id,
        region,
        "sts",
        "v4",
        boto3_session.get_credentials(),
        boto3_session.events,
    )

    params = {
        "method": "GET",
        "url": join_url(
            client.meta.endpoint_url, # https://sts.{region}.amazonaws.com
            {"Action": "GetCallerIdentity", "Version": "2011-06-15"},
        ),
        "body": {},
        "headers": {"x-k8s-aws-id": cluster_id},
        "context": {},
    }

    signed_url = signer.generate_presigned_url(
        params, region_name=region, expires_in=STS_TOKEN_EXPIRES_IN, operation_name=""
    )
    # remove any base64 encoding padding
    base64_url = (
        base64.urlsafe_b64encode(signed_url.encode("utf-8")).decode("utf-8").rstrip("=")
    )
    return "k8s-aws-v1." + base64_url


def create_kubeconfig(
    boto3_session: boto3.session.Session,
    cluster_name: str,
    region: str,
    endpoint: str,
    cert_data: str,
) -> dict[str, Any]:
    token = _get_eks_bearer_token(boto3_session, cluster_name, region)

    kubeconfig = {
        "apiVersion": "v1",
        "kind": "Config",
        "current-context": cluster_name,
        "contexts": [
            {
                "name": cluster_name,
                "context": {"cluster": cluster_name, "user": f"{cluster_name}-user"},
            }
        ],
        "clusters": [
            {
                "name": cluster_name,
                "cluster": {
                    "server": endpoint,
                    "certificate-authority-data": cert_data,
                },
            }
        ],
        "users": [{"name": f"{cluster_name}-user", "user": {"token": token}}],
    }

    return kubeconfig


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            "Syncing EKS for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )

        clusters: list[str] = get_eks_clusters(boto3_session, region)
        cluster_data: dict[str, Any] = {}
        for cluster_name in clusters:
            cluster_data[cluster_name] = get_eks_describe_cluster(
                boto3_session,
                region,
                cluster_name,
            )
        transformed_list = transform(cluster_data)

        load_eks_clusters(
            neo4j_session,
            transformed_list,
            region,
            current_aws_account_id,
            update_tag,
        )

        if common_job_parameters.get("aws_eks_sync_cluster_resources"):
            # load EKS resources using kubernetes intel module
            for cluster_name, cluster_info in cluster_data.items():
                if cluster_name != "infra-testing-us":
                    continue

                endpoint = cluster_info["endpoint"]
                cert_data = cluster_info["certificateAuthority"]["data"]
                kubeconfig = create_kubeconfig(
                    boto3_session, cluster_name, region, endpoint, cert_data
                )

                logger.info(
                    "Syncing EKS cluster resources for cluster '%s' in region '%s' in account '%s'.",
                    cluster_name,
                    region,
                    current_aws_account_id,
                )
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".yaml"
                ) as tmp_kubeconfig_file:
                    yaml.dump(kubeconfig, tmp_kubeconfig_file, default_flow_style=False)
                    tmp_kubeconfig_file.flush()

                    job_parameters = {
                        "UPDATE_TAG": common_job_parameters["UPDATE_TAG"],
                        "k8s_kubeconfig": tmp_kubeconfig_file.name,
                    }
                    start_k8s_ingestion_with_parameters(neo4j_session, job_parameters)

    cleanup(neo4j_session, common_job_parameters)
