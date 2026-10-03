"""Join independently collected GKE, IAM, Compute, and Kubernetes inventory.

These are configuration/evidence relationships, not an effective-permissions solver.
No cloud calls are made per pod, service account, or IAM binding.
"""

import ipaddress
from collections import defaultdict
from typing import Any

import neo4j

from cartography.client.core.tx import load_matchlinks
from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.intel.gcp.gke_utils import parse_cluster_ref
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.kubernetes.gke import GKEClusterMatchLink
from cartography.models.kubernetes.gke import GKEGatewayLoadBalancerMatchLink
from cartography.models.kubernetes.gke import GKEIngressLoadBalancerMatchLink
from cartography.models.kubernetes.gke import GKENodePoolMatchLink
from cartography.models.kubernetes.gke import GKEPoolMatchLink
from cartography.models.kubernetes.gke import GKEServiceLoadBalancerMatchLink
from cartography.models.kubernetes.gke import GKEUserMatchLink
from cartography.models.kubernetes.gke import GKEWorkloadImpersonationMatchLink
from cartography.models.kubernetes.gke import GKEWorkloadPolicyMatchLink


def principal_members(sa: dict[str, Any], pool: str, cluster_resource: str) -> set[str]:
    """Enumerate documented GKE member forms; no substring or pool-only matching."""
    pool_id = pool.rsplit("/", 1)[-1]
    principal = f"principal://iam.googleapis.com/{pool}"
    principal_set = f"principalSet://iam.googleapis.com/{pool}"
    namespace, name = sa["namespace"], sa["name"]
    members = {
        f"{principal}/subject/ns/{namespace}/sa/{name}",
        f"{principal_set}/namespace/{namespace}",
        f"{principal_set}/kubernetes.cluster/https://container.googleapis.com/v1/{cluster_resource}",
        f"{principal_set}/*",
        f"serviceAccount:{pool_id}[{namespace}/{name}]",
    }
    if sa.get("uid"):
        members.add(f"{principal}/kubernetes.serviceaccount.uid/{sa['uid']}")
    return members


