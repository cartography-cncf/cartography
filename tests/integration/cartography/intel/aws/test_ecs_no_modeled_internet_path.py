"""ECS tasks that no internet path modelled in the graph reaches."""

from dataclasses import dataclass
from unittest.mock import patch

import pytest
from neo4j.exceptions import ServiceUnavailable

from cartography.analysis.aws.analysis import AWS_ECS_NO_MODELED_INTERNET_PATH
from cartography.graph.statement import GraphStatement
from cartography.intel.aws import _check_unmodeled_internet_paths
from cartography.intel.aws import _perform_aws_analysis
from cartography.intel.aws import _sync_one_account
from cartography.intel.aws import _withdraw_unmodeled_internet_paths_check
from cartography.intel.aws import apigateway
from cartography.intel.aws import apigatewayv2
from cartography.intel.aws import cloudfront
from cartography.intel.aws import ecs
from cartography.intel.aws.ec2 import load_balancer_v2s as elbv2
from cartography.intel.aws.ec2.elastic_ip_addresses import load_elastic_ip_addresses
from cartography.intel.aws.ec2.network_interfaces import load_network_data
from cartography.intel.aws.ec2.network_interfaces import (
    transform_network_interface_data,
)
from cartography.intel.aws.ec2.subnets import load_subnets
from cartography.intel.aws.resources import RESOURCE_FUNCTIONS
from cartography.util import run_typed_analysis_job
from tests.data.aws.cloudfront import CLOUDFRONT_DISTRIBUTIONS_VPC_ORIGIN
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.cartography.intel.aws.common import make_load_balancer_v2
from tests.integration.util import check_nodes

ACCOUNT = "123456789012"
LB_ACCOUNT = "000000000000"
OTHER_ACCOUNT = "210987654321"
REGION = "us-east-1"
VPC = "vpc-0example"
INTERNAL_ALB = "internal-app.example.invalid"
CHAINED_ALB = "internal-chained.example.invalid"
PUBLIC_ALB = "public-app.example.invalid"
PUBLIC_NLB = "public-edge.example.invalid"
VPC_LINK_INTEGRATION = "a1b2c3d4e5/r00t00/ANY"
HTTP_API = "f6g7h8i9j0"
ALL_SYNCS = frozenset(RESOURCE_FUNCTIONS)
ENTRY_POINT_SYNCS = frozenset({"apigateway", "apigatewayv2", "cloudfront"})


def _cluster(account):
    return f"arn:aws:ecs:{REGION}:{account}:cluster/example"


def _subnet(account):
    return f"subnet-{account}"


@dataclass(frozen=True)
class Workload:
    name: str
    ip: str
    network_mode: str = "awsvpc"
    public_ip: str | None = None
    secondary_public_ip: str | None = None
    ipv6: str | None = None
    # The load balancer whose target group the task's service is registered with.
    target_group: str | None = None
    # A task can start between the ENI and ECS syncs, so its ENI is not ingested yet.
    eni_ingested: bool = True
    account: str = ACCOUNT

    @property
    def task(self) -> str:
        return f"arn:aws:ecs:{REGION}:{self.account}:task/example/{self.name}"

    @property
    def container(self) -> str:
        return f"arn:aws:ecs:{REGION}:{self.account}:container/example/{self.name}/app"


