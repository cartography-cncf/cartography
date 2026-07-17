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
from botocore.exceptions import ClientError
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.x509.extensions import ExtensionNotFound
from cryptography.x509.oid import ExtensionOID

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.eks.access_entry import EKSAccessEntrySchema
from cartography.models.aws.eks.clusters import EKSClusterSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)

ACCESS_ENTRIES_UNSUPPORTED_AUTH_MODE_MESSAGE = (
    "authentication mode must be set to one of [API, API_AND_CONFIG_MAP]"
)


@timeit
@aws_handle_regions
def get_eks_clusters(boto3_session: boto3.session.Session, region: str) -> List[str]:
    client = create_boto3_client(boto3_session, "eks", region_name=region)
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
    client = create_boto3_client(boto3_session, "eks", region_name=region)
    response = client.describe_cluster(name=cluster_name)
    return response["cluster"]


def _is_access_entries_unsupported_auth_mode_error(error: ClientError) -> bool:
    error_details = error.response.get("Error", {})
    error_code = error_details.get("Code")
    error_message = error_details.get("Message", "")
    return (
        error_code == "InvalidRequestException"
        and ACCESS_ENTRIES_UNSUPPORTED_AUTH_MODE_MESSAGE in error_message
    )


def _list_access_entry_principal_arns(client: Any, cluster_name: str) -> list[str]:
    principal_arns = []

    try:
        paginator = client.get_paginator("list_access_entries")
        for page in paginator.paginate(clusterName=cluster_name):
            principal_arns.extend(page.get("accessEntries", []))
    except ClientError as e:
        if _is_access_entries_unsupported_auth_mode_error(e):
            logger.info(
                "EKS Access Entries are unavailable for cluster %s authentication "
                "mode; skipping Access Entries.",
                cluster_name,
            )
            return []
        raise

    return principal_arns


@timeit
@aws_handle_regions
def get_eks_access_entries(
    boto3_session: boto3.session.Session,
    region: str,
    cluster_name: str,
    authentication_mode: str | None,
) -> list[dict[str, Any]]:
    if authentication_mode == "CONFIG_MAP":
        logger.info(
            "EKS Access Entries are unavailable for cluster %s authentication mode; "
            "skipping Access Entries.",
            cluster_name,
        )
        return []

    client = create_boto3_client(boto3_session, "eks", region_name=region)
    access_entries = []
    describe_access_entries = True

    principal_arns = _list_access_entry_principal_arns(client, cluster_name)
    for principal_arn in principal_arns:
        if not describe_access_entries:
            access_entries.append(
                {
                    "clusterName": cluster_name,
                    "principalArn": principal_arn,
                }
            )
            continue
        try:
            response = client.describe_access_entry(
                clusterName=cluster_name,
                principalArn=principal_arn,
            )
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                logger.warning(
                    "Access entry lookup failed for principal %s on cluster %s: %s",
                    principal_arn,
                    cluster_name,
                    e,
                )
                continue
            if error_code == "AccessDeniedException":
                logger.warning(
                    "Access entry detail lookup denied on cluster %s; loading minimal "
                    "access entry data from ListAccessEntries for all remaining principals.",
                    cluster_name,
                )
                describe_access_entries = False
                access_entries.append(
                    {
                        "clusterName": cluster_name,
                        "principalArn": principal_arn,
                    }
                )
                continue
            raise
        access_entries.append(response["accessEntry"])

    logger.info(
        "Retrieved %d EKS Access Entries for cluster %s",
        len(access_entries),
        cluster_name,
    )
    return access_entries


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


@timeit
def load_eks_access_entries(
    neo4j_session: neo4j.Session,
    access_entry_data: list[dict[str, Any]],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        EKSAccessEntrySchema(),
        access_entry_data,
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


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _get_subject_key_identifier_hex(cert: x509.Certificate) -> str | None:
    """
    Return the SKI extension value when present on the certificate.

    This intentionally does not derive SKI from the certificate's public key.
    """
    try:
        ski = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_KEY_IDENTIFIER)
    except ExtensionNotFound:
        return None
    return ski.value.digest.hex()


