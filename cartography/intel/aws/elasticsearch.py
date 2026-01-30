import json
import logging
from typing import Dict
from typing import List

import boto3
import botocore.config
import neo4j
from policyuniverse.policy import Policy

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.intel.dns import ingest_dns_record_by_fqdn
from cartography.models.aws.elasticsearch.domain import ESDomainSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


# TODO memoize this
def _get_botocore_config() -> botocore.config.Config:
    return botocore.config.Config(
        retries={
            "max_attempts": 8,
        },
    )


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

        # Flattened data with VPC lists for one-to-many relationships
        transformed = {
            "DomainId": domain_id,
            "ARN": domain.get("ARN"),
            "Deleted": domain.get("Deleted"),
            "Created": domain.get("Created"),
            "Endpoint": domain.get("Endpoint"),
            "ElasticsearchVersion": domain.get("ElasticsearchVersion"),
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
            # Keep original for DNS/access policy processing
            "_original": domain,
        }

        domains_data.append(transformed)

    return domains_data


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
    # Load domain nodes with all relationships via schema
    load(
        neo4j_session,
        ESDomainSchema(),
        domain_list,
        lastupdated=aws_update_tag,
        AWS_ID=aws_account_id,
    )

    # Process DNS and access policies (kept separate per plan)
    for domain in domain_list:
        original = domain.get("_original", {})
        domain_id = domain["DomainId"]
        _link_es_domains_to_dns(neo4j_session, domain_id, original, aws_update_tag)
        _process_access_policy(neo4j_session, domain_id, original)


@timeit
def _link_es_domains_to_dns(
    neo4j_session: neo4j.Session,
    domain_id: str,
    domain_data: Dict,
    aws_update_tag: int,
) -> None:
    """
    Link the ES domain to its DNS FQDN endpoint and create associated nodes in the graph
    if needed

    :param neo4j_session: Neo4j session object
    :param domain_id: ES domain id
    :param domain_data: domain data
    """
    # TODO add support for endpoints to this method
    if domain_data.get("Endpoint"):
        ingest_dns_record_by_fqdn(
            neo4j_session,
            aws_update_tag,
            domain_data["Endpoint"],
            domain_id,
            record_label="ESDomain",
            dns_node_additional_label="AWSDNSRecord",
        )
    else:
        logger.debug(f"No es endpoint data for domain id {domain_id}")


@timeit
def _process_access_policy(
    neo4j_session: neo4j.Session,
    domain_id: str,
    domain_data: Dict,
) -> None:
    """
    Link the ES domain to its DNS FQDN endpoint and create associated nodes in the graph
    if needed

    :param neo4j_session: Neo4j session object
    :param domain_id: ES domain id
    :param domain_data: domain data
    """
    tag_es = (
        "MATCH (es:ESDomain{id: $DomainId}) SET es.exposed_internet = $InternetExposed"
    )

    exposed_internet = False

    if domain_data.get("Endpoint") and domain_data.get("AccessPolicies"):
        policy = Policy(json.loads(domain_data["AccessPolicies"]))
        if policy.is_internet_accessible():
            exposed_internet = True

    run_write_query(
        neo4j_session,
        tag_es,
        DomainId=domain_id,
        InternetExposed=exposed_internet,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, update_tag: int, aws_account_id: int) -> None:
    # Clean up ESDomain nodes and schema-defined relationships
    GraphJob.from_node_schema(
        ESDomainSchema(),
        {"UPDATE_TAG": update_tag, "AWS_ID": aws_account_id},
    ).run(neo4j_session)

    # TODO: Keep raw Cypher here for DNS cleanup since _link_es_domains_to_dns() creates
    # DNSRecord:AWSDNSRecord nodes and DNS_POINTS_TO edges outside the schema.
    # This will be handled at the ontology level soon.
    cleanup_dns_query = """
        MATCH (:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(:ESDomain)<-[:DNS_POINTS_TO]-(n:DNSRecord)
        WHERE n.lastupdated <> $UPDATE_TAG
        DETACH DELETE n
    """
    run_write_query(
        neo4j_session,
        cleanup_dns_query,
        AWS_ID=aws_account_id,
        UPDATE_TAG=update_tag,
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
        client = boto3_session.client(
            "es",
            region_name=region,
            config=_get_botocore_config(),
        )
        data = _get_es_domains(client)
        domains_data = _transform_es_domains(data)
        _load_es_domains(
            neo4j_session,
            domains_data,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, update_tag, current_aws_account_id)  # type: ignore
