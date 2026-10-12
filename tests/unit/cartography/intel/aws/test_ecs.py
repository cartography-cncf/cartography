import logging
from copy import deepcopy
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError
from botocore.exceptions import EndpointConnectionError
from botocore.exceptions import ReadTimeoutError
from botocore.parsers import ResponseParserError

from cartography.intel.aws import ecs


@pytest.mark.parametrize(
    "getter,kwargs",
    [
        (ecs.get_ecs_cluster_arns, {}),
        (ecs.get_ecs_clusters, {"cluster_arns": ["cluster"]}),
        (ecs.get_ecs_container_instances, {"cluster_arn": "cluster"}),
        (ecs.get_ecs_services, {"cluster_arn": "cluster"}),
        (ecs.get_ecs_task_definitions, {"tasks": []}),
        (ecs.get_ecs_tasks, {"cluster_arn": "cluster"}),
    ],
)
@pytest.mark.parametrize(
    "exception", [ConnectTimeoutError, EndpointConnectionError, ReadTimeoutError]
)
def test_ecs_getters_distinguish_transport_failure_from_empty(
    getter, kwargs, exception
):
    # Arrange
    provider = MagicMock()
    error = exception(endpoint_url="https://ecs.example.invalid")
    provider.client.side_effect = error

    # Act and assert: no empty-list fallback or extra transport retry.
    with pytest.raises(ecs.ECSTransientRegionFailure) as failure:
        getter(boto3_session=provider, region="us-east-1", **kwargs)
    assert failure.value.__cause__ is error
    provider.client.assert_called_once()


@pytest.mark.parametrize(
    "error",
    [
        ClientError({"Error": {"Code": "ThrottlingException"}}, "ListClusters"),
        ResponseParserError("Synthetic malformed response"),
    ],
)
def test_ecs_getter_retains_aws_handle_regions_retries(error):
    # Arrange: the API fails once after the SDK's own retries, then succeeds.
    provider = MagicMock()
    paginator = provider.client.return_value.get_paginator.return_value
    paginator.paginate.side_effect = [error, [{"clusterArns": ["cluster"]}]]

    # Act
    result = ecs.get_ecs_cluster_arns(provider, "us-east-1")

    # Assert: the outer getter retry is still present.
    assert result == ["cluster"]
    assert paginator.paginate.call_count == 2


@pytest.mark.parametrize(
    "message",
    ["Synthetic denial", "Synthetic explicit deny in a service control policy"],
)
def test_ecs_getter_retains_access_denial_policy(message, caplog):
    # Arrange
    provider = MagicMock()
    provider.client.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": message}},
        "ListClusters",
    )

    # Act and assert: denial remains an empty result with the original diagnostic.
    assert ecs.get_ecs_cluster_arns(provider, "us-east-1") == []
    provider.client.assert_called_once()
    assert message in caplog.text


def test_ecs_getter_retains_invalid_token_guidance():
    # Arrange
    provider = MagicMock()
    provider.client.side_effect = ClientError(
        {"Error": {"Code": "InvalidToken"}}, "ListClusters"
    )

    # Act and assert
    with pytest.raises(RuntimeError, match="AWS_STS_REGIONAL_ENDPOINTS=regional"):
        ecs.get_ecs_cluster_arns(provider, "us-east-1")
    provider.client.assert_called_once()


def test_ecs_getter_preserves_handled_server_failure():
    # Arrange: this server error is normally swallowed by aws_handle_regions.
    provider = MagicMock()
    error = ClientError(
        {"Error": {"Code": "InternalServerErrorException"}}, "ListClusters"
    )
    provider.client.return_value.get_paginator.return_value.paginate.side_effect = error

    # Act and assert: distinguish failure from an authoritative empty inventory.
    with pytest.raises(ecs.ECSTransientRegionFailure) as failure:
        ecs.get_ecs_cluster_arns(provider, "us-east-1")
    assert failure.value.__cause__ is error
    provider.client.assert_called_once()


def _task_provider(arns_by_status, tasks_by_arn, failures=None):
    """An ECS client whose ListTasks pages depend on desiredStatus (None = unset)."""
    provider = MagicMock()
    client = provider.client.return_value
    client.get_paginator.return_value.paginate.side_effect = (
        lambda **kwargs: arns_by_status[kwargs.get("desiredStatus")]
    )
    client.describe_tasks.side_effect = lambda cluster, tasks: {
        "tasks": [tasks_by_arn[arn] for arn in tasks if arn in tasks_by_arn],
        "failures": [f for f in (failures or []) if f["arn"] in tasks],
    }
    return provider, client


def test_get_ecs_tasks_lists_running_tasks_only_by_default():
    # Arrange
    provider, client = _task_provider(
        {None: [{"taskArns": ["running"]}]},
        {"running": {"taskArn": "running", "lastStatus": "RUNNING"}},
    )

    # Act
    tasks = ecs.get_ecs_tasks("cluster", provider, "us-east-1")

    # Assert: the ListTasks call is unchanged, so its default (RUNNING) applies.
    client.get_paginator.return_value.paginate.assert_called_once_with(
        cluster="cluster"
    )
    assert tasks == [{"taskArn": "running", "lastStatus": "RUNNING"}]


