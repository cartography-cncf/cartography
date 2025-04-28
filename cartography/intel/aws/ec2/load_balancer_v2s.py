import logging
from typing import Dict
from typing import List

import boto3
import botocore
import neo4j

from .util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_load_balancer_v2_listeners(client: botocore.client.BaseClient, load_balancer_arn: str) -> List[Dict]:
    paginator = client.get_paginator('describe_listeners')
    listeners: List[Dict] = []
    for page in paginator.paginate(LoadBalancerArn=load_balancer_arn):
        listeners.extend(page['Listeners'])

    # Technically listeners don't have names, but the AWS console titles them as 'protocol':'port' so we'll do the same.
    for listener in listeners:
        listener['name'] = listener['Protocol'] + ":" + str(listener['Port'])
    return listeners


@timeit
@aws_handle_regions
def get_load_balancer_v2_rules(client: botocore.client.BaseClient, listener_arn: str) -> List[Dict]:
    paginator = client.get_paginator('describe_rules')
    rules: List[Dict] = []
    for page in paginator.paginate(ListenerArn=listener_arn):
        rules.extend(page['Rules'])

    # Enrich rule data with plain text summaries of any conditions and a unique ID for each action.
    # Add a human-friendly name to actions for convenient display.
    for i, rule in enumerate(rules):
        rules[i]['ConditionStrings'] = rule_conditions_to_strings(rule['Conditions'])
        for j, action in enumerate(rule['Actions']):
            rules[i]['Actions'][j]['id'] = f"{rule['RuleArn']}-action-{action.setdefault('Order', 'default')}"
            rules[i]['Actions'][j]['name'] = f"action-{action.setdefault('Order', 'default')}"
    return rules


@timeit
def get_load_balancer_v2_target_groups(client: botocore.client.BaseClient, load_balancer_arn: str) -> List[Dict]:
    paginator = client.get_paginator('describe_target_groups')
    target_groups: List[Dict] = []
    for page in paginator.paginate(LoadBalancerArn=load_balancer_arn):
        target_groups.extend(page['TargetGroups'])

    # Add instance data
    for target_group in target_groups:
        target_group['Targets'] = []
        target_health = client.describe_target_health(TargetGroupArn=target_group['TargetGroupArn'])
        for target_health_description in target_health['TargetHealthDescriptions']:
            target_group['Targets'].append(target_health_description['Target']['Id'])

    return target_groups


@timeit
def get_all_target_groups(client: botocore.client.BaseClient) -> List[Dict]:
    paginator = client.get_paginator('describe_target_groups')
    target_groups: List[Dict] = []
    for page in paginator.paginate():
        target_groups.extend(page['TargetGroups'])

    # Add instance data
    for target_group in target_groups:
        target_group['Targets'] = []
        target_health = client.describe_target_health(TargetGroupArn=target_group['TargetGroupArn'])
        for target_health_description in target_health['TargetHealthDescriptions']:
            target_group['Targets'].append(target_health_description['Target']['Id'])

    return target_groups


