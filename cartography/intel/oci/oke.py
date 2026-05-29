# Copyright (c) 2020, Oracle and/or its affiliates.
# OCI Container Engine for Kubernetes (OKE) API-centric functions.
# https://docs.oracle.com/en-us/iaas/Content/ContEng/Concepts/contengoverview.htm
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
import oci

from . import utils
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def get_cluster_list_data(
    container_engine: oci.container_engine.ContainerEngineClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List OKE clusters in a compartment.
    See https://docs.oracle.com/en-us/iaas/api/#/en/containerengine/latest/Cluster/ListClusters
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            container_engine.list_clusters, compartment_id=compartment_id,
        )
        return {'Clusters': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve OKE clusters for compartment '%s': %s",
            compartment_id, e.message,
        )
        return {'Clusters': []}


def get_cluster_details(
    container_engine: oci.container_engine.ContainerEngineClient,
    cluster_id: str,
) -> Dict[str, Any]:
    """
    Fetch the full Cluster object including endpoint config, KMS key,
    image policy, admission controller options, and pod network options
    that the ListClusters summary does not return.
    """
    try:
        response = container_engine.get_cluster(cluster_id=cluster_id)
        rows = utils.oci_object_to_json(f"[{response.data}]")
        return rows[0] if rows else {}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve OKE cluster details for '%s': %s",
            cluster_id, e.message,
        )
        return {}


def get_node_pool_list_data(
    container_engine: oci.container_engine.ContainerEngineClient,
    compartment_id: str,
    cluster_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List node pools belonging to a single OKE cluster. Filtering server-side
    by ``cluster_id`` keeps each call narrow and avoids cross-cluster mixing
    when a compartment hosts multiple clusters.
    See https://docs.oracle.com/en-us/iaas/api/#/en/containerengine/latest/NodePool/ListNodePools
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            container_engine.list_node_pools,
            compartment_id=compartment_id,
            cluster_id=cluster_id,
        )
        return {'NodePools': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve OKE node pools for cluster '%s': %s",
            cluster_id, e.message,
        )
        return {'NodePools': []}