PRIVATE = Workload("private", "10.0.1.10")
BEHIND_INTERNAL_ALB = Workload("behind-internal-alb", "10.0.1.11")
BEHIND_PUBLIC_ALB = Workload("behind-public-alb", "10.0.1.12")
PUBLIC_ALB_SERVICE = Workload(
    "public-alb-service", "10.0.1.13", target_group=PUBLIC_ALB
)
BEHIND_CHAINED_ALB = Workload("behind-chained-alb", "10.0.1.14")
PUBLIC_IP = Workload("public-ip", "10.0.1.15", public_ip="203.0.113.15")
IPV6 = Workload("ipv6", "10.0.1.16", ipv6="2001:db8::16")
SECONDARY_PUBLIC_IP = Workload(
    "secondary-public-ip", "10.0.1.20", secondary_public_ip="203.0.113.20"
)
BRIDGE = Workload("bridge", "10.0.1.17", network_mode="bridge")
HOST = Workload("host", "10.0.1.18", network_mode="host")
ENI_NOT_INGESTED = Workload("eni-not-ingested", "10.0.1.19", eni_ingested=False)
INTERNAL_ALB_SERVICE = Workload(
    "internal-alb-service", "10.0.1.21", target_group=INTERNAL_ALB
)
# The internal ALB's target group targets the service, and an internet-facing NLB
# forwards to that ALB.
CHAINED_ALB_SERVICE = Workload(
    "chained-alb-service", "10.0.1.22", target_group=CHAINED_ALB
)
WORKLOADS = (
    PRIVATE,
    BEHIND_INTERNAL_ALB,
    BEHIND_PUBLIC_ALB,
    PUBLIC_ALB_SERVICE,
    BEHIND_CHAINED_ALB,
    PUBLIC_IP,
    IPV6,
    SECONDARY_PUBLIC_IP,
    BRIDGE,
    HOST,
    ENI_NOT_INGESTED,
    INTERNAL_ALB_SERVICE,
    CHAINED_ALB_SERVICE,
)
CLEAR = {PRIVATE, BEHIND_INTERNAL_ALB, INTERNAL_ALB_SERVICE}


LOAD_BALANCERS = [
    make_load_balancer_v2(
        INTERNAL_ALB, "internal", "application", [("ip", [BEHIND_INTERNAL_ALB.ip])]
    ),
    make_load_balancer_v2(
        PUBLIC_ALB, "internet-facing", "application", [("ip", [BEHIND_PUBLIC_ALB.ip])]
    ),
    make_load_balancer_v2(
        CHAINED_ALB, "internal", "application", [("ip", [BEHIND_CHAINED_ALB.ip])]
    ),
    # An internet-facing NLB forwarding to an internal ALB reaches the ALB's targets.
    make_load_balancer_v2(
        PUBLIC_NLB,
        "internet-facing",
        "network",
        [
            (
                "alb",
                [
                    f"arn:aws:elasticloadbalancing:{REGION}:{ACCOUNT}:loadbalancer/{CHAINED_ALB}"
                ],
            )
        ],
    ),
]


# The static IP pattern for an ALB: an NLB whose IP target group lists the private
# IPs of an internal ALB's own interfaces.
LOAD_BALANCER_INTERFACE_IP = "10.0.1.200"
STATIC_IP_NLB = "static-ip.example.invalid"


def _load_balancer_interface(account):
    interface = _network_interface(
        Workload("internal-app-node", LOAD_BALANCER_INTERFACE_IP, account=account)
    )
    interface["Description"] = "ELB app/internal-app/50dc6c495c0c9188"
    interface["RequesterId"] = "amazon-elb"
    return interface


def _network_interface(workload):
    interface = {
        "NetworkInterfaceId": f"eni-{workload.name}",
        "Description": f"arn:aws:ecs:{REGION}:{workload.account}:attachment/{workload.name}",
        "InterfaceType": "interface",
        "MacAddress": "02:00:00:00:00:01",
        "RequesterManaged": True,
        "SourceDestCheck": True,
        "Status": "in-use",
        "SubnetId": _subnet(workload.account),
        "PrivateIpAddress": workload.ip,
        "PrivateIpAddresses": [{"PrivateIpAddress": workload.ip, "Primary": True}],
        "Ipv6Addresses": (
            [{"Ipv6Address": workload.ipv6, "IsPrimaryIpv6": True}]
            if workload.ipv6
            else []
        ),
    }
    if workload.public_ip:
        interface["Association"] = {"PublicIp": workload.public_ip}
    if workload.secondary_public_ip:
        interface["PrivateIpAddresses"].append(
            {
                "PrivateIpAddress": "10.0.2.20",
                "Primary": False,
                "Association": {"PublicIp": workload.secondary_public_ip},
            }
        )
    return interface


