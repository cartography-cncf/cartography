import datetime


def create_test_account(neo4j_session, test_account_id, test_update_tag):
    # Create Test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag, aws :Tenant
        """,
        aws_account_id=test_account_id,
        aws_update_tag=test_update_tag,
    )


def make_load_balancer_v2(
    dns_name,
    scheme,
    lb_type,
    target_groups=(),
    *,
    account_id="123456789012",
    region="us-east-1",
    vpc_id="vpc-0example",
):
    """A DescribeLoadBalancers entry, with its target groups as (type, targets) pairs."""
    return {
        "DNSName": dns_name,
        "LoadBalancerName": dns_name.split(".")[0],
        "LoadBalancerArn": f"arn:aws:elasticloadbalancing:{region}:{account_id}:loadbalancer/{dns_name}",
        "CreatedTime": datetime.datetime(2026, 1, 1),
        "Type": lb_type,
        "Scheme": scheme,
        "Listeners": [{"ListenerArn": f"{dns_name}/listener", "Port": 443}],
        "TargetGroups": [
            {
                "TargetGroupArn": f"{dns_name}/targets",
                "TargetType": target_type,
                "VpcId": vpc_id,
                "Port": 443,
                "Protocol": "HTTPS",
                "Targets": targets,
            }
            for target_type, targets in target_groups
        ],
    }
