import json
import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.waf.web_acl import WAFRuleSchema
from cartography.models.aws.waf.web_acl import WAFWebACLSchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

CLOUDFRONT_REGION = "us-east-1"
# API Gateway and CloudFront expose their WAF associations in their own APIs.
# Other ListResourcesForWebACL target types do not yet have Cartography models.
REGIONAL_RESOURCE_TYPES = (
    "APPLICATION_LOAD_BALANCER",
    "COGNITO_USER_POOL",
)


def _list_with_marker(
    client: Any,
    operation: str,
    result_key: str,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Collect a WAFv2 list operation, whose APIs don't expose boto3 paginators."""
    result: list[dict[str, Any]] = []
    while True:
        response = getattr(client, operation)(**kwargs)
        result.extend(response.get(result_key, []))
        marker = response.get("NextMarker")
        if not marker:
            return result
        kwargs["NextMarker"] = marker


@timeit
@aws_handle_regions
def get_web_acls(
    boto3_session: boto3.session.Session,
    region: str,
    scope: str,
    scan_status: dict[str, bool] | None = None,
) -> list[dict[str, Any]]:
    """Retrieve complete web ACL objects for one AWS WAF scope."""
    client = create_boto3_client(boto3_session, "wafv2", region_name=region)
    summaries = _list_with_marker(client, "list_web_acls", "WebACLs", Scope=scope)
    web_acls: list[dict[str, Any]] = []
    for summary in summaries:
        response = client.get_web_acl(ARN=summary["ARN"])
        web_acls.append(response["WebACL"])
    if scan_status is not None:
        scan_status["complete"] = True
    return web_acls


@timeit
@aws_handle_regions
def get_logging_configurations(
    boto3_session: boto3.session.Session,
    region: str,
    scope: str,
    scan_status: dict[str, bool] | None = None,
) -> list[dict[str, Any]]:
    """Retrieve customer-managed logging configurations for one AWS WAF scope."""
    client = create_boto3_client(boto3_session, "wafv2", region_name=region)
    configurations = _list_with_marker(
        client,
        "list_logging_configurations",
        "LoggingConfigurations",
        Scope=scope,
        LogScope="CUSTOMER",
    )
    if scan_status is not None:
        scan_status["complete"] = True
    return configurations


@timeit
@aws_handle_regions
def get_protected_resources(
    boto3_session: boto3.session.Session,
    region: str,
    web_acl_arn: str,
    scan_status: dict[str, bool] | None = None,
) -> list[dict[str, str]]:
    """Retrieve supported regional resources associated with a web ACL."""
    client = create_boto3_client(boto3_session, "wafv2", region_name=region)
    resources: list[dict[str, str]] = []
    for resource_type in REGIONAL_RESOURCE_TYPES:
        response = client.list_resources_for_web_acl(
            WebACLArn=web_acl_arn,
            ResourceType=resource_type,
        )
        resources.extend(
            {"ResourceType": resource_type, "ResourceArn": resource_arn}
            for resource_arn in response.get("ResourceArns", [])
        )
    if scan_status is not None:
        scan_status["complete"] = True
    return resources


def _json(value: Any) -> str | None:
    return json.dumps(value, sort_keys=True, default=str) if value else None


def _action_name(action: dict[str, Any] | None) -> str | None:
    return next(iter(action)).upper() if action else None


def _statement_metadata(statement: dict[str, Any]) -> dict[str, list[Any]]:
    metadata: dict[str, list[Any]] = {
        "StatementTypes": [],
        "ReferencedRuleGroupArns": [],
        "ReferencedIPSetArns": [],
        "ReferencedRegexPatternSetArns": [],
        "ManagedRuleGroups": [],
        "RateLimits": [],
    }

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key.endswith("Statement") and key not in metadata["StatementTypes"]:
                    metadata["StatementTypes"].append(key)
                if key == "RuleGroupReferenceStatement" and child.get("ARN"):
                    metadata["ReferencedRuleGroupArns"].append(child["ARN"])
                elif key == "IPSetReferenceStatement" and child.get("ARN"):
                    metadata["ReferencedIPSetArns"].append(child["ARN"])
                elif key == "RegexPatternSetReferenceStatement" and child.get("ARN"):
                    metadata["ReferencedRegexPatternSetArns"].append(child["ARN"])
                elif key == "ManagedRuleGroupStatement":
                    version = child.get("Version")
                    reference = f'{child["VendorName"]}/{child["Name"]}'
                    metadata["ManagedRuleGroups"].append(
                        f"{reference}/{version}" if version else reference,
                    )
                elif key == "RateBasedStatement" and child.get("Limit") is not None:
                    metadata["RateLimits"].append(child["Limit"])
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(statement)
    return metadata


def _transform_rule(
    rule: dict[str, Any],
    web_acl_arn: str,
    phase: str,
) -> dict[str, Any]:
    statement = rule.get("Statement") or rule.get("FirewallManagerStatement") or {}
    visibility = rule.get("VisibilityConfig", {})
    return {
        "RuleId": f'{web_acl_arn}:{phase}:{rule["Priority"]}:{rule["Name"]}',
        "WebACLArn": web_acl_arn,
        "Name": rule["Name"],
        "Priority": rule["Priority"],
        "Phase": phase,
        "Action": _action_name(rule.get("Action")),
        "OverrideAction": _action_name(rule.get("OverrideAction")),
        "Statement": _json(statement),
        "SampledRequestsEnabled": visibility.get("SampledRequestsEnabled"),
        "CloudWatchMetricsEnabled": visibility.get("CloudWatchMetricsEnabled"),
        "MetricName": visibility.get("MetricName"),
        **_statement_metadata(statement),
    }


def transform(
    web_acls: list[dict[str, Any]],
    logging_configurations: list[dict[str, Any]],
    protected_resources: dict[str, list[dict[str, str]]],
    region: str,
    scope: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Transform AWS WAF responses into web ACL and rule records."""
    logging_by_arn = {
        config["ResourceArn"]: config for config in logging_configurations
    }
    transformed_acls: list[dict[str, Any]] = []
    transformed_rules: list[dict[str, Any]] = []

    for web_acl in web_acls:
        arn = web_acl["ARN"]
        visibility = web_acl.get("VisibilityConfig", {})
        logging_config = logging_by_arn.get(arn, {})
        resources = protected_resources.get(arn, [])
        transformed_acls.append(
            {
                "ARN": arn,
                "Id": web_acl["Id"],
                "Name": web_acl["Name"],
                "Description": web_acl.get("Description"),
                "Scope": scope,
                "Region": region,
                "Capacity": web_acl.get("Capacity"),
                "DefaultAction": _action_name(web_acl.get("DefaultAction")),
                "ManagedByFirewallManager": web_acl.get("ManagedByFirewallManager"),
                "RetrofittedByFirewallManager": web_acl.get(
                    "RetrofittedByFirewallManager",
                ),
                "LabelNamespace": web_acl.get("LabelNamespace"),
                "TokenDomains": web_acl.get("TokenDomains"),
                "SampledRequestsEnabled": visibility.get("SampledRequestsEnabled"),
                "CloudWatchMetricsEnabled": visibility.get(
                    "CloudWatchMetricsEnabled",
                ),
                "MetricName": visibility.get("MetricName"),
                "LoggingEnabled": bool(logging_config),
                "LogDestinationConfigs": logging_config.get(
                    "LogDestinationConfigs",
                ),
                "RedactedFieldTypes": [
                    next(iter(field))
                    for field in logging_config.get("RedactedFields", [])
                    if field
                ],
                "LoggingFilter": _json(logging_config.get("LoggingFilter")),
                "AssociationConfig": _json(web_acl.get("AssociationConfig")),
                "OnSourceDDoSProtectionConfig": _json(
                    web_acl.get("OnSourceDDoSProtectionConfig"),
                ),
                "ProtectedLoadBalancerArns": [
                    resource["ResourceArn"]
                    for resource in resources
                    if resource["ResourceType"] == "APPLICATION_LOAD_BALANCER"
                ],
                "ProtectedCognitoUserPoolIds": [
                    resource["ResourceArn"].rsplit("/", 1)[-1]
                    for resource in resources
                    if resource["ResourceType"] == "COGNITO_USER_POOL"
                ],
            },
        )

        for phase, rules in (
            ("regular", web_acl.get("Rules", [])),
            ("pre_process", web_acl.get("PreProcessFirewallManagerRuleGroups", [])),
            ("post_process", web_acl.get("PostProcessFirewallManagerRuleGroups", [])),
        ):
            transformed_rules.extend(
                _transform_rule(rule, arn, phase) for rule in rules
            )

    return transformed_acls, transformed_rules


def load_web_acls(
    neo4j_session: neo4j.Session,
    web_acls: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        WAFWebACLSchema(),
        web_acls,
        lastupdated=update_tag,
        AWS_ID=current_aws_account_id,
    )
    load(
        neo4j_session,
        WAFRuleSchema(),
        rules,
        lastupdated=update_tag,
        AWS_ID=current_aws_account_id,
    )


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(WAFRuleSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(WAFWebACLSchema(), common_job_parameters).run(
        neo4j_session,
    )


def _sync_scope(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    region: str,
    scope: str,
    current_aws_account_id: str,
    update_tag: int,
) -> bool:
    scan_status: dict[str, bool] = {}
    web_acls = get_web_acls(boto3_session, region, scope, scan_status)
    if not scan_status.get("complete"):
        return False
    if not web_acls:
        return True

    scan_status = {}
    logging_configurations = get_logging_configurations(
        boto3_session,
        region,
        scope,
        scan_status,
    )
    if not scan_status.get("complete"):
        return False

    protected_resources: dict[str, list[dict[str, str]]] = {}
    if scope == "REGIONAL":
        for web_acl in web_acls:
            scan_status = {}
            resources = get_protected_resources(
                boto3_session,
                region,
                web_acl["ARN"],
                scan_status,
            )
            if not scan_status.get("complete"):
                return False
            protected_resources[web_acl["ARN"]] = resources
    transformed_acls, transformed_rules = transform(
        web_acls,
        logging_configurations,
        protected_resources,
        region,
        scope,
    )
    load_web_acls(
        neo4j_session,
        transformed_acls,
        transformed_rules,
        current_aws_account_id,
        update_tag,
    )
    return True


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """Sync regional and CloudFront-scoped AWS WAFv2 web ACLs."""
    scan_complete = True
    for region in regions:
        scan_complete = (
            _sync_scope(
                neo4j_session,
                boto3_session,
                region,
                "REGIONAL",
                current_aws_account_id,
                update_tag,
            )
            and scan_complete
        )

    scan_complete = (
        _sync_scope(
            neo4j_session,
            boto3_session,
            CLOUDFRONT_REGION,
            "CLOUDFRONT",
            current_aws_account_id,
            update_tag,
        )
        and scan_complete
    )
    if not scan_complete:
        logger.warning(
            "Skipping AWS WAF cleanup and sync metadata because the scan was incomplete",
        )
        return

    cleanup(neo4j_session, common_job_parameters)

    for synced_type in ("AWSWAFWebACL", "AWSWAFRule"):
        merge_module_sync_metadata(
            neo4j_session,
            group_type="AWSAccount",
            group_id=current_aws_account_id,
            synced_type=synced_type,
            update_tag=update_tag,
            stat_handler=stat_handler,
        )