def match_workload_policies(
    service_accounts: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
    pool: str,
    cluster_resource: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Index exact selectors once, avoiding a KSA x all-project-bindings scan."""
    by_member: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for binding in bindings:
        for member in binding.get("raw_members") or []:
            by_member[member].append(binding)
    grants, impersonations = [], []
    for sa in service_accounts:
        matched: dict[str, tuple[dict[str, Any], set[str]]] = {}
        for member in principal_members(sa, pool, cluster_resource):
            for binding in by_member.get(member, []):
                matched.setdefault(binding["id"], (binding, set()))[1].add(member)
        for binding, members in matched.values():
            row = {
                "source_id": sa["id"],
                "target_id": binding["id"],
                "matched_members": sorted(members),
                "policy_lastupdated": binding.get("lastupdated"),
            }
            grants.append(row)
            # Use the observed APPLIES_TO GSA email, not a guessed resource-name suffix.
            email = sa.get("gcp_service_account")
            if (
                email
                and email in (binding.get("service_account_emails") or [])
                and binding.get("role") == "roles/iam.workloadIdentityUser"
                and binding.get("has_condition") is False
            ):
                impersonations.append({**row, "target_id": email})
    return grants, impersonations


def _network_path(value: str | None) -> str | None:
    if not value:
        return None
    return value.removeprefix("https://www.googleapis.com/compute/v1/").removeprefix(
        "https://compute.googleapis.com/compute/v1/"
    )


def _listener_matches(resource: dict[str, Any], rule: dict[str, Any]) -> bool:
    listeners = resource.get("load_balancer_listeners")
    if not listeners:
        return True
    for listener in listeners:
        protocol, port = listener.split(":", 1)
        if rule.get("ip_protocol") and rule["ip_protocol"] not in (
            protocol,
            "L3_DEFAULT",
        ):
            continue
        if rule.get("ports"):
            if port in rule["ports"]:
                return True
        elif rule.get("port_range"):
            bounds = rule["port_range"].split("-")
            try:
                if int(bounds[0]) <= int(port) <= int(bounds[-1]):
                    return True
            except ValueError:
                continue
        else:
            # Compute allPorts forwarding rules omit both ports and portRange.
            return True
    return False


def match_load_balancers(
    resources: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    project: str,
    network: str | None,
) -> list[dict[str, str]]:
    by_address: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rule in rules:
        if rule.get("project_id") != project:
            continue
        if rule.get("lb_type") == "vpn":
            continue
        scheme = rule.get("load_balancing_scheme") or ""
        # Unknown forwarding rule types (e.g. VPN) must not become load balancers.
        if scheme not in {
            "EXTERNAL",
            "EXTERNAL_MANAGED",
            "INTERNAL",
            "INTERNAL_MANAGED",
            "INTERNAL_SELF_MANAGED",
        }:
            continue
        if scheme.startswith("INTERNAL") and (
            not network or _network_path(rule.get("network")) != _network_path(network)
        ):
            continue
        try:
            address = str(ipaddress.ip_address(rule.get("ip_address", "")))
        except ValueError:
            continue
        by_address[address].append(rule)
    matches: set[tuple[str, str]] = set()
    for resource in resources:
        for address in resource.get("load_balancer_ips") or []:
            try:
                canonical = str(ipaddress.ip_address(address))
            except ValueError:
                continue
            matches.update(
                (resource["id"], rule["id"])
                for rule in by_address.get(canonical, [])
                if _listener_matches(resource, rule)
            )
    return [
        {"source_id": source, "target_id": target} for source, target in sorted(matches)
    ]


def _load_links(
    session: neo4j.Session,
    schema: CartographyRelSchema,
    rows: list[dict[str, Any]],
    scope: str,
    scope_id: str,
    tag: int,
) -> None:
    load_matchlinks(
        session,
        schema,
        rows,
        lastupdated=tag,
        _sub_resource_label=scope,
        _sub_resource_id=scope_id,
    )
    GraphJob.from_matchlink(schema, scope, scope_id, tag).run(session)


def sync(
    session: neo4j.Session,
    cluster: dict[str, Any],
    cluster_id: str,
    update_tag: int,
    gateway_complete: bool = True,
) -> None:
    ref = parse_cluster_ref(cluster["resource_name"])
    cloud = session.run(
        "MATCH (g:GKECluster {resource_name: $name}) RETURN g.id AS id, g.network_uri AS network",
        name=ref.resource_name,
    ).single()
    if cloud:
        _load_links(
            session,
            GKEClusterMatchLink(),
            [{"source_id": cloud["id"], "target_id": cluster_id}],
            "GKECluster",
            cloud["id"],
            update_tag,
        )
        # One cloud resource has one current kube-system UID, including recreation within a sync tag.
        run_write_query(
            session,
            "MATCH (g:GKECluster {id: $cloud_id})-[r:MAPS_TO]->(k:KubernetesCluster) WHERE k.id <> $cluster_id DELETE r",
            cloud_id=cloud["id"],
            cluster_id=cluster_id,
        )
    scope = "KubernetesCluster"
    nodes = session.run(
        "MATCH (:KubernetesCluster {id: $id})-[:RESOURCE]->(n:KubernetesNode) WHERE n.lastupdated = $tag RETURN n.id AS source_id, n.gke_node_pool AS pool",
        id=cluster_id,
        tag=update_tag,
    ).data()
    _load_links(
        session,
        GKENodePoolMatchLink(),
        [
            {
                "source_id": n["source_id"],
                "target_id": f"{ref.resource_name}/nodePools/{n['pool']}",
            }
            for n in nodes
            if n["pool"]
        ],
        scope,
        cluster_id,
        update_tag,
    )
    pool_name = (cluster.get("workloadIdentityConfig") or {}).get("workloadPool")
    pool = (
        session.run(
            "MATCH (p:GCPWorkloadIdentityPool {project_id: $project, pool_id: $pool}) RETURN p.id AS id",
            project=ref.project,
            pool=pool_name,
        ).single()
        if pool_name
        else None
    )
    if cloud:
        _load_links(
            session,
            GKEPoolMatchLink(),
            [{"source_id": cloud["id"], "target_id": pool["id"]}] if pool else [],
            "GKECluster",
            cloud["id"],
            update_tag,
        )
    # Missing cloud inventory is unknown, not an empty IAM policy snapshot.
    if pool:
        accounts = session.run(
            "MATCH (:KubernetesCluster {id: $id})-[:RESOURCE]->(s:KubernetesServiceAccount) WHERE s.lastupdated = $tag RETURN properties(s) AS sa",
            id=cluster_id,
            tag=update_tag,
        )
        sas = [r["sa"] for r in accounts]
        bindings = session.run(
            "MATCH (b:GCPPolicyBinding) WHERE $pool IN b.wif_pools OR any(m IN b.raw_members WHERE m STARTS WITH $legacy) OPTIONAL MATCH (b)-[:APPLIES_TO]->(g:GCPServiceAccount) RETURN properties(b) AS binding, collect(g.email) AS emails",
            pool=pool["id"],
            legacy=f"serviceAccount:{pool_name}[",
        )
        policies = [
            {**r["binding"], "service_account_emails": r["emails"]} for r in bindings
        ]
        grants, impersonations = match_workload_policies(
            sas, policies, pool["id"], ref.resource_name
        )
        _load_links(
            session, GKEWorkloadPolicyMatchLink(), grants, scope, cluster_id, update_tag
        )
        _load_links(
            session,
            GKEWorkloadImpersonationMatchLink(),
            impersonations,
            scope,
            cluster_id,
            update_tag,
        )
        # DEPRECATED: remove pre-v1.0.0 annotation-only edges after valid edges have been merged.
        run_write_query(
            session,
            "MATCH (:KubernetesCluster {id: $id})-[:RESOURCE]->(:KubernetesServiceAccount)-[r:WORKLOAD_IDENTITY_BINDING]->(:GCPServiceAccount) WHERE r._sub_resource_id IS NULL DELETE r",
            id=cluster_id,
        )
    elif not pool_name:
        _load_links(
            session, GKEWorkloadPolicyMatchLink(), [], scope, cluster_id, update_tag
        )
        _load_links(
            session,
            GKEWorkloadImpersonationMatchLink(),
            [],
            scope,
            cluster_id,
            update_tag,
        )
    users = session.run(
        "MATCH (:KubernetesCluster {id: $id})-[:RESOURCE]->(u:KubernetesUser) WHERE u.lastupdated = $tag RETURN u.name AS source_id, u.id AS target_id",
        id=cluster_id,
        tag=update_tag,
    ).data()
    _load_links(session, GKEUserMatchLink(), users, scope, cluster_id, update_tag)
    # Shared VPC network lives in the host project; forwarding rules remain scoped to the service project.
    network = (cluster.get("networkConfig") or {}).get("network") or (
        cloud["network"] if cloud else None
    )
    rules = [
        r["rule"]
        for r in session.run(
            "MATCH (r:GCPForwardingRule {project_id: $project}) RETURN properties(r) AS rule",
            project=ref.project,
        )
    ]
    schemas = [GKEServiceLoadBalancerMatchLink(), GKEIngressLoadBalancerMatchLink()]
    if gateway_complete:
        schemas.append(GKEGatewayLoadBalancerMatchLink())
    for schema in schemas:
        # Labels come exclusively from the static schemas above.
        resources = [
            r["resource"]
            for r in session.run(
                f"MATCH (:KubernetesCluster {{id: $id}})-[:RESOURCE]->(s:{schema.source_node_label}) WHERE s.lastupdated = $tag RETURN properties(s) AS resource",
                id=cluster_id,
                tag=update_tag,
            )
        ]
        _load_links(
            session,
            schema,
            match_load_balancers(resources, rules, ref.project, network),
            scope,
            cluster_id,
            update_tag,
        )
