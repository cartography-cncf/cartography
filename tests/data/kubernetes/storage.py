from datetime import datetime
from datetime import timezone

from kubernetes.client import V1Container
from kubernetes.client import V1CSIPersistentVolumeSource
from kubernetes.client import V1ObjectMeta
from kubernetes.client import V1ObjectReference
from kubernetes.client import V1PersistentVolume
from kubernetes.client import V1PersistentVolumeClaim
from kubernetes.client import V1PersistentVolumeClaimSpec
from kubernetes.client import V1PersistentVolumeClaimStatus
from kubernetes.client import V1PersistentVolumeClaimVolumeSource
from kubernetes.client import V1PersistentVolumeSpec
from kubernetes.client import V1PersistentVolumeStatus
from kubernetes.client import V1Pod
from kubernetes.client import V1PodSpec
from kubernetes.client import V1PodStatus
from kubernetes.client import V1ResourceRequirements
from kubernetes.client import V1StorageClass
from kubernetes.client import V1Volume
from kubernetes.client import V1VolumeMount

STORAGE_CLASS_NAME = "shared-csi"
VOLUME_NAME = "pvc-00000000-0000-0000-0000-000000000001"
CLAIM_NAME = "shared-data"
NAMESPACE = "my-namespace"
CREATION_TIMESTAMP = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
CREATION_EPOCH = 1767323045
DELETION_TIMESTAMP = datetime(2026, 1, 3, 3, 4, 5, tzinfo=timezone.utc)
DELETION_EPOCH = 1767409445

RAW_STORAGE_CLASSES = [
    V1StorageClass(
        metadata=V1ObjectMeta(
            name=STORAGE_CLASS_NAME,
            uid="00000000-0000-0000-0000-000000000000",
            creation_timestamp=CREATION_TIMESTAMP,
            deletion_timestamp=DELETION_TIMESTAMP,
        ),
        provisioner="csi.example.com",
        reclaim_policy="Retain",
        volume_binding_mode="Immediate",
        allow_volume_expansion=True,
        parameters={"filesystem": "project-data"},
        mount_options=["discard"],
    )
]

RAW_PERSISTENT_VOLUMES = [
    V1PersistentVolume(
        metadata=V1ObjectMeta(
            name=VOLUME_NAME,
            uid="00000000-0000-0000-0000-000000000002",
            labels={"storage.example.com/tier": "performance"},
            creation_timestamp=CREATION_TIMESTAMP,
            deletion_timestamp=DELETION_TIMESTAMP,
        ),
        spec=V1PersistentVolumeSpec(
            capacity={"storage": "2Pi"},
            access_modes=["ReadWriteMany"],
            persistent_volume_reclaim_policy="Retain",
            storage_class_name=STORAGE_CLASS_NAME,
            volume_mode="Filesystem",
            claim_ref=V1ObjectReference(namespace=NAMESPACE, name=CLAIM_NAME),
            csi=V1CSIPersistentVolumeSource(
                driver="csi.example.com",
                volume_handle="volume-0001",
            ),
        ),
        status=V1PersistentVolumeStatus(phase="Bound"),
    )
]

RAW_PERSISTENT_VOLUME_CLAIMS = [
    V1PersistentVolumeClaim(
        metadata=V1ObjectMeta(
            name=CLAIM_NAME,
            namespace=NAMESPACE,
            uid="00000000-0000-0000-0000-000000000003",
            labels={"data.example.com/classification": "restricted"},
            creation_timestamp=CREATION_TIMESTAMP,
            deletion_timestamp=DELETION_TIMESTAMP,
        ),
        spec=V1PersistentVolumeClaimSpec(
            access_modes=["ReadWriteMany"],
            resources=V1ResourceRequirements(requests={"storage": "2Pi"}),
            storage_class_name=STORAGE_CLASS_NAME,
            volume_mode="Filesystem",
            volume_name=VOLUME_NAME,
        ),
        status=V1PersistentVolumeClaimStatus(phase="Bound"),
    )
]

RAW_GPU_PODS = [
    V1Pod(
        metadata=V1ObjectMeta(
            name="training-job-head",
            namespace=NAMESPACE,
            uid="00000000-0000-0000-0000-000000000004",
            labels={
                "scheduler.example.com/user": "user-a",
                "workload.example.com/node-type": "head",
            },
        ),
        spec=V1PodSpec(
            node_name="gpu-worker-01",
            service_account_name="workload-scheduler",
            volumes=[
                V1Volume(
                    name="shared-data",
                    persistent_volume_claim=V1PersistentVolumeClaimVolumeSource(
                        claim_name=CLAIM_NAME
                    ),
                )
            ],
            containers=[
                V1Container(
                    name="worker",
                    image="example.com/training@sha256:0000",
                    resources=V1ResourceRequirements(
                        requests={
                            "cpu": "32",
                            "memory": "600Gi",
                            "nvidia.com/gpu": "8",
                        },
                        limits={
                            "memory": "1500Gi",
                            "nvidia.com/gpu": "8",
                        },
                    ),
                    volume_mounts=[
                        V1VolumeMount(name="shared-data", mount_path="/data")
                    ],
                )
            ],
        ),
        status=V1PodStatus(phase="Running", container_statuses=[]),
    )
]