def get_node_pool_details(
    container_engine: oci.container_engine.ContainerEngineClient,
    node_pool_id: str,
) -> Dict[str, Any]:
    """
    Fetch the full NodePool object. Critically, this is the call that returns
    the ``nodes`` list — each entry's ``id`` is the OCID of the underlying
    compute instance and is what we use to create CONTAINS_NODE edges.
    """
    try:
        response = container_engine.get_node_pool(node_pool_id=node_pool_id)
        rows = utils.oci_object_to_json(f"[{response.data}]")
        return rows[0] if rows else {}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve OKE node pool details for '%s': %s",
            node_pool_id, e.message,
        )
        return {}


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def transform_clusters(
    cluster_summaries: List[Dict[str, Any]],
    cluster_details_by_id: Dict[str, Dict[str, Any]],
    region: str,
) -> List[Dict[str, Any]]:
    """
    Merge per-cluster detail payload onto each summary and shape the dicts to
    the keys our load_clusters Cypher expects. Surfaces every property our
    security posture checks care about: public endpoint exposure, etcd KMS
    key, image policy, pod-security-policy admission controller, CNI choice.
    """
    transformed: List[Dict[str, Any]] = []
    for summary in cluster_summaries:
        cluster_id = summary.get("id")
        if not cluster_id:
            continue
        details = cluster_details_by_id.get(cluster_id, {})
        merged = {**summary, **details}

        endpoint_config = merged.get("endpoint-config") or {}
        endpoints = merged.get("endpoints") or {}
        options = merged.get("options") or {}
        admission = options.get("admission-controller-options") or {}
        kube_net = options.get("kubernetes-network-config") or {}
        image_policy = merged.get("image-policy-config") or {}
        pod_network_options = merged.get("cluster-pod-network-options") or []
        cni_types = [p.get("cni-type") for p in pod_network_options if isinstance(p, dict)]

        transformed.append({
            "ocid": cluster_id,
            "name": merged.get("name"),
            "compartment_id": merged.get("compartment-id"),
            "kubernetes_version": merged.get("kubernetes-version"),
            "lifecycle_state": merged.get("lifecycle-state"),
            "lifecycle_details": merged.get("lifecycle-details"),
            "type": merged.get("type"),
            "vcn_id": merged.get("vcn-id"),
            # Etcd encryption (cluster-level KMS)
            "kms_key_id": merged.get("kms-key-id"),
            "is_encrypted_with_cmk": bool(merged.get("kms-key-id")),
            # Endpoint exposure (security-critical)
            "endpoint_subnet_id": endpoint_config.get("subnet-id"),
            "endpoint_is_public_ip_enabled": bool(endpoint_config.get("is-public-ip-enabled", False)),
            "endpoint_nsg_ids": endpoint_config.get("nsg-ids") or [],
            "kubernetes_endpoint": endpoints.get("kubernetes"),
            "public_endpoint": endpoints.get("public-endpoint"),
            "private_endpoint": endpoints.get("private-endpoint"),
            "is_public": bool(endpoints.get("public-endpoint")),
            # Networking config
            "pods_cidr": kube_net.get("pods-cidr"),
            "services_cidr": kube_net.get("services-cidr"),
            "service_lb_subnet_ids": options.get("service-lb-subnet-ids") or [],
            "cni_types": cni_types,
            # Admission / image policy
            "is_pod_security_policy_enabled": bool(admission.get("is-pod-security-policy-enabled", False)),
            "image_policy_enabled": bool(image_policy.get("is-policy-enabled", False)),
            "image_policy_kms_keys": [
                k.get("kms-key-id") for k in (image_policy.get("key-details") or [])
                if isinstance(k, dict) and k.get("kms-key-id")
            ],
            "available_kubernetes_upgrades": merged.get("available-kubernetes-upgrades") or [],
            "time_created": str(merged.get("metadata", {}).get("time-created", "")),
            "region": region,
        })
    return transformed


