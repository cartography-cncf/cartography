import base64
import binascii
import logging
from datetime import datetime
from datetime import timezone
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.x509.extensions import ExtensionNotFound
from cryptography.x509.oid import ExtensionOID

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.eks.clusters import EKSClusterSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_eks_clusters(boto3_session: boto3.session.Session, region: str) -> List[str]:
    client = boto3_session.client("eks", region_name=region)
    clusters: List[str] = []
    paginator = client.get_paginator("list_clusters")
    for page in paginator.paginate():
        clusters.extend(page["clusters"])
    return clusters


@timeit
def get_eks_describe_cluster(
    boto3_session: boto3.session.Session,
    region: str,
    cluster_name: str,
) -> Dict:
    client = boto3_session.client("eks", region_name=region)
    response = client.describe_cluster(name=cluster_name)
    return response["cluster"]


@timeit
def load_eks_clusters(
    neo4j_session: neo4j.Session,
    cluster_data: List[Dict[str, Any]],
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


def _process_logging(cluster: Dict) -> bool:
    """
    Parse cluster.logging.clusterLogging to verify if
    at least one entry has audit logging set to Enabled.
    """
    logging: bool = False
    cluster_logging: Any = cluster.get("logging", {}).get("clusterLogging")
    if cluster_logging:
        logging = any(filter(lambda x: "audit" in x["types"] and x["enabled"], cluster_logging))  # type: ignore
    return logging


def _format_datetime_iso(value: datetime) -> str:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).isoformat()
    return value.isoformat()


def _parse_certificate_authority_metadata(cluster: Dict[str, Any]) -> Dict[str, Any]:
    cert_data = cluster.get("certificateAuthority", {}).get("data")
    cert_metadata: Dict[str, Any] = {
        "certificate_authority_data_present": bool(cert_data),
        "certificate_authority_sha256_fingerprint": None,
        "certificate_authority_subject": None,
        "certificate_authority_issuer": None,
        "certificate_authority_not_before": None,
        "certificate_authority_not_after": None,
        "certificate_authority_subject_key_identifier": None,
        "certificate_authority_authority_key_identifier": None,
    }

    if not cert_data:
        return cert_metadata

    cluster_name = cluster.get("name", "<unknown>")
    cluster_arn = cluster.get("arn", "<unknown>")

    try:
        cert_bytes = base64.b64decode(cert_data, validate=True)
    except (ValueError, binascii.Error) as err:
        logger.warning(
            "Failed to decode EKS cluster certificate authority data for cluster %s (%s): %s",
            cluster_name,
            cluster_arn,
            err,
        )
        return cert_metadata

    cert: x509.Certificate
    try:
        cert = x509.load_der_x509_certificate(cert_bytes)
    except ValueError:
        try:
            cert = x509.load_pem_x509_certificate(cert_bytes)
        except ValueError as err:
            logger.warning(
                "Failed to parse EKS cluster certificate authority certificate for cluster %s (%s): %s",
                cluster_name,
                cluster_arn,
                err,
            )
            return cert_metadata

    cert_metadata["certificate_authority_sha256_fingerprint"] = cert.fingerprint(
        hashes.SHA256(),
    ).hex()
    cert_metadata["certificate_authority_subject"] = cert.subject.rfc4514_string()
    cert_metadata["certificate_authority_issuer"] = cert.issuer.rfc4514_string()

    not_before_utc = (
        cert.not_valid_before_utc
        if hasattr(cert, "not_valid_before_utc")
        else cert.not_valid_before
    )
    not_after_utc = (
        cert.not_valid_after_utc
        if hasattr(cert, "not_valid_after_utc")
        else cert.not_valid_after
    )
    cert_metadata["certificate_authority_not_before"] = _format_datetime_iso(
        not_before_utc,
    )
    cert_metadata["certificate_authority_not_after"] = _format_datetime_iso(
        not_after_utc,
    )

    try:
        ski = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_KEY_IDENTIFIER)
        cert_metadata["certificate_authority_subject_key_identifier"] = (
            ski.value.digest.hex()
        )
    except ExtensionNotFound:
        pass

    try:
        aki = cert.extensions.get_extension_for_oid(
            ExtensionOID.AUTHORITY_KEY_IDENTIFIER
        )
        if aki.value.key_identifier:
            cert_metadata["certificate_authority_authority_key_identifier"] = (
                aki.value.key_identifier.hex()
            )
    except ExtensionNotFound:
        pass

    return cert_metadata


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.info("Running EKS cluster cleanup")
    GraphJob.from_node_schema(EKSClusterSchema(), common_job_parameters).run(
        neo4j_session,
    )


def transform(cluster_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    transformed_list = []
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
        transformed_dict.update(_parse_certificate_authority_metadata(cluster_dict))
        transformed_list.append(transformed_dict)
    return transformed_list


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
            "Syncing EKS for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )

        clusters: List[str] = get_eks_clusters(boto3_session, region)
        cluster_data = {}
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

    cleanup(neo4j_session, common_job_parameters)
