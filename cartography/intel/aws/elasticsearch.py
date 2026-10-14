import json
import logging
from typing import Dict
from typing import List

import boto3
import botocore
import neo4j
from policyuniverse.policy import Policy

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.intel.dns import resolve_a_record
from cartography.intel.dns_utils import normalize_hostname
from cartography.models.aws.elasticsearch.domain import ESDomainSchema
from cartography.models.aws.elasticsearch.endpoint import (
    ESDomainEndpointDNSRecordSchema,
)
from cartography.models.aws.elasticsearch.endpoint import ESDomainEndpointIpSchema
from cartography.util import aws_handle_regions
from cartography.util import run_scoped_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _is_internet_exposed(domain: Dict) -> bool:
    if not domain.get("Endpoint") or not domain.get("AccessPolicies"):
        return False
    policy = Policy(json.loads(domain["AccessPolicies"]))
    return policy.is_internet_accessible()


@timeit
@aws_handle_regions
def _get_es_domains(client: botocore.client.BaseClient) -> List[Dict]:
    """
    Get ES domains.

    :param client: ES boto client
    :return: list of ES domains
    """
    data = client.list_domain_names()
    domain_names = [d["DomainName"] for d in data.get("DomainNames", [])]
    # NOTE describe_elasticsearch_domains takes at most 5 domain names
    domain_name_chunks = [
        domain_names[i : i + 5] for i in range(0, len(domain_names), 5)
    ]
    domains: List[Dict] = []
    for domain_name_chunk in domain_name_chunks:
        chunk_data = client.describe_elasticsearch_domains(
            DomainNames=domain_name_chunk,
        )
        domains.extend(chunk_data["DomainStatusList"])
    return domains


def _transform_es_domains(domain_list: List[Dict]) -> List[Dict]:
    """
    Transform Elasticsearch domains data, flattening nested properties.

    Returns a list of flattened domain data ready for loading.
    """
    domains_data = []

    for domain in domain_list:
        # Remove ServiceSoftwareOptions as it contains datetime objects
        if "ServiceSoftwareOptions" in domain:
            del domain["ServiceSoftwareOptions"]

        domain_id = domain["DomainId"]

        # Flatten nested structures
        cluster_config = domain.get("ElasticsearchClusterConfig", {})
        ebs_options = domain.get("EBSOptions", {})
        encryption_options = domain.get("EncryptionAtRestOptions", {})
        log_options = domain.get("LogPublishingOptions", {})
        vpc_options = domain.get("VPCOptions") or {}

        # AWS rebranded Elasticsearch Service to OpenSearch Service. The same
        # AWSESDomain node can therefore represent either engine; AWS encodes the
        # distinction in `ElasticsearchVersion` (e.g. "OpenSearch_2.5" vs
        # "7.10"). Derive the engine here so downstream consumers (notably the
        # databases ontology mapping) can label the node correctly without
        # parsing the version string themselves. Leave engine unset when the
        # version is missing rather than guessing — a missing version is rare
        # but a wrong label downstream is harder to debug.
        es_version = domain.get("ElasticsearchVersion")
        if not es_version:
            engine = None
        elif es_version.startswith("OpenSearch"):
            engine = "opensearch"
        else:
            engine = "elasticsearch"

        # Flattened data with VPC lists for one-to-many relationships
        transformed = {
            "DomainId": domain_id,
            "DomainName": domain.get("DomainName"),
            "ARN": domain.get("ARN"),
            "Deleted": domain.get("Deleted"),
            "Created": domain.get("Created"),
            "Endpoint": domain.get("Endpoint"),
            "ElasticsearchVersion": domain.get("ElasticsearchVersion"),
            "Engine": engine,
            "exposed_internet": _is_internet_exposed(domain),
            # Cluster config
            "ElasticsearchClusterConfigInstanceType": cluster_config.get(
                "InstanceType"
            ),
            "ElasticsearchClusterConfigInstanceCount": cluster_config.get(
                "InstanceCount"
            ),
            "ElasticsearchClusterConfigDedicatedMasterEnabled": cluster_config.get(
                "DedicatedMasterEnabled"
            ),
            "ElasticsearchClusterConfigZoneAwarenessEnabled": cluster_config.get(
                "ZoneAwarenessEnabled"
            ),
            "ElasticsearchClusterConfigDedicatedMasterType": cluster_config.get(
                "DedicatedMasterType"
            ),
            "ElasticsearchClusterConfigDedicatedMasterCount": cluster_config.get(
                "DedicatedMasterCount"
            ),
            # EBS options
            "EBSOptionsEBSEnabled": ebs_options.get("EBSEnabled"),
            "EBSOptionsVolumeType": ebs_options.get("VolumeType"),
            "EBSOptionsVolumeSize": ebs_options.get("VolumeSize"),
            "EBSOptionsIops": ebs_options.get("Iops"),
            # Encryption options
            "EncryptionAtRestOptionsEnabled": encryption_options.get("Enabled"),
            "EncryptionAtRestOptionsKmsKeyId": encryption_options.get("KmsKeyId"),
            # Log publishing options (per log type)
            "LogPublishingIndexSlowLogsEnabled": log_options.get(
                "INDEX_SLOW_LOGS", {}
            ).get("Enabled"),
            "LogPublishingIndexSlowLogsArn": log_options.get("INDEX_SLOW_LOGS", {}).get(
                "CloudWatchLogsLogGroupArn"
            ),
            "LogPublishingSearchSlowLogsEnabled": log_options.get(
                "SEARCH_SLOW_LOGS", {}
            ).get("Enabled"),
            "LogPublishingSearchSlowLogsArn": log_options.get(
                "SEARCH_SLOW_LOGS", {}
            ).get("CloudWatchLogsLogGroupArn"),
            "LogPublishingEsApplicationLogsEnabled": log_options.get(
                "ES_APPLICATION_LOGS", {}
            ).get("Enabled"),
            "LogPublishingEsApplicationLogsArn": log_options.get(
                "ES_APPLICATION_LOGS", {}
            ).get("CloudWatchLogsLogGroupArn"),
            "LogPublishingAuditLogsEnabled": log_options.get("AUDIT_LOGS", {}).get(
                "Enabled"
            ),
            "LogPublishingAuditLogsArn": log_options.get("AUDIT_LOGS", {}).get(
                "CloudWatchLogsLogGroupArn"
            ),
            # VPC options - keep as lists for one-to-many relationships
            "SubnetIds": vpc_options.get("SubnetIds", []),
            "SecurityGroupIds": vpc_options.get("SecurityGroupIds", []),
        }

        domains_data.append(transformed)

    return domains_data