def _task(workload):
    task = {
        "taskArn": workload.task,
        "clusterArn": _cluster(workload.account),
        "taskDefinitionArn": f"arn:aws:ecs:{REGION}:{workload.account}:task-definition/{workload.name}:1",
        "lastStatus": "RUNNING",
        "containers": [
            {
                "containerArn": workload.container,
                "taskArn": workload.task,
                "name": "app",
                "lastStatus": "RUNNING",
            }
        ],
    }
    if workload.target_group:
        task["group"] = f"service:{workload.name}"
    if workload.network_mode == "awsvpc":
        task["attachments"] = [
            {
                "type": "ElasticNetworkInterface",
                "details": [
                    {"name": "networkInterfaceId", "value": f"eni-{workload.name}"}
                ],
            }
        ]
    return task


def _sync(
    session,
    tag,
    workloads=WORKLOADS,
    *,
    account=ACCOUNT,
    lb_account=None,
    vpc_origin=False,
    vpc_link=False,
    http_api=False,
    requested_syncs=ALL_SYNCS,
    check_lb_account=True,
    static_ip_nlb_scheme=None,
):
    """
    Run the requested syncs of `account` with the real loaders, in the AWS sync order,
    between the per-account withdrawal and check of unmodeled internet paths. When
    lb_account is set, the load balancers and the API Gateway REST integration live in
    that account, which shares the workloads' VPC, and it is synced by the same run.
    """
    create_test_account(session, account, tag)
    if lb_account:
        create_test_account(session, lb_account, tag)
    params = {"UPDATE_TAG": tag, "AWS_ID": account}
    checked = [account]
    if lb_account and lb_account != account and check_lb_account:
        checked.append(lb_account)
    for checked_account in checked:
        _withdraw_unmodeled_internet_paths_check(
            session,
            set(requested_syncs),
            {"UPDATE_TAG": tag, "AWS_ID": checked_account},
        )
    load_balancers = LOAD_BALANCERS + (
        [
            make_load_balancer_v2(
                STATIC_IP_NLB,
                static_ip_nlb_scheme,
                "network",
                [("ip", [LOAD_BALANCER_INTERFACE_IP])],
            )
        ]
        if static_ip_nlb_scheme
        else []
    )
    if "ec2:subnet" in requested_syncs:
        load_subnets(
            session,
            [{"SubnetId": _subnet(account), "VpcId": VPC}],
            REGION,
            account,
            tag,
        )
    if "ec2:network_interface" in requested_syncs:
        network = transform_network_interface_data(
            [
                _network_interface(w)
                for w in workloads
                if w.network_mode == "awsvpc" and w.eni_ingested
            ]
            + ([_load_balancer_interface(account)] if static_ip_nlb_scheme else []),
            REGION,
        )
        load_network_data(session, REGION, account, tag, **network._asdict())
    if lb_account and "ec2:load_balancer_v2" in requested_syncs:
        elbv2.load_load_balancer_v2s(session, load_balancers, REGION, lb_account, tag)

    if "ecs" in requested_syncs:
        # The ECS sync loads tasks before services, so a task of a service that is
        # new in this run gets no WORKLOAD_PARENT edge until the next run.
        tasks = ecs.transform_ecs_tasks([_task(w) for w in workloads])
        ecs.load_ecs_tasks(session, _cluster(account), tasks, REGION, account, tag)
        ecs.load_ecs_containers(
            session, ecs._get_containers_from_tasks(tasks), REGION, account, tag
        )
        ecs.load_ecs_task_definitions(
            session,
            [
                {
                    "taskDefinitionArn": t["taskDefinitionArn"],
                    "networkMode": w.network_mode,
                }
                for t, w in zip(tasks, workloads)
            ],
            REGION,
            account,
            tag,
        )
        ecs.load_ecs_services(
            session,
            _cluster(account),
            [
                {
                    "serviceArn": f"arn:aws:ecs:{REGION}:{account}:service/example/{w.name}",
                    "serviceName": w.name,
                    "clusterArn": _cluster(account),
                    "loadBalancers": [{"targetGroupArn": f"{w.target_group}/targets"}],
                }
                for w in workloads
                if w.target_group
            ],
            REGION,
            account,
            tag,
        )

    if "cloudfront" in requested_syncs:
        cloudfront.load_cloudfront_distributions(
            session,
            cloudfront.transform_cloudfront_distributions(
                CLOUDFRONT_DISTRIBUTIONS_VPC_ORIGIN if vpc_origin else []
            ),
            account,
            tag,
        )
        cloudfront.cleanup_cloudfront_distributions(session, params)
    if "apigatewayv2" in requested_syncs:
        apigatewayv2.load_apigatewayv2_apis(
            session,
            apigatewayv2.transform_apigatewayv2_apis(
                [{"ApiId": HTTP_API, "Name": "http", "ProtocolType": "HTTP"}]
                if http_api
                else []
            ),
            REGION,
            account,
            tag,
        )
        apigatewayv2.cleanup(session, params)
    if "apigateway" in requested_syncs:
        integration_account = lb_account or account
        if vpc_link:
            integration = {
                "apiId": "a1b2c3d4e5",
                "resourceId": "r00t00",
                "httpMethod": "ANY",
                "type": "HTTP_PROXY",
                "connectionType": "VPC_LINK",
                "connectionId": "vlk0example",
            }
            apigateway.load_rest_api_details(
                session,
                [("a1b2c3d4e5", [], None, [], [], [integration], None)],
                integration_account,
                tag,
            )
        apigateway.cleanup(session, {"UPDATE_TAG": tag, "AWS_ID": integration_account})

    if lb_account and "ec2:load_balancer_v2:expose" in requested_syncs:
        lb_params = {"UPDATE_TAG": tag, "AWS_ID": lb_account}
        with patch.object(
            elbv2, "get_loadbalancer_v2_data", return_value=load_balancers
        ):
            elbv2.sync_load_balancer_v2_expose(
                session, None, [REGION], lb_account, tag, lb_params
            )

    for checked_account in checked:
        _check_unmodeled_internet_paths(
            session,
            set(requested_syncs),
            {"UPDATE_TAG": tag, "AWS_ID": checked_account},
        )