def transform_node_pools(
    node_pool_summaries: List[Dict[str, Any]],
    pool_details_by_id: Dict[str, Dict[str, Any]],
    region: str,
) -> List[Dict[str, Any]]:
    """
    Merge per-pool detail payloads onto each summary and shape them for load.
    Pulls SSH public key, shape config, boot volume KMS, in-transit encryption
    flag, NSG attachments, and the underlying compute instance OCIDs.
    """
    transformed: List[Dict[str, Any]] = []
    for summary in node_pool_summaries:
        pool_id = summary.get("id")
        if not pool_id:
            continue
        details = pool_details_by_id.get(pool_id, {})
        merged = {**summary, **details}

        shape_config = merged.get("node-shape-config") or {}
        node_source = merged.get("node-source-details") or merged.get("node-source") or {}
        node_config = merged.get("node-config-details") or {}
        eviction = merged.get("node-eviction-node-pool-settings") or {}
        nodes = merged.get("nodes") or []

        node_records: List[Dict[str, Any]] = []
        for n in nodes:
            if not isinstance(n, dict) or not n.get("id"):
                continue
            node_records.append({
                "ocid": n.get("id"),
                "name": n.get("name"),
                "availability_domain": n.get("availability-domain"),
                "subnet_id": n.get("subnet-id"),
                "lifecycle_state": n.get("lifecycle-state"),
                "kubernetes_version": n.get("kubernetes-version"),
                "private_ip": n.get("private-ip"),
                "public_ip": n.get("public-ip"),
                "fault_domain": n.get("fault-domain"),
            })

        transformed.append({
            "ocid": pool_id,
            "name": merged.get("name"),
            "compartment_id": merged.get("compartment-id"),
            "cluster_id": merged.get("cluster-id"),
            "kubernetes_version": merged.get("kubernetes-version"),
            "lifecycle_state": merged.get("lifecycle-state"),
            "node_shape": merged.get("node-shape"),
            "node_shape_ocpus": shape_config.get("ocpus"),
            "node_shape_memory_in_gbs": shape_config.get("memory-in-gbs"),
            "node_source_type": node_source.get("source-type"),
            "node_source_image_id": node_source.get("image-id"),
            "boot_volume_size_in_gbs": node_source.get("boot-volume-size-in-gbs"),
            "ssh_public_key": merged.get("ssh-public-key"),
            "has_ssh_key": bool(merged.get("ssh-public-key")),
            "quantity_per_subnet": merged.get("quantity-per-subnet"),
            "subnet_ids": merged.get("subnet-ids") or [],
            "size": node_config.get("size"),
            # Boot-volume encryption posture
            "kms_key_id": node_config.get("kms-key-id"),
            "is_encrypted_with_cmk": bool(node_config.get("kms-key-id")),
            "is_pv_encryption_in_transit_enabled": bool(
                node_config.get("is-pv-encryption-in-transit-enabled", False),
            ),
            "node_nsg_ids": node_config.get("nsg-ids") or [],
            "eviction_grace_duration": eviction.get("eviction-grace-duration"),
            "is_force_delete_after_grace_duration": bool(
                eviction.get("is-force-delete-after-grace-duration", False),
            ),
            "time_created": str(merged.get("metadata", {}).get("time-created", "")),
            "region": region,
            "nodes": node_records,
        })
    return transformed


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_clusters(
    neo4j_session: neo4j.Session,
    clusters: List[Dict[str, Any]],
    compartment_id: str,
    oci_update_tag: int,
) -> None:
    """
    Batch-ingest OCIOKECluster nodes and attach each to its owning OCICompartment
    via the standard RESOURCE relationship.
    """
    ingest_clusters = """
    UNWIND $clusters AS c
        MERGE (cl:OCIOKECluster{ocid: c.ocid})
        ON CREATE SET cl.firstseen = timestamp(),
                      cl.createdate = c.time_created
        SET cl.name = c.name,
            cl.compartment_id = c.compartment_id,
            cl.kubernetes_version = c.kubernetes_version,
            cl.lifecycle_state = c.lifecycle_state,
            cl.lifecycle_details = c.lifecycle_details,
            cl.type = c.type,
            cl.vcn_id = c.vcn_id,
            cl.kms_key_id = c.kms_key_id,
            cl.is_encrypted_with_cmk = c.is_encrypted_with_cmk,
            cl.endpoint_subnet_id = c.endpoint_subnet_id,
            cl.endpoint_is_public_ip_enabled = c.endpoint_is_public_ip_enabled,
            cl.endpoint_nsg_ids = c.endpoint_nsg_ids,
            cl.kubernetes_endpoint = c.kubernetes_endpoint,
            cl.public_endpoint = c.public_endpoint,
            cl.private_endpoint = c.private_endpoint,
            cl.is_public = c.is_public,
            cl.pods_cidr = c.pods_cidr,
            cl.services_cidr = c.services_cidr,
            cl.service_lb_subnet_ids = c.service_lb_subnet_ids,
            cl.cni_types = c.cni_types,
            cl.is_pod_security_policy_enabled = c.is_pod_security_policy_enabled,
            cl.image_policy_enabled = c.image_policy_enabled,
            cl.image_policy_kms_keys = c.image_policy_kms_keys,
            cl.available_kubernetes_upgrades = c.available_kubernetes_upgrades,
            cl.region = c.region,
            cl.lastupdated = $oci_update_tag
        WITH cl
        MATCH (cc:OCICompartment{ocid: $COMPARTMENT_ID})
        MERGE (cc)-[r:RESOURCE]->(cl)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $oci_update_tag
    """
    neo4j_session.run(
        ingest_clusters,
        clusters=clusters,
        COMPARTMENT_ID=compartment_id,
        oci_update_tag=oci_update_tag,
    )


