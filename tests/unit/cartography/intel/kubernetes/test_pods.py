from types import SimpleNamespace

from cartography.intel.kubernetes.pods import transform_pods


def test_transform_pods_defaults_service_account_name():
    pod = SimpleNamespace(
        metadata=SimpleNamespace(
            uid="pod-1",
            name="default-sa-pod",
            namespace="my-namespace",
            creation_timestamp=None,
            deletion_timestamp=None,
            labels={},
        ),
        spec=SimpleNamespace(
            containers=[],
            volumes=[],
            node_name="node-a",
            service_account_name=None,
        ),
        status=SimpleNamespace(phase="Running", container_statuses=[]),
    )

    transformed = transform_pods([pod], "my-cluster-1")

    assert transformed == [
        {
            "uid": "pod-1",
            "name": "default-sa-pod",
            "status_phase": "Running",
            "creation_timestamp": None,
            "deletion_timestamp": None,
            "namespace": "my-namespace",
            "service_account_name": "default",
            "service_account_id": "my-cluster-1/my-namespace/default",
            "node": "node-a",
            "node_id": "my-cluster-1/node-a",
            "architecture_normalized": None,
            "labels": "{}",
            "containers": [],
            "secret_volume_ids": [],
            "secret_env_ids": [],
        },
    ]


def test_transform_pods_propagates_node_architecture_to_pod_and_container():
    pod = SimpleNamespace(
        metadata=SimpleNamespace(
            uid="pod-2",
            name="arch-pod",
            namespace="my-namespace",
            creation_timestamp=None,
            deletion_timestamp=None,
            labels={},
        ),
        spec=SimpleNamespace(
            containers=[
                SimpleNamespace(
                    name="app",
                    image="example:latest",
                    image_pull_policy="IfNotPresent",
                    resources=None,
                    env=None,
                    env_from=None,
                ),
            ],
            volumes=[],
            node_name="node-a",
            service_account_name="default",
        ),
        status=SimpleNamespace(phase="Running", container_statuses=[]),
    )

    transformed = transform_pods(
        [pod],
        "my-cluster-1",
        node_arch_map={"node-a": "arm64"},
    )

    assert transformed[0]["architecture_normalized"] == "arm64"
    assert transformed[0]["containers"][0]["image_pull_policy"] == "IfNotPresent"
    assert transformed[0]["containers"][0]["architecture_normalized"] == "arm64"
