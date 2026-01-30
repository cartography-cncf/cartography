import logging
from collections import namedtuple
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.security_group_rules import IpPermissionInboundSchema
from cartography.models.aws.ec2.security_group_rules import IpRangeSchema
from cartography.models.aws.ec2.security_group_rules import IpRuleSchema
from cartography.models.aws.ec2.security_groups import EC2SecurityGroupSchema
from cartography.models.aws.ec2.securitygroup_instance import (
    EC2SecurityGroupInstanceSchema,
)
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_ec2_security_group_data(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict]:
    client = boto3_session.client(
        "ec2",
        region_name=region,
        config=get_botocore_config(),
    )
    paginator = client.get_paginator("describe_security_groups")
    security_groups: List[Dict] = []
    for page in paginator.paginate():
        security_groups.extend(page["SecurityGroups"])
    return security_groups


Ec2SecurityGroupData = namedtuple(
    "Ec2SecurityGroupData",
    ["groups", "inbound_rules", "egress_rules", "ranges"],
)


def transform_ec2_security_group_data(
    data: List[Dict[str, Any]],
) -> Ec2SecurityGroupData:
    groups: List[Dict[str, Any]] = []
    inbound_rules: List[Dict[str, Any]] = []
    egress_rules: List[Dict[str, Any]] = []
    ranges: List[Dict[str, Any]] = []

    for group in data:
        group_record = {
            "GroupId": group["GroupId"],
            "GroupName": group.get("GroupName"),
            "Description": group.get("Description"),
            "VpcId": group.get("VpcId"),
        }
        # Collect referenced security groups for relationship loading
        source_group_ids: set[str] = set()

        for rule_type, target in (
            ("IpPermissions", inbound_rules),
            ("IpPermissionsEgress", egress_rules),
        ):
            for rule in group.get(rule_type, []):
                protocol = rule.get("IpProtocol", "all")
                from_port = rule.get("FromPort")
                to_port = rule.get("ToPort")
                rule_id = (
                    f"{group['GroupId']}/{rule_type}/{from_port}{to_port}{protocol}"
                )
                target.append(
                    {
                        "RuleId": rule_id,
                        "GroupId": group["GroupId"],
                        "Protocol": protocol,
                        "FromPort": from_port,
                        "ToPort": to_port,
                    },
                )
                for ip_range in rule.get("IpRanges", []):
                    ranges.append({"RangeId": ip_range["CidrIp"], "RuleId": rule_id})
                for pair in rule.get("UserIdGroupPairs", []):
                    sg_id = pair.get("GroupId")
                    if sg_id:
                        source_group_ids.add(sg_id)

        group_record["SOURCE_GROUP_IDS"] = list(source_group_ids)
        groups.append(group_record)

    return Ec2SecurityGroupData(
        groups=groups,
        inbound_rules=inbound_rules,
        egress_rules=egress_rules,
        ranges=ranges,
    )


@timeit
def load_ip_rules(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    inbound: bool,
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    schema = IpPermissionInboundSchema() if inbound else IpRuleSchema()
    load(
        neo4j_session,
        schema,
        data,
        Region=region,
        AWS_ID=aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_ip_ranges(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        IpRangeSchema(),
        data,
        Region=region,
        AWS_ID=aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_ec2_security_groupinfo(
    neo4j_session: neo4j.Session,
    data: Ec2SecurityGroupData,
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EC2SecurityGroupSchema(),
        data.groups,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )

    load_ip_rules(
        neo4j_session,
        data.inbound_rules,
        inbound=True,
        region=region,
        aws_account_id=current_aws_account_id,
        update_tag=update_tag,
    )
    load_ip_rules(
        neo4j_session,
        data.egress_rules,
        inbound=False,
        region=region,
        aws_account_id=current_aws_account_id,
        update_tag=update_tag,
    )
    load_ip_ranges(
        neo4j_session,
        data.ranges,
        region,
        current_aws_account_id,
        update_tag,
    )


@timeit
def cleanup_ec2_security_groupinfo(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    GraphJob.from_node_schema(
        EC2SecurityGroupSchema(),
        common_job_parameters,
    ).run(neo4j_session)
    GraphJob.from_node_schema(IpPermissionInboundSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(IpRuleSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(IpRangeSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(
        EC2SecurityGroupInstanceSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_ec2_security_groupinfo(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info(
            "Syncing EC2 security groups for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        data = get_ec2_security_group_data(boto3_session, region)
        transformed = transform_ec2_security_group_data(data)
        load_ec2_security_groupinfo(
            neo4j_session,
            transformed,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup_ec2_security_groupinfo(neo4j_session, common_job_parameters)