def load_node_pools(
    neo4j_session: neo4j.Session,
    node_pools: List[Dict[str, Any]],
    compartment_id: str,
    oci_update_tag: int,
) -> None:
    """
    Batch-ingest OCIOKENodePool nodes, attach each to its owning OCICompartment
    via RESOURCE, and connect it to its parent OCIOKECluster via HAS_NODE_POOL.

    Then in a second batch, link each node pool to the underlying OCIInstance
    nodes via CONTAINS_NODE. Uses a MATCH (not MERGE) on OCIInstance so that
    pools containing instances we have not yet synced (e.g. compute hasn't
    run, or the instance is in a different compartment) silently no-op rather
    than creating empty placeholder nodes.
    """
    ingest_pools = """
    UNWIND $pools AS p
        MERGE (np:OCIOKENodePool{ocid: p.ocid})
        ON CREATE SET np.firstseen = timestamp(),
                      np.createdate = p.time_created
        SET np.name = p.name,
            np.compartment_id = p.compartment_id,
            np.cluster_id = p.cluster_id,
            np.kubernetes_version = p.kubernetes_version,
            np.lifecycle_state = p.lifecycle_state,
            np.node_shape = p.node_shape,
            np.node_shape_ocpus = p.node_shape_ocpus,
            np.node_shape_memory_in_gbs = p.node_shape_memory_in_gbs,
            np.node_source_type = p.node_source_type,
            np.node_source_image_id = p.node_source_image_id,
            np.boot_volume_size_in_gbs = p.boot_volume_size_in_gbs,
            np.ssh_public_key = p.ssh_public_key,
            np.has_ssh_key = p.has_ssh_key,
            np.quantity_per_subnet = p.quantity_per_subnet,
            np.subnet_ids = p.subnet_ids,
            np.size = p.size,
            np.kms_key_id = p.kms_key_id,
            np.is_encrypted_with_cmk = p.is_encrypted_with_cmk,
            np.is_pv_encryption_in_transit_enabled = p.is_pv_encryption_in_transit_enabled,
            np.node_nsg_ids = p.node_nsg_ids,
            np.eviction_grace_duration = p.eviction_grace_duration,
            np.is_force_delete_after_grace_duration = p.is_force_delete_after_grace_duration,
            np.region = p.region,
            np.lastupdated = $oci_update_tag
        WITH np, p
        MATCH (cc:OCICompartment{ocid: $COMPARTMENT_ID})
        MERGE (cc)-[r1:RESOURCE]->(np)
        ON CREATE SET r1.firstseen = timestamp()
        SET r1.lastupdated = $oci_update_tag
        WITH np, p
        MATCH (cl:OCIOKECluster{ocid: p.cluster_id})
        MERGE (cl)-[r2:HAS_NODE_POOL]->(np)
        ON CREATE SET r2.firstseen = timestamp()
        SET r2.lastupdated = $oci_update_tag
    """
    neo4j_session.run(
        ingest_pools,
        pools=node_pools,
        COMPARTMENT_ID=compartment_id,
        oci_update_tag=oci_update_tag,
    )

    # Build (pool_ocid, node_ocid) pairs for the compute bridge so we can do
    # one UNWIND-driven MATCH per pool/node pair.
    node_links: List[Dict[str, str]] = []
    for pool in node_pools:
        pool_ocid = pool.get("ocid")
        for node in pool.get("nodes") or []:
            node_ocid = node.get("ocid")
            if pool_ocid and node_ocid:
                node_links.append({"pool_ocid": pool_ocid, "node_ocid": node_ocid})

    if node_links:
        link_compute = """
        UNWIND $links AS link
            MATCH (np:OCIOKENodePool{ocid: link.pool_ocid})
            MATCH (i:OCIInstance{ocid: link.node_ocid})
            MERGE (np)-[r:CONTAINS_NODE]->(i)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $oci_update_tag
        """
        neo4j_session.run(link_compute, links=node_links, oci_update_tag=oci_update_tag)