def _get_authority_key_identifier_hex(cert: x509.Certificate) -> str | None:
    """
    Return the AKI key identifier extension value when present on the certificate.
    """
    try:
        aki = cert.extensions.get_extension_for_oid(
            ExtensionOID.AUTHORITY_KEY_IDENTIFIER
        )
    except ExtensionNotFound:
        return None
    if aki.value.key_identifier:
        return aki.value.key_identifier.hex()
    return None


def _parse_certificate_authority_metadata(cluster: Dict[str, Any]) -> Dict[str, Any]:
    cert_data = cluster.get("certificateAuthority", {}).get("data")
    cert_metadata: Dict[str, Any] = {
        "certificate_authority_data_present": bool(cert_data),
        "certificate_authority_parse_status": "missing",
        "certificate_authority_parse_error": None,
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
        cert_metadata["certificate_authority_parse_status"] = "invalid_base64"
        cert_metadata["certificate_authority_parse_error"] = str(err)
        logger.warning(
            "Failed to decode EKS cluster certificate authority data for cluster %s (%s): "
            "status=%s error=%s",
            cluster_name,
            cluster_arn,
            cert_metadata["certificate_authority_parse_status"],
            cert_metadata["certificate_authority_parse_error"],
        )
        return cert_metadata

    cert: x509.Certificate
    try:
        cert = x509.load_der_x509_certificate(cert_bytes)
    except ValueError:
        try:
            cert = x509.load_pem_x509_certificate(cert_bytes)
        except ValueError as err:
            cert_metadata["certificate_authority_parse_status"] = "invalid_certificate"
            cert_metadata["certificate_authority_parse_error"] = str(err)
            logger.warning(
                "Failed to parse EKS cluster certificate authority certificate for cluster %s (%s): "
                "status=%s error=%s",
                cluster_name,
                cluster_arn,
                cert_metadata["certificate_authority_parse_status"],
                cert_metadata["certificate_authority_parse_error"],
            )
            return cert_metadata

    cert_metadata["certificate_authority_parse_status"] = "parsed"
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
    not_before_utc = _ensure_utc(not_before_utc)
    not_after_utc = _ensure_utc(not_after_utc)
    cert_metadata["certificate_authority_not_before"] = not_before_utc
    cert_metadata["certificate_authority_not_after"] = not_after_utc

    cert_metadata["certificate_authority_subject_key_identifier"] = (
        _get_subject_key_identifier_hex(cert)
    )
    cert_metadata["certificate_authority_authority_key_identifier"] = (
        _get_authority_key_identifier_hex(cert)
    )

    return cert_metadata


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.info("Running EKS access entry cleanup")
    GraphJob.from_node_schema(EKSAccessEntrySchema(), common_job_parameters).run(
        neo4j_session,
    )
    logger.info("Running EKS cluster cleanup")
    GraphJob.from_node_schema(EKSClusterSchema(), common_job_parameters).run(
        neo4j_session,
    )


def transform_access_entries(
    access_entries: list[dict[str, Any]],
    cluster_arn: str,
) -> list[dict[str, Any]]:
    transformed_entries = []
    for entry in access_entries:
        transformed_entry = entry.copy()
        transformed_entry["id"] = f"{cluster_arn}/access-entry/{entry['principalArn']}"
        transformed_entry["cluster_arn"] = cluster_arn
        transformed_entries.append(transformed_entry)
    return transformed_entries


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
        transformed_dict["AuthenticationMode"] = transformed_dict.get(
            "accessConfig",
            {},
        ).get(
            "authenticationMode",
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
        access_entries: list[dict[str, Any]] = []
        for cluster in transformed_list:
            access_entries.extend(
                transform_access_entries(
                    get_eks_access_entries(
                        boto3_session,
                        region,
                        cluster["name"],
                        cluster.get("AuthenticationMode"),
                    ),
                    cluster["arn"],
                )
            )
        load_eks_access_entries(
            neo4j_session,
            access_entries,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