@timeit
@aws_handle_regions
def get_loadbalancer_v2_data(boto3_session: boto3.Session, region: str) -> List[Dict]:
    client = boto3_session.client('elbv2', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_load_balancers')
    elbv2s: List[Dict] = []
    for page in paginator.paginate():
        elbv2s.extend(page['LoadBalancers'])

    # Create a dict of load balancers keyed by ARN to their position in the list so that we can do a quick lookup
    # rather than repeatedly looping over the list to find load balancers when assigning target groups
    arn_list_index: Dict[str, int] = {elbv2s[i]['LoadBalancerArn']: i for i in range(0, len(elbv2s))}

    # Get all target groups in a single (paged) call and associate using the map to avoid making an API call for every
    # load balancer.
    for tg in get_all_target_groups(client):
        for lb_arn in tg['LoadBalancerArns']:
            if lb_arn in arn_list_index:
                if 'TargetGroups' in elbv2s[arn_list_index[lb_arn]]:
                    elbv2s[arn_list_index[lb_arn]]['TargetGroups'].append(tg)
                else:
                    elbv2s[arn_list_index[lb_arn]]['TargetGroups'] = [tg]

    # Make extra calls to get listeners, rules
    for elbv2 in elbv2s:
        elbv2['Listeners'] = get_load_balancer_v2_listeners(client, elbv2['LoadBalancerArn'])
        for listener in elbv2['Listeners']:
            listener['Rules'] = get_load_balancer_v2_rules(client, listener['ListenerArn'])
    return elbv2s


@timeit
def load_load_balancer_v2s(
    neo4j_session: neo4j.Session, data: List[Dict], region: str, current_aws_account_id: str,
    update_tag: int,
) -> None:
    ingest_load_balancer_v2 = """
    MERGE (elbv2:LoadBalancerV2{id: $ID})
    ON CREATE SET elbv2.firstseen = timestamp(), elbv2.createdtime = $CREATED_TIME
    SET elbv2.lastupdated = $update_tag, elbv2.name = $NAME, elbv2.dnsname = $DNS_NAME,
    elbv2.canonicalhostedzonenameid = $HOSTED_ZONE_NAME_ID,
    elbv2.type = $ELBv2_TYPE, elbv2.arn = $ARN,
    elbv2.scheme = $SCHEME, elbv2.region = $Region
    WITH elbv2
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(elbv2)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    for lb in data:
        load_balancer_id = lb["DNSName"]

        neo4j_session.run(
            ingest_load_balancer_v2,
            ID=load_balancer_id,
            CREATED_TIME=str(lb["CreatedTime"]),
            NAME=lb["LoadBalancerName"],
            DNS_NAME=load_balancer_id,
            HOSTED_ZONE_NAME_ID=lb.get("CanonicalHostedZoneNameID"),
            ARN=lb["LoadBalancerArn"],
            ELBv2_TYPE=lb.get("Type"),
            SCHEME=lb.get("Scheme"),
            AWS_ACCOUNT_ID=current_aws_account_id,
            Region=region,
            update_tag=update_tag,
        )

        if lb["AvailabilityZones"]:
            az = lb["AvailabilityZones"]
            load_load_balancer_v2_subnets(neo4j_session, load_balancer_id, az, region, update_tag)

        # NLB's don't have SecurityGroups, so check for one first.
        if 'SecurityGroups' in lb and lb["SecurityGroups"]:
            ingest_load_balancer_v2_security_group = """
            MATCH (elbv2:LoadBalancerV2{id: $ID}),
            (group:EC2SecurityGroup{groupid: $GROUP_ID})
            MERGE (elbv2)-[r:MEMBER_OF_EC2_SECURITY_GROUP]->(group)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $update_tag
            """
            for group in lb["SecurityGroups"]:
                neo4j_session.run(
                    ingest_load_balancer_v2_security_group,
                    ID=load_balancer_id,
                    GROUP_ID=str(group),
                    update_tag=update_tag,
                )

        # Add an EXPOSE relationship to resources linked to the Load Balancer via a Target Group
        if lb['TargetGroups']:
            load_load_balancer_v2_target_groups(
                neo4j_session, load_balancer_id, lb['TargetGroups'],
                current_aws_account_id, update_tag,
            )

        if lb['Listeners']:
            load_load_balancer_v2_listeners(neo4j_session, load_balancer_id, lb['Listeners'], update_tag)
            for listener in lb['Listeners']:
                load_load_balancer_v2_listener_rules(
                    neo4j_session, listener['ListenerArn'], listener['Rules'], update_tag,
                )
                for rule in listener['Rules']:
                    load_load_balancer_v2_actions(
                        neo4j_session, rule['RuleArn'], rule['Actions'], update_tag,
                    )
                    # Add TARGET_GROUP_TARGET relationships to resources for traffic flow analysis
                    load_load_balancer_v2_target_group_targets(
                        neo4j_session, rule, lb, current_aws_account_id, update_tag,
                    )


@timeit
def load_load_balancer_v2_subnets(
        neo4j_session: neo4j.Session, load_balancer_id: str, az_data: List[Dict],
        region: str, update_tag: int,
) -> None:
    ingest_load_balancer_subnet = """
    MATCH (elbv2:LoadBalancerV2{id: $ID})
    MERGE (subnet:EC2Subnet{subnetid: $SubnetId})
    ON CREATE SET subnet.firstseen = timestamp()
    SET subnet.region = $region, subnet.lastupdated = $update_tag
    WITH elbv2, subnet
    MERGE (elbv2)-[r:SUBNET]->(subnet)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    for az in az_data:
        neo4j_session.run(
            ingest_load_balancer_subnet,
            ID=load_balancer_id,
            SubnetId=az['SubnetId'],
            region=region,
            update_tag=update_tag,
        )


@timeit
def load_load_balancer_v2_target_groups(
    neo4j_session: neo4j.Session, load_balancer_id: str, target_groups: List[Dict], current_aws_account_id: str,
    update_tag: int,
) -> None:
    ingest_instances = """
    MATCH (elbv2:LoadBalancerV2{id: $ID}), (instance:EC2Instance{instanceid: $INSTANCE_ID})
    MERGE (elbv2)-[r:EXPOSE]->(instance)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag,
        r.port = $PORT, r.protocol = $PROTOCOL,
        r.target_group_arn = $TARGET_GROUP_ARN
    WITH instance
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(instance)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    for target_group in target_groups:

        if not target_group['TargetType'] == 'instance':
            # Only working on EC2 Instances now. TODO: Add IP & Lambda EXPOSE.
            continue

        for instance in target_group["Targets"]:
            neo4j_session.run(
                ingest_instances,
                ID=load_balancer_id,
                INSTANCE_ID=instance,
                AWS_ACCOUNT_ID=current_aws_account_id,
                TARGET_GROUP_ARN=target_group.get('TargetGroupArn'),
                PORT=target_group.get('Port'),
                PROTOCOL=target_group.get('Protocol'),
                update_tag=update_tag,
            )


@timeit
def load_load_balancer_v2_target_group_targets(
        neo4j_session: neo4j.Session, rule_data: Dict, lb_data: Dict, current_aws_account_id: str, update_tag: int,
) -> None:
    """Create target group relationships from ELBV2Actions to targets"""

    ingest_target_group_relationships = {
        "instance": """
            MATCH (action:ELBV2ForwardAction{id: $ActionId})
            WITH action
            UNWIND $Targets as target
                MATCH (instance:EC2Instance{instanceid: target})
                MERGE (action)-[r:TARGET_GROUP_TARGET{weight: $WEIGHT}]->(instance)
                ON CREATE SET r.firstseen = timestamp()
                SET r.lastupdated = $update_tag,
                    r.target_group_name = $TargetGroupName
                WITH instance
                MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
                MERGE (aa)-[r:RESOURCE]->(instance)
                ON CREATE SET r.firstseen = timestamp()
                SET r.lastupdated = $update_tag
            """,
        "ip": """
            MATCH (action:ELBV2ForwardAction{id: $ActionId})
            WITH action
            UNWIND $Targets as target
                MATCH (ip:Ip{id: target})
                MERGE (action)-[r:TARGET_GROUP_TARGET{weight: $WEIGHT}]->(ip)
                ON CREATE SET r.firstseen = timestamp()
                SET r.lastupdated = $update_tag,
                    r.target_group_name = $TargetGroupName
            """,
        "lambda": """
            MATCH (action:ELBV2ForwardAction{id: $ActionId})
            WITH action
            UNWIND $Targets as target
                MATCH (lambda:AWSLambda{id: target})
                MERGE (action)-[r:TARGET_GROUP_TARGET{weight: $WEIGHT}]->(lambda)
                ON CREATE SET r.firstseen = timestamp()
                SET r.lastupdated = $update_tag,
                    r.target_group_name = $TargetGroupName
                WITH lambda
                MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
                MERGE (aa)-[r:RESOURCE]->(lambda)
                ON CREATE SET r.firstseen = timestamp()
                SET r.lastupdated = $update_tag
            """,
        "alb": """
            MATCH (action:ELBV2ForwardAction{id: $ActionId})
            WITH action
            UNWIND $Targets as target
                MATCH (lb:LoadBalancerV2{arn: target})
                MERGE (action)-[r:TARGET_GROUP_TARGET{weight: $WEIGHT}]->(lb)
                ON CREATE SET r.firstseen = timestamp()
                SET r.lastupdated = $update_tag,
                    r.target_group_name = $TargetGroupName
                WITH lb
                MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
                MERGE (aa)-[r:RESOURCE]->(lb)
                ON CREATE SET r.firstseen = timestamp()
                SET r.lastupdated = $update_tag
            """,
    }

    for action in rule_data['Actions']:
        # Only 'forward' type actions have links to target groups so others can be skipped
        if action['Type'] != "forward":
            continue
        for forwarder_target_group in action['ForwardConfig']['TargetGroups']:
            # Find the actual target group info in the load balancer data by iterating over the general load balancer
            # data dict until we find a matching ARN.
            for target_group in lb_data['TargetGroups']:
                if target_group['TargetGroupArn'] == forwarder_target_group['TargetGroupArn']:
                    # Then add relationships to the appropriate objects using the TargetType to select one of the above
                    # queries.
                    neo4j_session.run(
                        ingest_target_group_relationships[target_group['TargetType']],
                        ActionId=f"{rule_data['RuleArn']}-action-{action.get('Order', 'default')}",
                        Targets=target_group['Targets'],
                        WEIGHT=forwarder_target_group.get('Weight', 0),
                        TargetGroupName=target_group['TargetGroupName'],
                        AWS_ACCOUNT_ID=current_aws_account_id,
                        update_tag=update_tag,
                    )
                    break
    return


@timeit
def load_load_balancer_v2_listeners(
        neo4j_session: neo4j.Session, load_balancer_id: str, listener_data: List[Dict],
        update_tag: int,
) -> None:
    ingest_listener = """
    MATCH (elbv2:LoadBalancerV2{id: $LoadBalancerId})
    WITH elbv2
    UNWIND $Listeners as data
        MERGE (l:Endpoint:ELBV2Listener{id: data.ListenerArn})
        ON CREATE SET l.port = data.Port, l.protocol = data.Protocol,
            l.firstseen = timestamp(),
            l.targetgrouparn = data.TargetGroupArn
        SET l.lastupdated = $update_tag,
            l.ssl_policy = data.SslPolicy,
            l.name = data.name
        WITH l, elbv2
        MERGE (elbv2)-[r:ELBV2_LISTENER]->(l)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """
    neo4j_session.run(
        ingest_listener,
        LoadBalancerId=load_balancer_id,
        Listeners=listener_data,
        update_tag=update_tag,
    )


def rule_conditions_to_strings(conditions: List[Dict]) -> Dict:
    result = {}
    for cnd in conditions:
        if cnd['Field'] == 'http-header':
            result['http_header'] = f"{cnd['HttpHeaderConfig']['HttpHeaderName']}==[sensitive]"
        elif cnd['Field'] == 'http-request-method':
            result['http_request_method'] = '|'.join(cnd['HttpRequestMethodConfig']['Values'])
        elif cnd['Field'] == 'host-header':
            result['host_header'] = '|'.join(cnd['HostHeaderConfig']['Values'])
        elif cnd['Field'] == 'path-pattern':
            result['path_pattern'] = '|'.join(cnd['PathPatternConfig']['Values'])
        elif cnd['Field'] == 'query-string':
            result['query_string'] = '|'.join([f"{k}={v}" for k, v in cnd['QueryStringConfig']['Values'].items()])
        elif cnd['Field'] == 'source-ip':
            result['source_ip'] = '|'.join(cnd['SourceIpConfig']['Values'])
    return result


def action_ingest_statement(type: str, additional: str) -> str:
    statement = """
    MATCH (rule:ELBV2Rule{id: $RuleId})-[ATTACHED_TO]->(listener:ELBV2Listener)
    WITH listener, rule
    UNWIND $Actions as action
        MERGE (listener)-[rr:ELBV2_LISTENER_RULE]->(actionNode:ELBV2Action:""" + type + """{id: action.id})
        ON CREATE SET actionNode.firstseen = timestamp(),
            rr.firstseen = timestamp()
        SET actionNode.lastupdated = $update_tag,
            actionNode.name = action.name,
            // Copy rule properties to the relationship for simplified queries
            rr.priority = rule.priority,
            rr.http_header_condition = rule.http_header_condition,
            rr.http_request_method_condition = rule.http_request_method_condition,
            rr.host_header_condition = rule.host_header_condition,
            rr.path_pattern_condition = rule.path_pattern_condition,
            rr.query_string_condition = rule.query_string_condition,
            rr.source_ip_condition = rule.source_ip_condition,
            rr.lastupdated = $update_tag"""
    if additional != "":
        statement += f",\n{additional}"
    statement += """
        WITH rule, actionNode
        MERGE (rule)<-[r2:ATTACHED_TO]-(actionNode)
        ON CREATE SET r2.firstseen = timestamp(),
            r2.firstseen = timestamp()
    """
    return statement


def load_load_balancer_v2_actions(
        neo4j_session: neo4j.Session, rule_arn: str, action_data: List[Dict], update_tag: int,
) -> None:
    oidc_additional_statements = """
            actionNode.on_unauthenticated_request = action.AuthenticateOidcActionConfig.OnUnauthenticatedRequest
    """
    cognito_additional_statements = """
            actionNode.on_unauthenticated_request = action.AuthenticateCognitoActionConfig.OnUnauthenticatedRequest,
            actionNode.user_pool_arn = action.AuthenticateCognitoActionConfig.UserPoolArn
    """
    redirect_additional_statements = """
            actionNode.protocol = action.RedirectConfig.Protocol,
            actionNode.port = action.RedirectConfig.Port,
            actionNode.host = action.RedirectConfig.Host,
            actionNode.path = action.RedirectConfig.Path,
            actionNode.query = action.RedirectConfig.Query,
            actionNode.status_code = action.RedirectConfig.StatusCode
    """
    fixed_response_additional_statements = """
            actionNode.status_code = action.FixedResponseActionConfig.StatusCode,
            actionNode.message_body = action.FixedResponseActionConfig.MessageBody,
            actionNode.content_type = action.FixedResponseActionConfig.ContentType
    """

    # TODO: Clean this up by sorting actions by type only once, DRYing neo4j calls

    neo4j_session.run(
        action_ingest_statement('ELBV2ForwardAction', ""),
        RuleId=rule_arn,
        Actions=[action for action in action_data if action['Type'] == "forward"],
        update_tag=update_tag,
    )
    neo4j_session.run(
        action_ingest_statement('ELBV2AuthenticateOIDCAction', oidc_additional_statements),
        RuleId=rule_arn,
        Actions=[action for action in action_data if action['Type'] == "authenticate-oidc"],
        update_tag=update_tag,
    )
    neo4j_session.run(
        action_ingest_statement('ELBV2AuthenticateCognitoAction', cognito_additional_statements),
        RuleId=rule_arn,
        Actions=[action for action in action_data if action['Type'] == "authenticate-cognito"],
        update_tag=update_tag,
    )
    neo4j_session.run(
        action_ingest_statement('ELBV2RedirectAction', redirect_additional_statements),
        RuleId=rule_arn,
        Actions=[action for action in action_data if action['Type'] == "redirect"],
        update_tag=update_tag,
    )
    neo4j_session.run(
        action_ingest_statement('ELBV2FixedResponseAction', fixed_response_additional_statements),
        RuleId=rule_arn,
        Actions=[action for action in action_data if action['Type'] == "fixed-response"],
        update_tag=update_tag,
    )
    return


@timeit
def load_load_balancer_v2_listener_rules(
        neo4j_session: neo4j.Session, listener_arn: str, rule_data: List[Dict],
        update_tag: int,
) -> None:
    ingest_rule = """
    MATCH (listener:Endpoint:ELBV2Listener{id: $ListenerARN})
    WITH listener
    UNWIND $Rules as data
        MERGE (rule:ELBV2Rule{id: data.RuleArn})
        ON CREATE SET rule.firstseen = timestamp()
        SET rule.lastupdated = $update_tag,
            rule.priority = data.Priority,
            rule.http_header_condition = data.ConditionStrings.http_header,
            rule.http_request_method_condition = data.ConditionStrings.http_request_method,
            rule.host_header_condition = data.ConditionStrings.host_header,
            rule.path_pattern_condition = data.ConditionStrings.path_pattern,
            rule.query_string_condition = data.ConditionStrings.query_string,
            rule.source_ip_condition = data.ConditionStrings.source_ip
        WITH rule, listener
        MERGE (listener)<-[r:ATTACHED_TO]-(rule)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """

    neo4j_session.run(
        ingest_rule,
        ListenerARN=listener_arn,
        Rules=rule_data,
        update_tag=update_tag,
    )


@timeit
def cleanup_load_balancer_v2s(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """Delete elbv2's and dependent resources in the DB without the most recent lastupdated tag."""
    run_cleanup_job('aws_ingest_load_balancers_v2_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_load_balancer_v2s(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info("Syncing EC2 load balancers v2 for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_loadbalancer_v2_data(boto3_session, region)
        load_load_balancer_v2s(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_load_balancer_v2s(neo4j_session, common_job_parameters)
