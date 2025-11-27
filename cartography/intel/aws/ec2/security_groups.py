import boto3
import neo4j
from botocore.exceptions import ClientError
from botocore.exceptions import EndpointConnectionError
from collections import namedtuple
import logging
from typing import Any
from typing import Dict
from typing import List
from cartography.util import timeit
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
from .util import get_botocore_config


logger = logging.getLogger(__name__)


Ec2SecurityGroupData = namedtuple(
    "Ec2SecurityGroupData",
    ["groups", "inbound_rules", "egress_rules", "ranges"],
)


@timeit
@aws_handle_regions
def get_ec2_security_group_rules(
    boto3_session: boto3.session.Session,
    region: str,
    group_id: str,
) -> List[Dict]:
    client = boto3_session.client(
        "ec2",
        region_name=region,
        config=get_botocore_config()
    )

    rules = []
    try:
        paginator = client.get_paginator("describe_security_group_rules")
        for page in paginator.paginate(Filters=[{'Name': 'group-id', 'Values': [group_id]}]):
            for rule in page.get('SecurityGroupRules', []):
                rules.append({
                    'RuleId': rule.get('SecurityGroupRuleId'),
                    'GroupId': group_id,
                    'Protocol': rule.get('IpProtocol', '-1'),
                    'FromPort': rule.get('FromPort'),
                    'ToPort': rule.get('ToPort'),
                    'IsEgress': rule.get('IsEgress', False),
                    'SecurityGroupRuleArn': rule.get('SecurityGroupRuleArn'),
                    'CidrIpv4': rule.get('CidrIpv4'),
                    'CidrIpv6': rule.get('CidrIpv6')
                })
        return rules

    except Exception as e:
        logger.warning(
            "Failed to get security group rules for group %s in region %s: %s",
            group_id, region, e,
            exc_info=logger.isEnabledFor(logging.DEBUG)
        )
        return []


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
    try:
        paginator = client.get_paginator("describe_security_groups")
        security_groups: List[Dict] = []
        for page in paginator.paginate():
            security_groups.extend(page.get("SecurityGroups", []))
        return security_groups
    except Exception as e:
        logger.warning(
            "Failed to get security groups for region %s: %s",
            region, e,
            exc_info=logger.isEnabledFor(logging.DEBUG)
        )
        return []


def transform_ec2_security_group_data(
    data: List[Dict[str, Any]],
    boto3_session: boto3.session.Session,
    region: str,
) -> Ec2SecurityGroupData:
    groups: List[Dict[str, Any]] = []
    inbound_rules: List[Dict[str, Any]] = []
    egress_rules: List[Dict[str, Any]] = []
    ranges: List[Dict[str, Any]] = []

    for group in data:
        group_id = group["GroupId"]
        source_group_ids = set()
        group_record = {
            "GroupId": group_id,
            "GroupName": group.get("GroupName"),
            "Description": group.get("Description"),
            "VpcId": group.get("VpcId"),
        }

        rules = get_ec2_security_group_rules(boto3_session, region, group_id)

        for rule in rules:
            rule_id = rule.get("RuleId") or rule.get("SecurityGroupRuleId")
            if not rule_id:
                logger.warning("Skipping security group rule with missing ID in group %s", group_id)
                continue

            is_egress = rule.get("IsEgress", False)

            rule_data = {
                "RuleId": rule_id,
                "GroupId": group_id,
                "Protocol": rule.get("IpProtocol"),
                "FromPort": rule.get("FromPort"),
                "ToPort": rule.get("ToPort"),
                "Arn": rule.get("SecurityGroupRuleArn"),
                "IsEgress": is_egress,
            }

            if rule.get("CidrIpv4"):
                ranges.append({"RangeId": rule["CidrIpv4"], "RuleId": rule_id})
            if rule.get("CidrIpv6"):
                ranges.append({"RangeId": rule["CidrIpv6"], "RuleId": rule_id})
            if "IpRanges" in rule:
                for ip_range in rule["IpRanges"]:
                    if "CidrIp" in ip_range:
                        ranges.append({"RangeId": ip_range["CidrIp"], "RuleId": rule_id})
            if rule.get("IsEgress"):
                egress_rules.append(rule_data)
            else:
                inbound_rules.append(rule_data)
            if 'ReferencedGroupInfo' in rule and rule['ReferencedGroupInfo']:
                sg_id = rule['ReferencedGroupInfo'].get('GroupId')
                if sg_id:
                    source_group_ids.add(sg_id)
        if source_group_ids:
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

    if data.inbound_rules:
        load_ip_rules(
            neo4j_session,
            data.inbound_rules,
            inbound=True,
            region=region,
            aws_account_id=current_aws_account_id,
            update_tag=update_tag,
        )

    if data.egress_rules:
        load_ip_rules(
            neo4j_session,
            data.egress_rules,
            inbound=False,
            region=region,
            aws_account_id=current_aws_account_id,
            update_tag=update_tag,
        )

    if data.ranges:
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
        try:
            security_groups = get_ec2_security_group_data(boto3_session, region)
            transformed_data = transform_ec2_security_group_data(
                security_groups, boto3_session, region
            )
            load_ec2_security_groupinfo(
                neo4j_session,
                transformed_data,
                region,
                current_aws_account_id,
                update_tag,
            )

        except Exception as e:
            logger.error(
                "Failed to sync security groups for region %s: %s",
                region, e,
                exc_info=True
            )

    cleanup_ec2_security_groupinfo(neo4j_session, common_job_parameters)