def _analyze(session, tag, requested_syncs=ALL_SYNCS):
    _perform_aws_analysis(list(requested_syncs), session, {"UPDATE_TAG": tag})


def _results(session, label):
    return {
        (node_id, clear, checked_at)
        for node_id, clear, checked_at in check_nodes(
            session,
            label,
            ["id", "no_modeled_internet_path", "no_modeled_internet_path_checked_at"],
        )
        if clear is not None or checked_at is not None
    }


def _account_check(session, account=ACCOUNT):
    return (
        session.run(
            "MATCH (a:AWSAccount {id: $account}) "
            "RETURN a.unmodeled_internet_paths AS paths, "
            "a.unmodeled_internet_path_count AS count, "
            "a.unmodeled_internet_paths_checked_at AS checked_at",
            account=account,
        )
        .single()
        .data()
    )


@pytest.fixture
def neo4j_session_empty(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    return neo4j_session


def test_only_private_awsvpc_tasks_have_no_modeled_internet_path(
    neo4j_session_empty,
):
    session = neo4j_session_empty
    _sync(session, 1, lb_account=ACCOUNT)

    _analyze(session, 1)

    assert _results(session, "AWSECSTask") == {(w.task, True, 1) for w in CLEAR}
    assert _results(session, "AWSECSContainer") == {
        (w.container, True, 1) for w in CLEAR
    }
    # The internet-facing ALB has no security group open to 0.0.0.0/0, so its target
    # is not marked exposed. The scheme alone is enough to withhold the result.
    assert (BEHIND_PUBLIC_ALB.container, None) in check_nodes(
        session, "AWSECSContainer", ["id", "exposed_internet"]
    )
    assert _account_check(session) == {"paths": None, "count": 0, "checked_at": 1}


def test_result_is_dropped_when_a_later_run_finds_exposure(neo4j_session_empty):
    session = neo4j_session_empty
    _sync(session, 1, lb_account=ACCOUNT)
    _analyze(session, 1)

    exposed = Workload(PRIVATE.name, PRIVATE.ip, public_ip="203.0.113.10")
    workloads = tuple(exposed if w is PRIVATE else w for w in WORKLOADS)
    _sync(session, 2, workloads, lb_account=ACCOUNT)
    _analyze(session, 2)

    assert _results(session, "AWSECSTask") == {
        (w.task, True, 2) for w in CLEAR - {PRIVATE}
    }
    assert _results(session, "AWSECSContainer") == {
        (w.container, True, 2) for w in CLEAR - {PRIVATE}
    }


def test_failed_run_keeps_the_previous_result_and_tag(neo4j_session_empty):
    session = neo4j_session_empty
    _sync(session, 1, (PRIVATE,))
    _analyze(session, 1)

    run = GraphStatement.run

    def fail_cleanup(statement, neo4j_session):
        if statement.parent_job_name == "aws_ecs_no_modeled_internet_path" and (
            "REMOVE" in statement.query
        ):
            raise ServiceUnavailable("connection lost")
        return run(statement, neo4j_session)

    exposed = Workload(PRIVATE.name, PRIVATE.ip, public_ip="203.0.113.10")
    _sync(session, 2, (exposed,))
    with patch.object(GraphStatement, "run", autospec=True) as statement_run:
        statement_run.side_effect = fail_cleanup
        with pytest.raises(ServiceUnavailable):
            _analyze(session, 2)

    # The run did not clear the task again, and its cleanup never ran: the old result
    # stays, and its tag is now older than the task's lastupdated.
    assert check_nodes(
        session,
        "AWSECSTask",
        [
            "id",
            "no_modeled_internet_path",
            "no_modeled_internet_path_checked_at",
            "lastupdated",
        ],
    ) == {(PRIVATE.task, True, 1, 2)}


@pytest.mark.parametrize(
    "entry_point,path_id",
    [
        ({"vpc_origin": True}, CLOUDFRONT_DISTRIBUTIONS_VPC_ORIGIN[0]["ARN"]),
        ({"vpc_link": True}, VPC_LINK_INTEGRATION),
        ({"http_api": True}, HTTP_API),
    ],
    ids=["cloudfront_vpc_origin", "api_gateway_vpc_link", "api_gateway_v2_api"],
)
def test_account_with_an_unmodeled_path_gets_no_result_until_it_goes(
    neo4j_session_empty, entry_point, path_id
):
    session = neo4j_session_empty
    _sync(session, 1, (PRIVATE,), **entry_point)
    _analyze(session, 1)

    assert _results(session, "AWSECSTask") == set()
    assert _account_check(session) == {
        "paths": [path_id],
        "count": 1,
        "checked_at": 1,
    }

    _sync(session, 2, (PRIVATE,))
    _analyze(session, 2)

    assert _results(session, "AWSECSTask") == {(PRIVATE.task, True, 2)}
    assert _account_check(session) == {"paths": None, "count": 0, "checked_at": 2}


@pytest.mark.parametrize(
    "later_run,account_check",
    [
        # The account's check is newer than the task: a target group added since can
        # target the task's service without being linked to it.
        (
            {"requested_syncs": ALL_SYNCS - {"ecs"}},
            {"paths": None, "count": 0, "checked_at": 2},
        ),
        # Some of the check's inputs were synced, and an entry point appeared.
        (
            {"requested_syncs": ENTRY_POINT_SYNCS, "vpc_origin": True},
            {"paths": None, "count": None, "checked_at": None},
        ),
        # A load balancer added since would be missing.
        (
            {
                "requested_syncs": ALL_SYNCS
                - {"ec2:load_balancer_v2", "ec2:load_balancer_v2:expose"}
            },
            {"paths": None, "count": None, "checked_at": None},
        ),
        # IP targets resolve through the subnet's VPC, so one added since could be
        # missing.
        (
            {"requested_syncs": ALL_SYNCS - {"ec2:subnet"}},
            {"paths": None, "count": None, "checked_at": None},
        ),
    ],
    ids=[
        "without_ecs",
        "only_entry_points",
        "without_load_balancers",
        "without_subnets",
    ],
)
def test_later_run_without_every_input_retires_the_result(
    neo4j_session_empty, later_run, account_check
):
    session = neo4j_session_empty
    _sync(session, 1, (PRIVATE,))
    _analyze(session, 1)
    assert _results(session, "AWSECSTask") == {(PRIVATE.task, True, 1)}

    _sync(session, 2, (PRIVATE,), **later_run)
    _analyze(session, 2, later_run["requested_syncs"])

    assert _results(session, "AWSECSTask") == set()
    assert _results(session, "AWSECSContainer") == set()
    assert _account_check(session) == account_check


@pytest.mark.parametrize(
    "workload",
    [BEHIND_INTERNAL_ALB, INTERNAL_ALB_SERVICE],
    ids=["ip_target", "service_target_group"],
)
@pytest.mark.parametrize(
    "lb_account_state,expected_clear",
    [
        ({}, True),
        ({"vpc_link": True}, False),
        ({"check_lb_account": False}, False),
    ],
    ids=["clear", "unmodeled_path", "not_checked"],
)
def test_internal_load_balancer_in_another_account_needs_that_account_clear(
    neo4j_session_empty, workload, lb_account_state, expected_clear
):
    session = neo4j_session_empty
    # Shared VPC: the internal ALB belongs to another account, whose API Gateway VPC
    # link can put the internet in front of it.
    _sync(session, 1, (workload,), lb_account=LB_ACCOUNT, **lb_account_state)

    _analyze(session, 1)

    expected = {(workload.task, True, 1)} if expected_clear else set()
    assert _results(session, "AWSECSTask") == expected


@pytest.mark.parametrize(
    "scheme,expected",
    [
        ("internet-facing", set()),
        # The account's own entry points already count for an internal one.
        ("internal", {(BEHIND_INTERNAL_ALB.task, True, 1)}),
    ],
    ids=["internet_facing", "internal"],
)
def test_load_balancer_targeting_a_load_balancer_interface_withholds_its_targets(
    neo4j_session_empty, scheme, expected
):
    session = neo4j_session_empty
    # The graph does not link a load balancer's interfaces to it, so the internal
    # ALB in front of the task looks private.
    _sync(
        session,
        1,
        (BEHIND_INTERNAL_ALB,),
        lb_account=ACCOUNT,
        static_ip_nlb_scheme=scheme,
    )

    _analyze(session, 1)

    assert _results(session, "AWSECSTask") == expected


def test_load_balancer_interface_target_from_another_account_synced_later(
    neo4j_session_empty,
):
    session = neo4j_session_empty
    _sync(
        session,
        1,
        (BEHIND_INTERNAL_ALB,),
        lb_account=ACCOUNT,
        static_ip_nlb_scheme="internal",
    )
    _analyze(session, 1)
    assert _results(session, "AWSECSTask") == {(BEHIND_INTERNAL_ALB.task, True, 1)}

    # A later run syncs only another account in the shared VPC, whose NLB lists the
    # same interface. It counts even though it is internal.
    params = {"UPDATE_TAG": 2, "AWS_ID": OTHER_ACCOUNT}
    front = make_load_balancer_v2(
        "edge-static-ip.example.invalid",
        "internal",
        "network",
        [("ip", [LOAD_BALANCER_INTERFACE_IP])],
        account_id=OTHER_ACCOUNT,
    )
    create_test_account(session, OTHER_ACCOUNT, 2)
    elbv2.load_load_balancer_v2s(session, [front], REGION, OTHER_ACCOUNT, 2)
    with patch.object(elbv2, "get_loadbalancer_v2_data", return_value=[front]):
        elbv2.sync_load_balancer_v2_expose(
            session, None, [REGION], OTHER_ACCOUNT, 2, params
        )
    _check_unmodeled_internet_paths(session, set(ALL_SYNCS), params)
    _analyze(session, 2)

    assert _results(session, "AWSECSTask") == set()


def test_elastic_ip_linked_since_the_interface_sync_retires_the_result(
    neo4j_session_empty,
):
    session = neo4j_session_empty
    _sync(session, 1, (PRIVATE,))
    _analyze(session, 1)

    # A run that syncs only Elastic IPs links one to the task's interface, without
    # refreshing the interface's public IPv4 address.
    load_elastic_ip_addresses(
        session,
        [
            {
                "PublicIp": "203.0.113.30",
                "AllocationId": "eipalloc-0example",
                "AssociationId": "eipassoc-0example",
                "Domain": "vpc",
                "NetworkInterfaceId": f"eni-{PRIVATE.name}",
                "PrivateIpAddress": PRIVATE.ip,
            }
        ],
        REGION,
        ACCOUNT,
        2,
    )
    _analyze(session, 2, {"ec2:elastic_ip_addresses"})

    assert _results(session, "AWSECSTask") == set()


def test_accounts_synced_by_separate_runs_keep_their_results(neo4j_session_empty):
    session = neo4j_session_empty
    other = Workload("other-private", "10.0.3.10", account=OTHER_ACCOUNT)
    _sync(session, 1, (PRIVATE,))
    _analyze(session, 1)

    _sync(session, 2, (other,), account=OTHER_ACCOUNT)
    _analyze(session, 2)

    # The second run re-checks the first account's task against the whole graph, so
    # its result carries the newer tag while the task keeps its own lastupdated.
    assert check_nodes(
        session,
        "AWSECSTask",
        [
            "id",
            "no_modeled_internet_path",
            "no_modeled_internet_path_checked_at",
            "lastupdated",
        ],
    ) == {(PRIVATE.task, True, 2, 1), (other.task, True, 2, 2)}


def test_run_that_fails_part_way_leaves_the_account_unchecked(neo4j_session_empty):
    session = neo4j_session_empty
    _sync(session, 1, (PRIVATE,))
    _analyze(session, 1)

    def load_vpc_origin_then_fail(
        neo4j_session, current_aws_account_id, update_tag, **_
    ):
        cloudfront.load_cloudfront_distributions(
            neo4j_session,
            cloudfront.transform_cloudfront_distributions(
                CLOUDFRONT_DISTRIBUTIONS_VPC_ORIGIN
            ),
            current_aws_account_id,
            update_tag,
        )
        raise RuntimeError("a later module failed")

    with patch.dict(RESOURCE_FUNCTIONS, {"cloudfront": load_vpc_origin_then_fail}):
        with pytest.raises(RuntimeError):
            _sync_one_account(
                session,
                None,
                ACCOUNT,
                2,
                {"UPDATE_TAG": 2, "AWS_ID": ACCOUNT},
                regions=[REGION],
                aws_requested_syncs=["cloudfront"],
            )
    # The failed run did not sync the task, and a later run that syncs only another
    # account re-checks it.
    other = Workload("other-private", "10.0.3.10", account=OTHER_ACCOUNT)
    _sync(session, 3, (other,), account=OTHER_ACCOUNT)
    _analyze(session, 3)

    assert _results(session, "AWSECSTask") == {(other.task, True, 3)}
    assert _account_check(session) == {"paths": None, "count": None, "checked_at": None}


def test_result_is_never_written_on_a_runtime_marked_exposed(neo4j_session_empty):
    session = neo4j_session_empty
    _sync(session, 1, (PRIVATE,))
    # A future exposure rule may mark a container through a path this job does not
    # model. Run the job alone so the existing ECS rule does not clear the mark.
    session.run(
        "MATCH (c:AWSECSContainer {id: $id}) SET c.exposed_internet = true",
        id=PRIVATE.container,
    )

    run_typed_analysis_job(AWS_ECS_NO_MODELED_INTERNET_PATH, session, {"UPDATE_TAG": 1})

    assert _results(session, "AWSECSTask") == set()
    assert _results(session, "AWSECSContainer") == set()
