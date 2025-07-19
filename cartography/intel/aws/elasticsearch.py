import json
import logging
from typing import Any, Dict, List

import boto3
import neo4j
from policyuniverse.policy import Policy

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.intel.dns import ingest_dns_record_by_fqdn
from cartography.models.aws.elasticsearch.domain import ESDomainSchema
from cartography.util import aws_handle_regions, timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_es_domains(
    boto3_session: boto3.session.Session, region: str
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "es", region_name=region, config=get_botocore_config()
    )
    data = client.list_domain_names()
    domain_names = [d["DomainName"] for d in data.get("DomainNames", [])]
    domain_name_chunks = [
        domain_names[i : i + 5] for i in range(0, len(domain_names), 5)
    ]
    domains: List[Dict[str, Any]] = []
    for chunk in domain_name_chunks:
        chunk_data = client.describe_elasticsearch_domains(DomainNames=chunk)
        domains.extend(chunk_data.get("DomainStatusList", []))
    return domains


def transform_es_domains(
    domains: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    transformed: List[Dict[str, Any]] = []
    for d in domains:
        # ServiceSoftwareOptions contains datetime objects that Neo4j can't handle
        d.pop("ServiceSoftwareOptions", None)
        exposed_internet = False
        if d.get("Endpoint") and d.get("AccessPolicies"):
            policy = Policy(json.loads(d["AccessPolicies"]))
            exposed_internet = policy.is_internet_accessible()
        transformed.append(
            {
                "DomainId": d.get("DomainId"),
                "ARN": d.get("ARN"),
                "Deleted": d.get("Deleted"),
                "created": d.get("Created"),
                "Endpoint": d.get("Endpoint"),
                "ElasticsearchVersion": d.get("ElasticsearchVersion"),
                "ElasticsearchClusterConfig.InstanceType": d.get(
                    "ElasticsearchClusterConfig", {}
                ).get("InstanceType"),
                "ElasticsearchClusterConfig.InstanceCount": d.get(
                    "ElasticsearchClusterConfig", {}
                ).get("InstanceCount"),
                "ElasticsearchClusterConfig.DedicatedMasterEnabled": d.get(
                    "ElasticsearchClusterConfig", {}
                ).get("DedicatedMasterEnabled"),
                "ElasticsearchClusterConfig.ZoneAwarenessEnabled": d.get(
                    "ElasticsearchClusterConfig", {}
                ).get("ZoneAwarenessEnabled"),
                "ElasticsearchClusterConfig.DedicatedMasterType": d.get(
                    "ElasticsearchClusterConfig", {}
                ).get("DedicatedMasterType"),
                "ElasticsearchClusterConfig.DedicatedMasterCount": d.get(
                    "ElasticsearchClusterConfig", {}
                ).get("DedicatedMasterCount"),
                "EBSOptions.EBSEnabled": d.get("EBSOptions", {}).get("EBSEnabled"),
                "EBSOptions.VolumeType": d.get("EBSOptions", {}).get("VolumeType"),
                "EBSOptions.VolumeSize": d.get("EBSOptions", {}).get("VolumeSize"),
                "EBSOptions.Iops": d.get("EBSOptions", {}).get("Iops"),
                "EncryptionAtRestOptions.Enabled": d.get(
                    "EncryptionAtRestOptions", {}
                ).get("Enabled"),
                "EncryptionAtRestOptions.KmsKeyId": d.get(
                    "EncryptionAtRestOptions", {}
                ).get("KmsKeyId"),
                "LogPublishingOptions.CloudWatchLogsLogGroupArn": d.get(
                    "LogPublishingOptions", {}
                ).get("CloudWatchLogsLogGroupArn"),
                "LogPublishingOptions.Enabled": d.get("LogPublishingOptions", {}).get(
                    "Enabled"
                ),
                "exposed_internet": exposed_internet,
                "SubnetIds": d.get("VPCOptions", {}).get("SubnetIds", []),
                "SecurityGroupIds": d.get("VPCOptions", {}).get("SecurityGroupIds", []),
                "Region": region,
            }
        )
    return transformed


@timeit
def load_es_domains(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        ESDomainSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )

    for domain in data:
        if endpoint := domain.get("Endpoint"):
            ingest_dns_record_by_fqdn(
                neo4j_session,
                aws_update_tag,
                endpoint,
                domain["DomainId"],
                record_label="ESDomain",
                dns_node_additional_label="AWSDNSRecord",
            )


@timeit
def cleanup_es_domains(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ESDomainSchema(), common_job_parameters).run(
        neo4j_session
    )


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
            "Syncing Elasticsearch Service for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        raw_data = get_es_domains(boto3_session, region)
        transformed = transform_es_domains(raw_data, region)
        load_es_domains(
            neo4j_session, transformed, region, current_aws_account_id, update_tag
        )

    cleanup_es_domains(neo4j_session, common_job_parameters)