@timeit
def get_endpoint_ip_addresses(domain_list: List[Dict]) -> Dict[str, List[str]]:
    """
    Resolve each domain endpoint to the IP addresses of its A record.

    :param domain_list: Transformed domain list
    :return: The resolved IP addresses keyed by domain id
    """
    # TODO add support for the VPC `Endpoints` map
    endpoint_ips: Dict[str, List[str]] = {}
    for domain in domain_list:
        if domain.get("Endpoint"):
            endpoint_ips[domain["DomainId"]] = resolve_a_record(domain["Endpoint"])
        else:
            logger.debug("No es endpoint data for domain id %s", domain["DomainId"])
    return endpoint_ips


def transform_endpoint_dns_records(
    domain_list: List[Dict],
    endpoint_ips: Dict[str, List[str]],
) -> List[Dict]:
    records = []
    for domain in domain_list:
        ip_addresses = endpoint_ips.get(domain["DomainId"])
        if ip_addresses is None:
            continue
        endpoint = domain["Endpoint"]
        records.append(
            {
                "id": f"{endpoint}+A",
                "name": endpoint,
                "name_normalized": normalize_hostname(endpoint),
                "type": "A",
                "value": ",".join(ip_addresses),
                "ip_addresses": ip_addresses,
                "domain_id": domain["DomainId"],
            },
        )
    return records


@timeit
def _load_es_domains(
    neo4j_session: neo4j.Session,
    domain_list: List[Dict],
    aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Ingest Elastic Search domains

    :param neo4j_session: Neo4j session object
    :param domain_list: Transformed domain list to ingest
    :param aws_account_id: The AWS account related to the domains
    :param aws_update_tag: Update tag for the sync
    """
    load(
        neo4j_session,
        ESDomainSchema(),
        domain_list,
        lastupdated=aws_update_tag,
        AWS_ID=aws_account_id,
    )


@timeit
def load_endpoint_dns_records(
    neo4j_session: neo4j.Session,
    records: List[Dict],
    aws_update_tag: int,
) -> None:
    ip_addresses = sorted(
        {ip for record in records for ip in record["ip_addresses"]},
    )
    load(
        neo4j_session,
        ESDomainEndpointIpSchema(),
        [{"id": ip, "ip": ip} for ip in ip_addresses],
        lastupdated=aws_update_tag,
    )
    load(
        neo4j_session,
        ESDomainEndpointDNSRecordSchema(),
        records,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, update_tag: int, aws_account_id: str) -> None:
    common_job_parameters = {"UPDATE_TAG": update_tag, "AWS_ID": aws_account_id}
    # Endpoint records are reached through their domain, so clean them up while the stale
    # domains still exist.
    run_scoped_analysis_job(
        "aws_es_domain_endpoint_dns_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )
    GraphJob.from_node_schema(ESDomainSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info(
            "Syncing Elasticsearch Service for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        client = create_boto3_client(
            boto3_session,
            "es",
            region_name=region,
            config=get_botocore_config(),
        )
        data = _get_es_domains(client)
        domains_data = _transform_es_domains(data)
        endpoint_ips = get_endpoint_ip_addresses(domains_data)
        endpoint_records = transform_endpoint_dns_records(domains_data, endpoint_ips)
        _load_es_domains(
            neo4j_session,
            domains_data,
            current_aws_account_id,
            update_tag,
        )
        load_endpoint_dns_records(neo4j_session, endpoint_records, update_tag)

    cleanup(neo4j_session, update_tag, current_aws_account_id)
