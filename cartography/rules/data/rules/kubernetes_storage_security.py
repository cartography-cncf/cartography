from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference


class KubernetesContainerPersistentStorageFinding(Finding):
    container_name: str | None = None
    container_id: str | None = None
    namespace: str | None = None
    cluster_name: str | None = None
    claim_names: list[str] | None = None
    claim_ids: list[str] | None = None
    mount_details: str | None = None
    device_details: str | None = None


_internet_exposed_writable_persistent_storage = Fact(
    id="kubernetes-internet-exposed-writable-persistent-storage",
    name="Internet-Exposed Container with Writable Persistent Storage",
    description=(
        "Finds internet-exposed Kubernetes containers that mount one or more "
        "PersistentVolumeClaims with write access. Compromise of the container can "
        "put persistent application data at risk of modification or disclosure."
    ),
    cypher_query="""
    MATCH (container:KubernetesContainer)-[:MOUNTS]->(claim:KubernetesPersistentVolumeClaim)
    WHERE container.exposed_internet = true
      AND claim.id IN coalesce(container.persistent_volume_claim_read_write_ids, [])
    WITH DISTINCT container, claim
    ORDER BY claim.id
    WITH
        container,
        collect(claim.name) AS claim_names,
        collect(claim.id) AS claim_ids
    RETURN
        container.name AS container_name,
        container.id AS container_id,
        container.namespace AS namespace,
        container.cluster_name AS cluster_name,
        claim_names AS claim_names,
        claim_ids AS claim_ids,
        container.persistent_volume_claim_mounts AS mount_details
    ORDER BY container_id
    """,
    cypher_visual_query="""
    MATCH p=(container:KubernetesContainer)-[:MOUNTS]->(claim:KubernetesPersistentVolumeClaim)
    WHERE container.exposed_internet = true
      AND claim.id IN coalesce(container.persistent_volume_claim_read_write_ids, [])
    RETURN *
    """,
    cypher_count_query="""
    MATCH (container:KubernetesContainer)
    RETURN COUNT(container) AS count
    """,
    asset_label="KubernetesContainer",
    asset_id_field="container_id",
    identity_fields=("container_id",),
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)


_raw_block_persistent_storage = Fact(
    id="kubernetes-container-raw-block-persistent-storage",
    name="Container Using Raw Block Persistent Storage",
    description=(
        "Finds Kubernetes containers that receive PersistentVolumeClaims as raw block "
        "devices. Direct block-device access bypasses filesystem-level controls and "
        "should be limited to workloads that require it."
    ),
    cypher_query="""
    MATCH (container:KubernetesContainer)-[:USES_BLOCK_DEVICE]->(claim:KubernetesPersistentVolumeClaim)
    WITH DISTINCT container, claim
    ORDER BY claim.id
    WITH
        container,
        collect(claim.name) AS claim_names,
        collect(claim.id) AS claim_ids
    RETURN
        container.name AS container_name,
        container.id AS container_id,
        container.namespace AS namespace,
        container.cluster_name AS cluster_name,
        claim_names AS claim_names,
        claim_ids AS claim_ids,
        container.persistent_volume_claim_devices AS device_details
    ORDER BY container_id
    """,
    cypher_visual_query="""
    MATCH p=(container:KubernetesContainer)-[:USES_BLOCK_DEVICE]->(claim:KubernetesPersistentVolumeClaim)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (container:KubernetesContainer)
    RETURN COUNT(container) AS count
    """,
    asset_label="KubernetesContainer",
    asset_id_field="container_id",
    identity_fields=("container_id",),
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)


kubernetes_internet_exposed_containers_with_writable_persistent_storage = Rule(
    id="kubernetes-internet-exposed-containers-with-writable-persistent-storage",
    name="Internet-Exposed Containers with Writable Persistent Storage",
    description=(
        "Identifies internet-exposed Kubernetes containers that can write to "
        "persistent storage. Review whether the exposure and write access are both "
        "necessary, and apply workload, network, and storage controls to reduce the "
        "impact of a container compromise."
    ),
    output_model=KubernetesContainerPersistentStorageFinding,
    facts=(_internet_exposed_writable_persistent_storage,),
    tags=(
        "kubernetes",
        "data",
        "attack_surface",
        "stride:tampering",
        "stride:information_disclosure",
    ),
    version="0.1.0",
    references=[
        RuleReference(
            text="Kubernetes documentation - Persistent Volumes",
            url="https://kubernetes.io/docs/concepts/storage/persistent-volumes/",
        ),
    ],
)


kubernetes_containers_using_raw_block_persistent_storage = Rule(
    id="kubernetes-containers-using-raw-block-persistent-storage",
    name="Containers Using Raw Block Persistent Storage",
    description=(
        "Identifies Kubernetes containers that use PersistentVolumeClaims as raw "
        "block devices. Confirm that direct device access is required and that the "
        "workload protects the device and its data appropriately."
    ),
    output_model=KubernetesContainerPersistentStorageFinding,
    facts=(_raw_block_persistent_storage,),
    tags=(
        "kubernetes",
        "data",
        "attack_surface",
        "stride:tampering",
        "stride:information_disclosure",
    ),
    version="0.1.0",
    references=[
        RuleReference(
            text="Kubernetes documentation - Raw Block Volume Support",
            url="https://kubernetes.io/docs/concepts/storage/persistent-volumes/#raw-block-volume-support",
        ),
    ],
)