def test_get_ecs_tasks_includes_stopped_tasks_once_each():
    # Arrange: 101 running tasks over two pages, one task that stopped between the
    # two listings (so it is listed under both statuses), and one stopped task.
    running = [f"task-{i}" for i in range(101)]
    provider, client = _task_provider(
        {
            "RUNNING": [
                {"taskArns": running[:60]},
                {"taskArns": running[60:] + ["moved"]},
            ],
            "STOPPED": [{"taskArns": ["moved"]}, {"taskArns": ["stopped"]}],
        },
        {
            **{arn: {"taskArn": arn, "lastStatus": "RUNNING"} for arn in running},
            # Described after it stopped: lastStatus, not the list, is the state.
            "moved": {"taskArn": "moved", "lastStatus": "STOPPED"},
            "stopped": {"taskArn": "stopped", "lastStatus": "STOPPED"},
        },
    )

    # Act
    tasks = ecs.get_ecs_tasks("cluster", provider, "us-east-1", include_stopped=True)

    # Assert
    paginate = client.get_paginator.return_value.paginate
    assert [c.kwargs for c in paginate.call_args_list] == [
        {"cluster": "cluster", "desiredStatus": "RUNNING"},
        {"cluster": "cluster", "desiredStatus": "STOPPED"},
    ]
    described = [c.kwargs["tasks"] for c in client.describe_tasks.call_args_list]
    assert [len(chunk) for chunk in described] == [100, 3]
    assert sum(described, []) == running + ["moved", "stopped"]
    assert [t["taskArn"] for t in tasks] == running + ["moved", "stopped"]
    assert {t["taskArn"]: t["lastStatus"] for t in tasks}["moved"] == "STOPPED"


def test_get_ecs_tasks_skips_tasks_that_expired_before_describe(caplog):
    # Arrange
    caplog.set_level(logging.INFO, logger="cartography.intel.aws.ecs")
    provider, _ = _task_provider(
        {"RUNNING": [{"taskArns": []}], "STOPPED": [{"taskArns": ["kept", "gone"]}]},
        {"kept": {"taskArn": "kept", "lastStatus": "STOPPED"}},
        failures=[{"arn": "gone", "reason": "MISSING"}],
    )

    # Act
    tasks = ecs.get_ecs_tasks("cluster", provider, "us-east-1", include_stopped=True)

    # Assert
    assert tasks == [{"taskArn": "kept", "lastStatus": "STOPPED"}]
    assert "gone" in caplog.text


def test_get_ecs_tasks_raises_on_other_describe_failures():
    # Arrange: a failure that is not an expired task means the inventory is partial.
    provider, _ = _task_provider(
        {None: [{"taskArns": ["kept", "unknown"]}]},
        {"kept": {"taskArn": "kept", "lastStatus": "RUNNING"}},
        failures=[{"arn": "unknown", "reason": "SYNTHETIC_FAILURE"}],
    )

    # Act and assert: never returned as a complete (and cleanable) inventory.
    with pytest.raises(ecs.ECSTransientRegionFailure, match="SYNTHETIC_FAILURE"):
        ecs.get_ecs_tasks("cluster", provider, "us-east-1")


def test_get_ecs_task_definitions_describes_each_definition_once():
    # Arrange
    provider = MagicMock()
    client = provider.client.return_value
    client.describe_task_definition.side_effect = lambda taskDefinition: {
        "taskDefinition": {"taskDefinitionArn": taskDefinition}
    }
    tasks = [
        {"taskDefinitionArn": "td:1"},
        {"taskDefinitionArn": "td:1"},
        {"taskDefinitionArn": "td:2"},
    ]

    # Act
    definitions = ecs.get_ecs_task_definitions(provider, "us-east-1", tasks)

    # Assert
    assert [d["taskDefinitionArn"] for d in definitions] == ["td:1", "td:2"]
    assert client.describe_task_definition.call_count == 2


def test_transform_ecs_tasks_keeps_network_interface_attachment():
    # Arrange
    from tests.data.aws.ecs import GET_ECS_STOPPED_TASK

    task = deepcopy(GET_ECS_STOPPED_TASK)

    # Act
    (transformed,) = ecs.transform_ecs_tasks([task])

    # Assert
    assert transformed["networkInterfaceId"] == "eni-11111111111111111"
    assert (
        transformed["networkInterfaceAttachmentId"]
        == "11111111-1111-1111-1111-111111111111"
    )
    assert transformed["networkInterfaceAttachmentStatus"] == "DELETED"
    assert transformed["networkInterfaceSubnetId"] == "subnet-11111111111111111"
    assert transformed["networkInterfacePrivateIpv4Address"] == "10.0.1.11"
    # A standalone task: parented by its cluster, with no service invented.
    assert "serviceName" not in transformed
    assert transformed["_workload_parent_cluster_arn"] == transformed["clusterArn"]