# ---------------------------------------------------------------------------
# Sync orchestration
# ---------------------------------------------------------------------------

def sync_clusters(
    neo4j_session: neo4j.Session,
    container_engine: oci.container_engine.ContainerEngineClient,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> List[Dict[str, Any]]:
    """
    Fetch -> transform -> load OKE clusters for a compartment in a region.
    Returns the transformed cluster list so node-pool sync can iterate it
    without re-fetching summaries.
    """
    logger.debug(
        "Syncing OCI OKE clusters for compartment '%s', region '%s'.",
        compartment_id, region,
    )
    summaries = get_cluster_list_data(container_engine, compartment_id)["Clusters"]
    if not summaries:
        return []

    details_by_id: Dict[str, Dict[str, Any]] = {}
    for summary in summaries:
        cluster_id = summary.get("id")
        if not cluster_id:
            continue
        details = get_cluster_details(container_engine, cluster_id)
        if details:
            details_by_id[cluster_id] = details

    clusters = transform_clusters(summaries, details_by_id, region)
    if clusters:
        load_clusters(neo4j_session, clusters, compartment_id, oci_update_tag)
    return clusters


def sync_node_pools(
    neo4j_session: neo4j.Session,
    container_engine: oci.container_engine.ContainerEngineClient,
    clusters: List[Dict[str, Any]],
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    For each cluster fetched in this region, list its node pools, fetch each
    pool's full detail payload (which carries the ``nodes`` list), then
    batch-load the pools and their compute-instance bridges in a single pass.
    """
    if not clusters:
        return

    all_summaries: List[Dict[str, Any]] = []
    pool_details_by_id: Dict[str, Dict[str, Any]] = {}

    for cluster in clusters:
        cluster_id = cluster.get("ocid")
        if not cluster_id:
            continue
        summaries = get_node_pool_list_data(
            container_engine, compartment_id, cluster_id,
        )["NodePools"]
        for summary in summaries:
            pool_id = summary.get("id")
            if not pool_id:
                continue
            all_summaries.append(summary)
            details = get_node_pool_details(container_engine, pool_id)
            if details:
                pool_details_by_id[pool_id] = details

    if not all_summaries:
        return

    node_pools = transform_node_pools(all_summaries, pool_details_by_id, region)
    if node_pools:
        load_node_pools(neo4j_session, node_pools, compartment_id, oci_update_tag)


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    run_cleanup_job(
        'oci_import_oke_cleanup.json', neo4j_session, common_job_parameters,
    )


def sync(
    neo4j_session: neo4j.Session,
    container_engine: oci.container_engine.ContainerEngineClient,
    tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
    regions: Optional[List[str]] = None,
) -> None:
    """
    Sync OCI OKE resources for the compartment specified in
    ``common_job_parameters["OCI_COMPARTMENT_ID"]``. Mirrors the per-region
    iteration pattern used by compute.sync and storage.sync.
    """
    compartment_id = common_job_parameters.get("OCI_COMPARTMENT_ID", tenancy_id)
    logger.info("Syncing OCI OKE for compartment '%s'.", compartment_id)

    if not regions:
        regions = [container_engine.base_client.region or ""]

    for region in regions:
        logger.info(
            "Syncing OCI OKE in region '%s' for compartment '%s'.",
            region, compartment_id,
        )
        if region:
            container_engine.base_client.set_region(region)

        try:
            clusters = sync_clusters(
                neo4j_session, container_engine, compartment_id, region, oci_update_tag,
            )
        except Exception as e:
            logger.error("Error syncing OCI OKE clusters: %s", e, exc_info=True)
            clusters = []

        try:
            sync_node_pools(
                neo4j_session, container_engine, clusters,
                compartment_id, region, oci_update_tag,
            )
        except Exception as e:
            logger.error("Error syncing OCI OKE node pools: %s", e, exc_info=True)

    cleanup(neo4j_session, common_job_parameters)
