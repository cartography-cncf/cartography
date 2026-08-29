# Google Compute Engine API-centric functions
# https://cloud.google.com/compute/docs/concepts
from __future__ import annotations

import logging
from collections import namedtuple
from typing import Any

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.intel.gcp.backendservice import sync_gcp_backend_services
from cartography.intel.gcp.cloud_armor import sync_gcp_cloud_armor
from cartography.intel.gcp.instancegroup import sync_gcp_instance_groups
from cartography.intel.gcp.labels import sync_labels
from cartography.intel.gcp.ssl_policy import sync_gcp_ssl_policies
from cartography.intel.gcp.target_https_proxy import sync_gcp_target_https_proxies
from cartography.intel.gcp.target_ssl_proxy import sync_gcp_target_ssl_proxies
from cartography.intel.gcp.util import classify_gcp_http_error
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import is_permission_denied_error
from cartography.intel.gcp.util import parse_compute_full_uri_to_partial_uri
from cartography.intel.gcp.util import summarize_gcp_http_error
from cartography.models.gcp.compute.firewall import GCPFirewallSchema
from cartography.models.gcp.compute.firewall_target_tag import (
    GCPFirewallTargetTagSchema,
)
from cartography.models.gcp.compute.forwarding_rule import GCPForwardingRuleSchema
from cartography.models.gcp.compute.forwarding_rule import (
    GCPForwardingRuleWithSubnetSchema,
)
from cartography.models.gcp.compute.forwarding_rule import (
    GCPForwardingRuleWithVpcSchema,
)
from cartography.models.gcp.compute.instance import GCPInstanceSchema
from cartography.models.gcp.compute.ip_range import IpRangeSchema
from cartography.models.gcp.compute.ip_rule import GCPIpRuleAllowedSchema
from cartography.models.gcp.compute.ip_rule import GCPIpRuleDeniedSchema
from cartography.models.gcp.compute.network_interface import GCPNetworkInterfaceSchema
from cartography.models.gcp.compute.network_tag import GCPNetworkTagSchema
from cartography.models.gcp.compute.nic_access_config import GCPNicAccessConfigSchema
from cartography.models.gcp.compute.project import GCPProjectComputeMetadataSchema
from cartography.models.gcp.compute.subnet import GCPSubnetSchema
from cartography.models.gcp.compute.subnet_stub import GCPSubnetStubSchema
from cartography.models.gcp.compute.vpc import GCPVpcSchema
from cartography.models.gcp.compute.vpc_peering import GCPVpcPeeringSchema
from cartography.models.gcp.compute.vpc_stub import GCPVpcStubSchema
from cartography.models.gcp.compute.vpn_gateway import GCPVpnGatewaySchema
from cartography.models.gcp.compute.vpn_gateway_stub import GCPVpnGatewayStubSchema
from cartography.models.gcp.compute.vpn_tunnel import GCPVpnTunnelSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
InstanceUriPrefix = namedtuple("InstanceUriPrefix", "zone_name project_id")


@timeit
def get_zones_in_project(
    project_id: str,
    compute: Resource,
    max_results: int | None = None,
) -> list[dict] | None:
    """
    Return the zones where the Compute Engine API is enabled for the given project_id.
    See https://cloud.google.com/compute/docs/reference/rest/v1/zones and
    https://cloud.google.com/compute/docs/reference/rest/v1/zones/list.
    If the API is not enabled or if the project returns a 404-not-found, return None.
    :param project_id: The project ID number to sync.  See  the `projectId` field in
    https://cloud.google.com/resource-manager/reference/rest/v1/projects
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :param max_results: Optional cap on number of results returned by this function. Default = None, which means no cap.
    :return: List of a project's zone objects if Compute API is turned on, else None.
    """
    try:
        req = compute.zones().list(project=project_id, maxResults=max_results)
        res = gcp_api_execute_with_retry(req)
        return res["items"]
    except HttpError as e:
        category = classify_gcp_http_error(e)
        if category == "api_disabled":
            logger.info(
                "Google Compute Engine API access is not configured for project %s; skipping. %s",
                project_id,
                summarize_gcp_http_error(e),
            )
            return None
        elif category == "not_found":
            logger.info(
                "Project %s returned a 404 not found error. %s",
                project_id,
                summarize_gcp_http_error(e),
            )
            return None
        elif is_permission_denied_error(e):
            logger.info(
                (
                    "Your GCP identity does not have the compute.zones.list permission for project %s; "
                    "skipping compute sync for this project. %s"
                ),
                project_id,
                summarize_gcp_http_error(e),
            )
            return None
        else:
            raise


@timeit
def get_gcp_instance_responses(
    project_id: str,
    zones: list[dict] | None,
    compute: Resource,
) -> list[Resource]:
    """
    Return list of GCP instance response objects for a given project and list of zones
    :param project_id: The project ID
    :param zones: The list of zones to query for instances
    :param compute: The compute resource object
    :return: A list of response objects of the form {id: str, items: []} where each item in `items` is a GCP instance
    """
    if not zones:
        # If the Compute Engine API is not enabled for a project, there are no zones and therefore no instances.
        return []
    response_objects: list[Resource] = []
    for zone in zones:
        req = compute.instances().list(project=project_id, zone=zone["name"])
        try:
            res = gcp_api_execute_with_retry(req)
            response_objects.append(res)
        except HttpError as e:
            # Intentional widening vs. the old check (reason in {"backendError",
            # "rateLimitExceeded", "internalError"}): classify_gcp_http_error covers
            # 429, generic 500/502/504, and 403-quota responses in addition to the
            # original three reasons. After gcp_api_execute_with_retry has already
            # retried all of these, skipping the zone is the right fallback.
            if classify_gcp_http_error(e) == "transient":
                logger.warning(
                    "Transient error listing instances for project %s zone %s: %s; skipping this zone.",
                    project_id,
                    zone.get("name"),
                    summarize_gcp_http_error(e),
                )
                continue
            raise
    return response_objects


@timeit
def get_gcp_subnets(projectid: str, region: str, compute: Resource) -> dict | None:
    """
    Return list of all subnets in the given projectid and region. Returns None
    if the region is invalid or if the API call times out (to prevent partial
    data from triggering cleanup that would delete valid nodes).
    :param projectid: The project ID
    :param region: The region to pull subnets from
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Response object containing data on all GCP subnets for a given project,
        or None if region is invalid or the request times out
    """
    try:
        req = compute.subnetworks().list(project=projectid, region=region)
    except HttpError as e:
        if classify_gcp_http_error(e) == "invalid":
            logger.warning(
                "GCP: Invalid region %s for project %s; skipping subnet sync for this region.",
                region,
                projectid,
            )
            return None
        raise

    items: list[dict] = []
    response_id = f"projects/{projectid}/regions/{region}/subnetworks"
    while req is not None:
        try:
            res = gcp_api_execute_with_retry(req)
        except TimeoutError:
            logger.warning(
                "GCP: subnetworks.list for project %s region %s timed out; skipping this region to preserve existing data.",
                projectid,
                region,
            )
            return None
        except HttpError as e:
            if classify_gcp_http_error(e) == "invalid":
                logger.warning(
                    "GCP: Invalid region %s for project %s; skipping subnet sync for this region.",
                    region,
                    projectid,
                )
                return None
            raise
        items.extend(res.get("items", []))
        response_id = res.get("id", response_id)
        req = compute.subnetworks().list_next(
            previous_request=req, previous_response=res
        )
    return {"id": response_id, "items": items}


@timeit
def get_gcp_vpcs(projectid: str, compute: Resource) -> Resource:
    """
    Get VPC data for given project
    :param projectid: The project ID
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: VPC response object
    """
    req = compute.networks().list(project=projectid)
    return gcp_api_execute_with_retry(req)


def _is_skippable_vpn_list_error(e: HttpError) -> bool:
    """
    Return True if a vpnGateways/vpnTunnels list HttpError is an expected
    access or configuration failure (invalid region, missing list permission,
    API not enabled, billing disabled, or project not found) for which the
    region should be skipped rather than aborting the whole project sync.
    """
    return classify_gcp_http_error(e) in (
        "invalid",
        "forbidden",
        "api_disabled",
        "billing_disabled",
        "not_found",
    )


@timeit
def get_gcp_vpn_gateways(projectid: str, compute: Resource) -> tuple[list[dict], bool]:
    """
    Return all HA VPN gateways in the given projectid across all regions using
    the vpnGateways.aggregatedList endpoint (one request chain instead of one
    per region) with partial success enabled.
    :param projectid: The project ID
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Tuple of (gateway items, incomplete). incomplete is True if the
        request chain failed partway or any region scope returned an error, in
        which case cleanup must be suppressed for the project.
    """
    return _get_gcp_vpn_aggregated(projectid, compute, "vpnGateways")


@timeit
def get_gcp_vpn_tunnels(projectid: str, compute: Resource) -> tuple[list[dict], bool]:
    """
    Return all VPN tunnels in the given projectid across all regions using the
    vpnTunnels.aggregatedList endpoint (one request chain instead of one per
    region) with partial success enabled.
    :param projectid: The project ID
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Tuple of (tunnel items, incomplete). incomplete is True if the
        request chain failed partway or any region scope returned an error, in
        which case cleanup must be suppressed for the project.
    """
    return _get_gcp_vpn_aggregated(projectid, compute, "vpnTunnels")


def _get_gcp_vpn_aggregated(
    projectid: str,
    compute: Resource,
    resource: str,
) -> tuple[list[dict], bool]:
    """
    Fetch all VPN resources of the given type ("vpnGateways" or "vpnTunnels")
    for a project via the Compute aggregatedList endpoint with
    returnPartialSuccess=True: a single paginated request chain covers all
    regions, and a region that fails (e.g. transient location error) reports a
    per-scope `error` entry in the response instead of failing the whole call.

    Expected access/configuration failures of the whole call (missing list
    permission, API not enabled, billing disabled, project not found) return
    ([], True) so that other Compute resources still sync and cleanup is
    safely suppressed for the project.

    :param projectid: The project ID
    :param compute: The compute resource object
    :param resource: "vpnGateways" or "vpnTunnels"
    :return: Tuple of (items across all regions, incomplete)
    """
    api = getattr(compute, resource)()
    try:
        req = api.aggregatedList(project=projectid, returnPartialSuccess=True)
    except HttpError as e:
        if _is_skippable_vpn_list_error(e):
            logger.warning(
                "GCP: %s.aggregatedList failed for project %s; skipping this resource type for the project. %s",
                resource,
                projectid,
                summarize_gcp_http_error(e),
            )
            return [], True
        raise

    items: list[dict] = []
    incomplete = False
    while req is not None:
        try:
            res = gcp_api_execute_with_retry(req)
        except TimeoutError:
            logger.warning(
                "GCP: %s.aggregatedList for project %s timed out; keeping partial data and suppressing cleanup.",
                resource,
                projectid,
            )
            incomplete = True
            break
        except HttpError as e:
            if _is_skippable_vpn_list_error(e):
                logger.warning(
                    "GCP: %s.aggregatedList failed for project %s; keeping partial data and suppressing cleanup. %s",
                    resource,
                    projectid,
                    summarize_gcp_http_error(e),
                )
                incomplete = True
                break
            raise
        # Aggregated responses key items by scope ("regions/{region}"). A scope
        # is incomplete if it carries an `error` entry, or a `warning` with any
        # code other than the benign NO_RESULTS_ON_PAGE (e.g. UNREACHABLE means
        # the region could not be queried, so its data is missing).
        for scope, scope_data in res.get("items", {}).items():
            warning_code = (scope_data.get("warning") or {}).get("code")
            if scope_data.get("error") or (
                warning_code and warning_code != "NO_RESULTS_ON_PAGE"
            ):
                incomplete = True
                logger.warning(
                    "GCP: %s.aggregatedList for project %s reported a problem for scope %s (warning: %s); suppressing cleanup for the project.",
                    resource,
                    projectid,
                    scope,
                    warning_code or scope_data.get("error"),
                )
            items.extend(scope_data.get(resource, []))
        # Missing data can also be reported at the page level, outside items:
        # a non-empty `unreachables` list, or a top-level `warning` whose code
        # is not the benign NO_RESULTS_ON_PAGE (e.g. UNREACHABLE).
        if res.get("unreachables"):
            incomplete = True
            logger.warning(
                "GCP: %s.aggregatedList for project %s reported unreachable scopes %s; suppressing cleanup for the project.",
                resource,
                projectid,
                res["unreachables"],
            )
        page_warning_code = (res.get("warning") or {}).get("code")
        if page_warning_code and page_warning_code != "NO_RESULTS_ON_PAGE":
            incomplete = True
            logger.warning(
                "GCP: %s.aggregatedList for project %s returned warning %s; suppressing cleanup for the project.",
                resource,
                projectid,
                page_warning_code,
            )
        req = api.aggregatedList_next(previous_request=req, previous_response=res)
    return items, incomplete


@timeit
def get_gcp_compute_project_metadata(project_id: str, compute: Resource) -> dict:
    """
    Return project-level Compute metadata relevant to CIS checks.
    """
    req = compute.projects().get(project=project_id)
    return gcp_api_execute_with_retry(req)


@timeit
def get_gcp_regional_forwarding_rules(
    project_id: str,
    region: str,
    compute: Resource,
) -> Resource | None:
    """
    Return list of all regional forwarding rules in the given project_id and region.
    Returns None if the region is invalid.
    :param project_id: The project ID
    :param region: The region to pull forwarding rules from
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Response object containing data on all GCP forwarding rules for a given project, or None if region is invalid
    """
    req = compute.forwardingRules().list(project=project_id, region=region)
    try:
        return gcp_api_execute_with_retry(req)
    except HttpError as e:
        if classify_gcp_http_error(e) == "invalid":
            logger.warning(
                "GCP: Invalid region %s for project %s; skipping forwarding rules sync for this region.",
                region,
                project_id,
            )
            return None
        raise


@timeit
def get_gcp_global_forwarding_rules(project_id: str, compute: Resource) -> Resource:
    """
    Return list of all global forwarding rules in the given project_id and region
    :param project_id: The project ID
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Response object containing data on all GCP forwarding rules for a given project
    """
    req = compute.globalForwardingRules().list(project=project_id)
    return gcp_api_execute_with_retry(req)


@timeit
def get_gcp_firewall_ingress_rules(project_id: str, compute: Resource) -> Resource:
    """
    Get ingress Firewall data for a given project
    :param project_id: The project ID to get firewalls for
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Firewall response object
    """
    req = compute.firewalls().list(project=project_id, filter='(direction="INGRESS")')
    return gcp_api_execute_with_retry(req)


@timeit
def transform_gcp_instances(response_objects: list[dict]) -> list[dict]:
    """
    Process the GCP instance response objects and return a flattened list of GCP instances with all the necessary fields
    we need to load it into Neo4j
    :param response_objects: The return data from get_gcp_instance_responses()
    :return: A list of GCP instances
    """
    instance_list = []
    for res in response_objects:
        prefix = res["id"]
        prefix_fields = _parse_instance_uri_prefix(prefix)

        for instance in res.get("items", []):
            instance["partial_uri"] = f"{prefix}/{instance['name']}"
            instance["project_id"] = prefix_fields.project_id
            instance["zone_name"] = prefix_fields.zone_name
            machine_type = instance.get("machineType")
            instance["machine_type"] = (
                machine_type.split("/")[-1] if machine_type else None
            )
            service_accounts = instance.get("serviceAccounts", [])
            primary_service_account = service_accounts[0] if service_accounts else {}
            instance["service_account_email"] = primary_service_account.get("email")
            instance["service_account_scopes"] = primary_service_account.get(
                "scopes", []
            )
            instance["can_ip_forward"] = instance.get("canIpForward")
            shielded_config = instance.get("shieldedInstanceConfig", {})
            instance["enable_vtpm"] = shielded_config.get("enableVtpm")
            instance["enable_integrity_monitoring"] = shielded_config.get(
                "enableIntegrityMonitoring"
            )
            confidential_config = instance.get("confidentialInstanceConfig", {})
            instance["enable_confidential_compute"] = confidential_config.get(
                "enableConfidentialCompute"
            )
            metadata_items = {
                item.get("key"): item.get("value")
                for item in instance.get("metadata", {}).get("items", [])
                if item.get("key")
            }
            instance["block_project_ssh_keys"] = metadata_items.get(
                "block-project-ssh-keys"
            )
            instance["enable_oslogin_metadata"] = metadata_items.get("enable-oslogin")
            instance["serial_port_enable"] = metadata_items.get("serial-port-enable")
            instance["creation_timestamp"] = instance.get("creationTimestamp")

            # Project primary IPs onto the instance for the ComputeInstance ontology.
            # The full set of NIC / access-config IPs stays modelled on
            # GCPNetworkInterface / GCPNicAccessConfig; these fields just expose the
            # first pair for cross-cloud semantic queries.
            network_interfaces = instance.get("networkInterfaces", []) or []
            primary_nic = network_interfaces[0] if network_interfaces else {}
            instance["private_ip"] = primary_nic.get("networkIP")
            primary_access_configs = primary_nic.get("accessConfigs", []) or []
            instance["public_ip"] = (
                primary_access_configs[0].get("natIP")
                if primary_access_configs
                else None
            )

            for nic in network_interfaces:
                nic["subnet_partial_uri"] = _parse_compute_full_uri_to_partial_uri(
                    nic["subnetwork"],
                )
                nic["vpc_partial_uri"] = _parse_compute_full_uri_to_partial_uri(
                    nic["network"],
                )

            instance_list.append(instance)
    return instance_list


def _parse_instance_uri_prefix(prefix: str) -> InstanceUriPrefix:
    """
    Helper function to parse a GCP prefix string of the form `projects/{project}/zones/{zone}/instances`
    :param prefix: String of the form `projects/{project}/zones/{zone}/instances`
    :return: namedtuple with fields project_id and zone_name
    """
    split_list = prefix.split("/")

    return InstanceUriPrefix(
        project_id=split_list[1],
        zone_name=split_list[3],
    )


def _parse_compute_full_uri_to_partial_uri(full_uri: str, version: str = "v1") -> str:
    """
    Take a GCP Compute object's self_link of the form
    `https://www.googleapis.com/compute/{version}/projects/{project}/{location specifier}/{subtype}/{resource name}`
    and converts it to its partial URI `{project}/{location specifier}/{subtype}/{resource name}`.
    This is designed for GCP compute_objects that have compute/{version specifier}/ in their `self_link`s.
    :param network_full_uri: The full URI
    :param version: The version number; default to v1 since at the time of this writing v1 is the only Compute API.
    :return: Partial URI `{project}/{location specifier}/{subtype}/{resource name}`
    """
    parsed = parse_compute_full_uri_to_partial_uri(full_uri, version=version)
    return parsed if parsed is not None else full_uri


def _create_gcp_network_tag_id(vpc_partial_uri: str, tag: str) -> str:
    """
    Generate an ID for a GCP network tag
    :param vpc_partial_uri: The VPC that this tag applies to
    :return: An ID for the GCP network tag
    """
    return f"{vpc_partial_uri}/tags/{tag}"


@timeit
def transform_gcp_vpcs(vpc_res: dict) -> list[dict]:
    """
    Transform the VPC response object for Neo4j ingestion
    :param vpc_res: The return data
    :return: List of VPCs ready for ingestion to Neo4j
    """
    vpc_list = []

    # prefix has the form `projects/{project ID}/global/networks`
    prefix = vpc_res["id"]
    projectid = prefix.split("/")[1]
    for v in vpc_res.get("items", []):
        vpc = {}
        partial_uri = f"{prefix}/{v['name']}"

        vpc["partial_uri"] = partial_uri
        vpc["name"] = v["name"]
        vpc["self_link"] = v["selfLink"]
        vpc["project_id"] = projectid
        vpc["auto_create_subnetworks"] = v.get("autoCreateSubnetworks", None)
        vpc["description"] = v.get("description", None)
        vpc["routing_config_routing_mode"] = v.get("routingConfig", {}).get(
            "routingMode",
            None,
        )

        vpc_list.append(vpc)
    return vpc_list


@timeit
def transform_gcp_vpc_peerings(vpc_res: dict) -> list[dict]:
    """
    Extract VPC Network Peering connections from the networks.list response and
    transform them for Neo4j ingestion. Peerings are embedded in each network's
    `peerings` field, so no extra API call is needed. Each side of a peering is
    reported by its own project's networks.list response, so this yields one
    peering object per (local network, peering name) pair.
    :param vpc_res: The return data from get_gcp_vpcs()
    :return: List of VPC peerings ready for ingestion to Neo4j
    """
    # prefix has the form `projects/{project ID}/global/networks`
    prefix = vpc_res["id"]
    peering_list = []
    for v in vpc_res.get("items", []):
        network_partial_uri = f"{prefix}/{v['name']}"
        for p in v.get("peerings", []):
            peering: dict[str, Any] = {
                # The API exposes no resource URI for peerings, so construct a
                # stable ID from the local network and the peering name.
                "id": f"{network_partial_uri}/networkPeerings/{p['name']}",
                "name": p["name"],
                "network_partial_uri": network_partial_uri,
                "state": p.get("state"),
                "state_details": p.get("stateDetails"),
                "peer_mtu": p.get("peerMtu"),
                "stack_type": p.get("stackType"),
                "update_strategy": p.get("updateStrategy"),
                "auto_create_routes": p.get("autoCreateRoutes"),
                "exchange_subnet_routes": p.get("exchangeSubnetRoutes"),
                "import_custom_routes": p.get("importCustomRoutes"),
                "export_custom_routes": p.get("exportCustomRoutes"),
                "import_subnet_routes_with_public_ip": p.get(
                    "importSubnetRoutesWithPublicIp"
                ),
                "export_subnet_routes_with_public_ip": p.get(
                    "exportSubnetRoutesWithPublicIp"
                ),
            }
            peer_network = p.get("peerNetwork")
            if peer_network:
                peer_partial_uri = _parse_compute_full_uri_to_partial_uri(peer_network)
                peering["peer_network_partial_uri"] = peer_partial_uri
                # Partial URIs have the form `projects/{project}/global/networks/{name}`
                peering["peer_project_id"] = peer_partial_uri.split("/")[1]
            else:
                peering["peer_network_partial_uri"] = None
                peering["peer_project_id"] = None
            peering_list.append(peering)
    return peering_list


@timeit
def transform_gcp_vpn_gateways(gateways: list[dict], projectid: str) -> list[dict]:
    """
    Transform vpnGateways items (from the aggregatedList response) for Neo4j ingestion.
    :param gateways: Raw vpnGateway items from get_gcp_vpn_gateways()
    :param projectid: The project ID the gateways belong to
    :return: List of VPN gateways ready for ingestion to Neo4j
    """
    gateway_list = []
    for g in gateways:
        gateway: dict[str, Any] = {
            # selfLink has the form
            # `https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/vpnGateways/{name}`
            "partial_uri": _parse_compute_full_uri_to_partial_uri(g["selfLink"]),
            "self_link": g["selfLink"],
            "name": g["name"],
            "project_id": projectid,
            # Region looks like "https://www.googleapis.com/compute/v1/projects/{project}/regions/{region name}"
            "region": g.get("region", "").split("/")[-1],
            "description": g.get("description"),
            "gateway_ip_version": g.get("gatewayIpVersion"),
            "stack_type": g.get("stackType"),
            "creation_timestamp": g.get("creationTimestamp"),
        }
        network = g.get("network")
        gateway["network_partial_uri"] = (
            _parse_compute_full_uri_to_partial_uri(network) if network else None
        )
        gateway_list.append(gateway)
    return gateway_list


@timeit
def transform_gcp_vpn_tunnels(tunnels: list[dict], projectid: str) -> list[dict]:
    """
    Transform vpnTunnels items (from the aggregatedList response) for Neo4j ingestion.
    NOTE: The API response contains `sharedSecret` and `sharedSecretHash` (the
    IKE pre-shared key). We deliberately never copy these fields into the
    transformed output so that VPN secrets are never written to Neo4j.
    :param tunnels: Raw vpnTunnel items from get_gcp_vpn_tunnels()
    :param projectid: The project ID the tunnels belong to
    :return: List of VPN tunnels ready for ingestion to Neo4j
    """
    tunnel_list = []
    for t in tunnels:
        tunnel: dict[str, Any] = {
            "partial_uri": _parse_compute_full_uri_to_partial_uri(t["selfLink"]),
            "self_link": t["selfLink"],
            "name": t["name"],
            "project_id": projectid,
            "region": t.get("region", "").split("/")[-1],
            "description": t.get("description"),
            "status": t.get("status"),
            "detailed_status": t.get("detailedStatus"),
            "peer_ip": t.get("peerIp"),
            "ike_version": t.get("ikeVersion"),
            "local_traffic_selector": t.get("localTrafficSelector"),
            "remote_traffic_selector": t.get("remoteTrafficSelector"),
            "creation_timestamp": t.get("creationTimestamp"),
        }
        for field, out_field in (
            ("vpnGateway", "vpn_gateway_partial_uri"),
            ("peerGcpGateway", "peer_gcp_gateway_partial_uri"),
            ("targetVpnGateway", "target_vpn_gateway_partial_uri"),
            ("router", "router_partial_uri"),
        ):
            full_uri = t.get(field)
            tunnel[out_field] = (
                _parse_compute_full_uri_to_partial_uri(full_uri) if full_uri else None
            )
        tunnel_list.append(tunnel)
    return tunnel_list


@timeit
def transform_gcp_subnets(subnet_res: dict) -> list[dict]:
    """
    Add additional fields to the subnet object to make it easier to process in `load_gcp_subnets()`.
    :param subnet_res: The response object returned from compute.subnetworks.list()
    :return: A transformed subnet_res
    """
    # The `id` in the response object has the form `projects/{project}/regions/{region}/subnetworks`.
    # We can include this in each subnet object in the list to form the partial_uri later on.
    prefix = subnet_res["id"]
    projectid = prefix.split("/")[1]
    subnet_list: list[dict] = []
    for s in subnet_res.get("items", []):
        subnet = {}

        # Has the form `projects/{project}/regions/{region}/subnetworks/{subnet_name}`
        partial_uri = f"{prefix}/{s['name']}"
        subnet["id"] = partial_uri
        subnet["partial_uri"] = partial_uri

        # Let's maintain an on-node reference to the VPC that this subnet belongs to.
        subnet["vpc_self_link"] = s["network"]
        subnet["vpc_partial_uri"] = _parse_compute_full_uri_to_partial_uri(s["network"])

        subnet["name"] = s["name"]
        subnet["project_id"] = projectid
        # Region looks like "https://www.googleapis.com/compute/v1/projects/{project}/regions/{region name}"
        subnet["region"] = s["region"].split("/")[-1]
        subnet["gateway_address"] = s.get("gatewayAddress", None)
        subnet["ip_cidr_range"] = s.get("ipCidrRange", None)
        subnet["self_link"] = s["selfLink"]
        subnet["private_ip_google_access"] = s.get("privateIpGoogleAccess", None)
        subnet["purpose"] = s.get("purpose", None)
        subnet["flow_logs_enabled"] = s.get("enableFlowLogs", None)
        subnet["flow_logs_aggregation_interval"] = s.get("logConfig", {}).get(
            "aggregationInterval", None
        )
        subnet["flow_logs_sampling"] = s.get("logConfig", {}).get("flowSampling", None)
        subnet["flow_logs_metadata"] = s.get("logConfig", {}).get("metadata", None)
        subnet["flow_logs_filter_expr"] = s.get("logConfig", {}).get("filterExpr", None)

        subnet_list.append(subnet)
    return subnet_list


# Map forwarding-rule target collection -> ontology `lb_type`. GCP encodes the load
# balancer family in the target proxy resource path (e.g. targetHttpsProxies, targetPools).
_FORWARDING_RULE_LB_TYPE_BY_TARGET_KIND = {
    "targetHttpProxies": "http",
    "targetHttpsProxies": "https",
    "targetTcpProxies": "tcp",
    "targetSslProxies": "ssl",
    "targetGrpcProxies": "grpc",
    "targetPools": "network",
    # Backend-service-only forwarding rules (no target proxy) are L4 Network LBs.
    # The protocol (TCP/UDP/ESP/L3_DEFAULT) lives on `IPProtocol`, not the family.
    "backendServices": "network",
    "targetInstances": "network",
    "targetVpnGateways": "vpn",
}


def _derive_forwarding_rule_lb_type(*uris: str | None) -> str | None:
    # Forwarding rules either reference a target proxy / pool URI (`target`) or,
    # for internal LBs, point straight at a backend service (`backendService`).
    # Inspect each candidate URI in order and stop at the first known collection
    # segment. Target URIs look like ".../{collection}/{name}", so we walk segments
    # in reverse to ignore the trailing resource name.
    for uri in uris:
        if not uri:
            continue
        for segment in reversed(uri.split("/")):
            if segment in _FORWARDING_RULE_LB_TYPE_BY_TARGET_KIND:
                return _FORWARDING_RULE_LB_TYPE_BY_TARGET_KIND[segment]
    return None


@timeit
def transform_gcp_forwarding_rules(fwd_response: Resource) -> list[dict]:
    """
    Add additional fields to the forwarding rule object to make it easier to process in `load_gcp_forwarding_rules()`.
    :param fwd_response: The response object returned from compute.forwardRules.list()
    :return: A transformed fwd_response
    """
    fwd_list: list[dict] = []
    prefix = fwd_response["id"]
    project_id = prefix.split("/")[1]
    for fwd in fwd_response.get("items", []):
        forwarding_rule: dict[str, Any] = {}

        fwd_partial_uri = f"{prefix}/{fwd['name']}"
        forwarding_rule["id"] = fwd_partial_uri
        forwarding_rule["partial_uri"] = fwd_partial_uri

        forwarding_rule["project_id"] = project_id
        # Region looks like "https://www.googleapis.com/compute/v1/projects/{project}/regions/{region name}"
        region = fwd.get("region", None)
        forwarding_rule["region"] = region.split("/")[-1] if region else None
        forwarding_rule["ip_address"] = fwd.get("IPAddress", None)
        forwarding_rule["ip_protocol"] = fwd.get("IPProtocol", None)
        forwarding_rule["allow_global_access"] = fwd.get("allowGlobalAccess", None)

        forwarding_rule["load_balancing_scheme"] = fwd.get("loadBalancingScheme", None)
        forwarding_rule["name"] = fwd.get("name", None)
        forwarding_rule["port_range"] = fwd.get("portRange", None)
        forwarding_rule["ports"] = fwd.get("ports", None)
        forwarding_rule["self_link"] = fwd.get("selfLink", None)
        target = fwd.get("target", None)
        if target:
            forwarding_rule["target"] = _parse_compute_full_uri_to_partial_uri(target)
        else:
            forwarding_rule["target"] = None
        # Internal regional LBs front a backend service directly and omit `target`,
        # so fall back to the `backendService` URI to recover an lb_type for them.
        forwarding_rule["lb_type"] = _derive_forwarding_rule_lb_type(
            target,
            fwd.get("backendService"),
        )

        network = fwd.get("network", None)
        if network:
            forwarding_rule["network"] = network
            forwarding_rule["network_partial_uri"] = (
                _parse_compute_full_uri_to_partial_uri(network)
            )

        subnetwork = fwd.get("subnetwork", None)
        if subnetwork:
            forwarding_rule["subnetwork"] = subnetwork
            forwarding_rule["subnetwork_partial_uri"] = (
                _parse_compute_full_uri_to_partial_uri(subnetwork)
            )

        fwd_list.append(forwarding_rule)
    return fwd_list


@timeit
def transform_gcp_firewall(fw_response: Resource) -> list[dict]:
    """
    Adjust the firewall response objects into a format that is easy to write to Neo4j.
    Also see _transform_fw_entry and _parse_port_string_to_rule().
    :param fw_response: Firewall response object from the GCP API
    :return: List of transformed firewall rule objects.
    """
    fw_list: list[dict] = []
    prefix = fw_response["id"]
    for fw in fw_response.get("items", []):
        fw_partial_uri = f"{prefix}/{fw['name']}"
        fw["id"] = fw_partial_uri
        fw["vpc_partial_uri"] = _parse_compute_full_uri_to_partial_uri(fw["network"])

        fw["transformed_allow_list"] = []
        fw["transformed_deny_list"] = []
        # Mark whether this FW is defined on a target service account.
        # In future we will need to ingest GCP IAM objects but for now we simply mark the presence of svc accounts here.
        fw["has_target_service_accounts"] = (
            True if "targetServiceAccounts" in fw else False
        )

        for allow_rule in fw.get("allowed", []):
            transformed_allow_rules = _transform_fw_entry(
                allow_rule,
                fw_partial_uri,
                is_allow_rule=True,
            )
            fw["transformed_allow_list"].extend(transformed_allow_rules)

        for deny_rule in fw.get("denied", []):
            transformed_deny_rules = _transform_fw_entry(
                deny_rule,
                fw_partial_uri,
                is_allow_rule=False,
            )
            fw["transformed_deny_list"].extend(transformed_deny_rules)

        fw_list.append(fw)
    return fw_list


def _transform_fw_entry(
    rule: dict,
    fw_partial_uri: str,
    is_allow_rule: bool,
) -> list[dict]:
    """
    Takes a rule entry from a GCP firewall object's allow or deny list and converts it to a list of one or more
    dicts representing a firewall rule for each port and port range.  This format is easier to load into Neo4j.

    Example 1 - single port range:
    Input: `{'IPProtocol': 'tcp', 'ports': ['0-65535']}, fw_id, is_allow_rule=True`
    Output: `[ {fromport: 0, toport: 65535, protocol: tcp, ruleid: fw_id/allow/0to65535tcp} ]`

    Example 2 - multiple ports with a range
    Input: `{'IPProtocol': 'tcp', 'ports': ['80', '443', '12345-12349']}, fw_id, is_allow_rule=False`
    Output: `[ {fromport: 80, toport: 80, protocol: tcp, ruleid: fw_id/deny/80tcp,
               {fromport: 443, toport: 443, protocol: tcp, ruleid: fw_id/deny/443tcp,
               {fromport: 12345, toport: 12349, protocol: tcp, ruleid: fw_id/deny/12345to12349tcp ]`

    Example 3 - ICMP (no ports)
    Input: `{'IPProtocol': 'icmp'}, fw_id, is_allow_rule=True`
    Output: `[ {fromport: None, toport: None, protocol: icmp, ruleid: fw_id/allow/icmp} ]`

    :param rule: A rule entry object
    :param fw_partial_uri: The parent GCPFirewall's unique identifier
    :param is_allow_rule: Whether the rule is an `allow` rule.  If false it is a `deny` rule.
    :return: A list of one or more transformed rules
    """
    result: list[dict] = []
    # rule['ruleid'] = f"{fw_partial_uri}/"
    protocol = rule["IPProtocol"]

    # If the protocol covered is TCP or UDP then we need to handle ports
    if protocol == "tcp" or protocol == "udp":
        # If ports are specified then create rules for each port and range
        if "ports" in rule:
            for port in rule["ports"]:
                rule = _parse_port_string_to_rule(
                    port,
                    protocol,
                    fw_partial_uri,
                    is_allow_rule,
                )
                result.append(rule)
            return result

        # If ports are not specified then the rule applies to every port
        else:
            rule = _parse_port_string_to_rule(
                "0-65535",
                protocol,
                fw_partial_uri,
                is_allow_rule,
            )
            result.append(rule)
            return result

    # The protocol is  ICMP, ESP, AH, IPIP, SCTP, or proto numbers and ports don't apply
    else:
        rule = _parse_port_string_to_rule(None, protocol, fw_partial_uri, is_allow_rule)
        result.append(rule)
        return result


def _parse_port_string_to_rule(
    port: str | None,
    protocol: str,
    fw_partial_uri: str,
    is_allow_rule: bool,
) -> dict:
    """
    Takes a string argument representing a GCP firewall rule port or port range and returns a dict that is easier to
    load into Neo4j.

    Example 1 - single port range:
    Input: `'0-65535', 'tcp', fw_id, is_allow_rule=True`
    Output: `{fromport: 0, toport: 65535, protocol: tcp, ruleid: fw_id/allow/0to65535tcp}`

    Example 2 - single port
    Input: `'80', fw_id, is_allow_rule=False`
    Output: `{fromport: 80, toport: 80, protocol: tcp, ruleid: fw_id/deny/80tcp}`

    Example 3 - ICMP (no ports)
    Input: `None, fw_id, is_allow_rule=True`
    Output: `{fromport: None, toport: None, protocol: icmp, ruleid: fw_id/allow/icmp}`

    :param port: A string representing a single port or a range of ports.  Example inputs include '22' or '12345-12349'
    :param protocol: The protocol
    :param fw_partial_uri: The partial URI of the firewall
    :param is_allow_rule: Whether the rule is an `allow` rule.  If false it is a `deny` rule.
    :return: A dict containing fromport, toport, a ruleid, and protocol
    """
    # `port` can be a range like '12345-12349' or a single port like '22'

    if port is None:
        # Keep the port range as the empty string
        port_range_str = ""
        fromport = None
        toport = None
    else:
        # Case 1 - port range: '12345-12349'.split('-') => ['12345','12349'].
        # Case 2 - single port: '22'.split('-') => ['22'].
        port_split = port.split("-")

        # Port range
        if len(port_split) == 2:
            port_range_str = f"{port_split[0]}to{port_split[1]}"
            fromport = int(port_split[0])
            toport = int(port_split[1])
        # Single port
        else:
            port_range_str = f"{port_split[0]}"
            fromport = int(port_split[0])
            toport = int(port_split[0])

    rule_type = "allow" if is_allow_rule else "deny"

    return {
        "ruleid": f"{fw_partial_uri}/{rule_type}/{port_range_str}{protocol}",
        "fromport": fromport,
        "toport": toport,
        "protocol": protocol,
    }


def _transform_nics(instances: list[dict]) -> list[dict]:
    """
    Transform network interfaces from instances for loading.
    :param instances: List of transformed GCP instances
    :return: List of network interface objects ready for ingestion
    """
    nics: list[dict] = []
    for instance in instances:
        for nic in instance.get("networkInterfaces", []):
            nic_id = f"{instance['partial_uri']}/networkinterfaces/{nic['name']}"
            nics.append(
                {
                    "nic_id": nic_id,
                    "name": nic["name"],
                    "networkIP": nic.get("networkIP"),
                    "instance_partial_uri": instance["partial_uri"],
                    "subnet_partial_uri": nic["subnet_partial_uri"],
                    "vpc_partial_uri": nic["vpc_partial_uri"],
                    "accessConfigs": nic.get("accessConfigs", []),
                }
            )
    return nics


def _get_subnet_stubs_from_nics(nics: list[dict]) -> list[dict]:
    """
    Extract unique subnet stubs from NICs to ensure they exist before creating relationships.
    This preserves the legacy behavior where subnets were created via MERGE if they didn't exist.
    :param nics: List of network interface objects
    :return: List of subnet stub objects with partial_uri
    """
    seen_subnets: set[str] = set()
    subnet_stubs: list[dict] = []
    for nic in nics:
        subnet_uri = nic.get("subnet_partial_uri")
        if subnet_uri and subnet_uri not in seen_subnets:
            seen_subnets.add(subnet_uri)
            subnet_stubs.append(
                {
                    "partial_uri": subnet_uri,
                }
            )
    return subnet_stubs


def _create_subnet_stubs(
    neo4j_session: neo4j.Session,
    subnet_stubs: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    """
    Create GCPSubnet stub nodes if they don't exist.
    This ensures the PART_OF_SUBNET relationship can be created even if the subnet
    hasn't been loaded yet (preserving legacy behavior).
    :param neo4j_session: The Neo4j session
    :param subnet_stubs: List of subnet stub objects
    :param gcp_update_tag: The timestamp
    :param project_id: The GCP project ID
    """
    if not subnet_stubs:
        return
    load(
        neo4j_session,
        GCPSubnetStubSchema(),
        subnet_stubs,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


def _transform_access_configs(nics: list[dict]) -> list[dict]:
    """
    Transform access configs from network interfaces for loading.
    :param nics: List of network interface objects
    :return: List of access config objects ready for ingestion
    """
    access_configs: list[dict] = []
    for nic in nics:
        for ac in nic.get("accessConfigs", []):
            access_config_id = f"{nic['nic_id']}/accessconfigs/{ac['type']}"
            access_configs.append(
                {
                    "access_config_id": access_config_id,
                    "nic_id": nic["nic_id"],
                    "type": ac["type"],
                    "name": ac["name"],
                    "natIP": ac.get("natIP"),
                    "setPublicPtr": ac.get("setPublicPtr"),
                    "publicPtrDomainName": ac.get("publicPtrDomainName"),
                    "networkTier": ac.get("networkTier"),
                }
            )
    return access_configs


def _transform_instance_tags(instances: list[dict]) -> list[dict]:
    """
    Transform network tags from instances for loading.
    Deduplicates on (tag_id, instance_partial_uri) to ensure TAGGED relationships
    are created for all instances sharing the same tag.
    :param instances: List of transformed GCP instances
    :return: List of network tag objects ready for ingestion
    """
    tags: list[dict] = []
    seen_tag_instance_pairs: set[tuple[str, str]] = set()
    for instance in instances:
        for tag in instance.get("tags", {}).get("items", []):
            for nic in instance.get("networkInterfaces", []):
                tag_id = _create_gcp_network_tag_id(nic["vpc_partial_uri"], tag)
                pair = (tag_id, instance["partial_uri"])
                if pair not in seen_tag_instance_pairs:
                    seen_tag_instance_pairs.add(pair)
                    tags.append(
                        {
                            "tag_id": tag_id,
                            "value": tag,
                            "vpc_partial_uri": nic["vpc_partial_uri"],
                            "instance_partial_uri": instance["partial_uri"],
                        }
                    )
    return tags


@timeit
def load_gcp_instances(
    neo4j_session: neo4j.Session,
    data: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    """
    Ingest GCP instance objects to Neo4j
    :param neo4j_session: The Neo4j session object
    :param data: List of GCP instances to ingest. Basically the output of
    https://cloud.google.com/compute/docs/reference/rest/v1/instances/list
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param project_id: The GCP project ID
    :return: Nothing
    """
    # Load instances
    load(
        neo4j_session,
        GCPInstanceSchema(),
        data,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )

    # Transform and load network interfaces
    nics = _transform_nics(data)

    # Create subnet stubs first to ensure PART_OF_SUBNET relationships can be created
    # This preserves legacy behavior where subnets were created via MERGE if they didn't exist
    subnet_stubs = _get_subnet_stubs_from_nics(nics)
    _create_subnet_stubs(neo4j_session, subnet_stubs, gcp_update_tag, project_id)

    load(
        neo4j_session,
        GCPNetworkInterfaceSchema(),
        nics,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )

    # Transform and load access configs
    access_configs = _transform_access_configs(nics)
    load(
        neo4j_session,
        GCPNicAccessConfigSchema(),
        access_configs,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )

    # Transform and load network tags
    tags = _transform_instance_tags(data)
    load(
        neo4j_session,
        GCPNetworkTagSchema(),
        tags,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def load_gcp_vpcs(
    neo4j_session: neo4j.Session,
    vpcs: list[dict[str, Any]],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    load(
        neo4j_session,
        GCPVpcSchema(),
        vpcs,
        PROJECT_ID=project_id,
        LASTUPDATED=gcp_update_tag,
    )


def _get_vpc_stubs_from_peerings(peerings: list[dict]) -> list[dict]:
    """
    Extract unique peer VPC stubs from peering objects so that PEER_NETWORK
    relationships can be established even if the peer VPC's project has not been
    synced. Mirrors the subnet-stub pattern used by the instance sync.
    :param peerings: List of transformed GCPVpcPeering objects
    :return: List of VPC stub objects with partial_uri and project_id
    """
    seen_vpcs: set[str] = set()
    vpc_stubs: list[dict] = []
    for peering in peerings:
        peer_uri = peering.get("peer_network_partial_uri")
        if peer_uri and peer_uri not in seen_vpcs:
            seen_vpcs.add(peer_uri)
            vpc_stubs.append(
                {
                    "partial_uri": peer_uri,
                    "project_id": peering["peer_project_id"],
                }
            )
    return vpc_stubs


def _create_vpc_stubs(
    neo4j_session: neo4j.Session,
    vpc_stubs: list[dict],
    gcp_update_tag: int,
) -> None:
    """
    Create GCPVpc stub nodes if they don't exist. If the peer project is synced
    in the same run, the full VPC sync MERGEs on the same id and fills in all
    properties and labels.
    :param neo4j_session: The Neo4j session
    :param vpc_stubs: List of VPC stub objects
    :param gcp_update_tag: The timestamp
    """
    if not vpc_stubs:
        return
    load(
        neo4j_session,
        GCPVpcStubSchema(),
        vpc_stubs,
        lastupdated=gcp_update_tag,
    )


@timeit
def load_gcp_vpc_peerings(
    neo4j_session: neo4j.Session,
    peerings: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    """
    Ingest GCP VPC peering data to Neo4j
    :param neo4j_session: The Neo4j session
    :param peerings: List of the VPC peerings
    :param gcp_update_tag: The timestamp to set these Neo4j nodes with
    :param project_id: The project ID
    :return: Nothing
    """
    if not peerings:
        return
    load(
        neo4j_session,
        GCPVpcPeeringSchema(),
        peerings,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


def _get_vpn_gateway_stubs_from_tunnels(tunnels: list[dict]) -> list[dict]:
    """
    Extract unique peer VPN gateway stubs from tunnel objects so that
    CONNECTS_TO_GATEWAY relationships can be established even if the peer
    gateway's project has not been synced.
    :param tunnels: List of transformed GCPVpnTunnel objects
    :return: List of VPN gateway stub objects with partial_uri and project_id
    """
    seen_gateways: set[str] = set()
    gateway_stubs: list[dict] = []
    for tunnel in tunnels:
        peer_uri = tunnel.get("peer_gcp_gateway_partial_uri")
        if peer_uri and peer_uri not in seen_gateways:
            seen_gateways.add(peer_uri)
            gateway_stubs.append(
                {
                    "partial_uri": peer_uri,
                    # Partial URIs have the form
                    # `projects/{project}/regions/{region}/vpnGateways/{name}`
                    "project_id": peer_uri.split("/")[1],
                }
            )
    return gateway_stubs


def _create_vpn_gateway_stubs(
    neo4j_session: neo4j.Session,
    gateway_stubs: list[dict],
    gcp_update_tag: int,
) -> None:
    """
    Create GCPVpnGateway stub nodes if they don't exist. If the peer project is
    synced in the same run, the full gateway sync MERGEs on the same id and
    fills in all properties.
    :param neo4j_session: The Neo4j session
    :param gateway_stubs: List of VPN gateway stub objects
    :param gcp_update_tag: The timestamp
    """
    if not gateway_stubs:
        return
    load(
        neo4j_session,
        GCPVpnGatewayStubSchema(),
        gateway_stubs,
        lastupdated=gcp_update_tag,
    )


@timeit
def load_gcp_vpn_gateways(
    neo4j_session: neo4j.Session,
    gateways: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    """
    Ingest GCP HA VPN gateway data to Neo4j
    :param neo4j_session: The Neo4j session
    :param gateways: List of the VPN gateways
    :param gcp_update_tag: The timestamp to set these Neo4j nodes with
    :param project_id: The project ID
    :return: Nothing
    """
    load(
        neo4j_session,
        GCPVpnGatewaySchema(),
        gateways,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def load_gcp_vpn_tunnels(
    neo4j_session: neo4j.Session,
    tunnels: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    """
    Ingest GCP VPN tunnel data to Neo4j
    :param neo4j_session: The Neo4j session
    :param tunnels: List of the VPN tunnels
    :param gcp_update_tag: The timestamp to set these Neo4j nodes with
    :param project_id: The project ID
    :return: Nothing
    """
    load(
        neo4j_session,
        GCPVpnTunnelSchema(),
        tunnels,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def load_gcp_subnets(
    neo4j_session: neo4j.Session,
    subnets: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    """
    Ingest GCP subnet data to Neo4j using the data model
    :param neo4j_session: The Neo4j session
    :param subnets: List of the subnets
    :param gcp_update_tag: The timestamp to set these Neo4j nodes with
    :param project_id: The project ID
    :return: Nothing
    """
    from cartography.models.gcp.compute.subnet import GCPSubnetSchema

    load(
        neo4j_session,
        GCPSubnetSchema(),
        subnets,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def load_gcp_forwarding_rules(
    neo4j_session: neo4j.Session,
    fwd_rules: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    """
    Ingest GCP forwarding rules data to Neo4j
    :param neo4j_session: The Neo4j session
    :param fwd_rules: List of forwarding rules
    :param gcp_update_tag: The timestamp to set these Neo4j nodes with
    :param project_id: The GCP project ID
    :return: Nothing
    """
    # Separate rules by type: those with subnetwork vs those with only network
    rules_with_subnet = [fwd for fwd in fwd_rules if fwd.get("subnetwork")]
    rules_with_vpc_only = [
        fwd for fwd in fwd_rules if fwd.get("network") and not fwd.get("subnetwork")
    ]
    rules_no_network = [
        fwd for fwd in fwd_rules if not fwd.get("network") and not fwd.get("subnetwork")
    ]

    # Load rules with subnet relationships
    if rules_with_subnet:
        load(
            neo4j_session,
            GCPForwardingRuleWithSubnetSchema(),
            rules_with_subnet,
            lastupdated=gcp_update_tag,
            PROJECT_ID=project_id,
        )

    # Load rules with VPC relationships (no subnet)
    if rules_with_vpc_only:
        load(
            neo4j_session,
            GCPForwardingRuleWithVpcSchema(),
            rules_with_vpc_only,
            lastupdated=gcp_update_tag,
            PROJECT_ID=project_id,
        )

    # Load rules without network/subnet relationships
    if rules_no_network:
        load(
            neo4j_session,
            GCPForwardingRuleSchema(),
            rules_no_network,
            lastupdated=gcp_update_tag,
            PROJECT_ID=project_id,
        )


def _transform_firewall_ip_rules(fw_list: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Transform firewall rules to IP rules for loading.
    :param fw_list: List of transformed firewall objects
    :return: Tuple of (allowed_rules, denied_rules)
    """
    allowed_rules: list[dict] = []
    denied_rules: list[dict] = []

    for fw in fw_list:
        for rule in fw.get("transformed_allow_list", []):
            allowed_rules.append(
                {
                    "ruleid": rule["ruleid"],
                    "protocol": rule["protocol"],
                    "fromport": rule.get("fromport"),
                    "toport": rule.get("toport"),
                    "fw_partial_uri": fw["id"],
                }
            )
        for rule in fw.get("transformed_deny_list", []):
            denied_rules.append(
                {
                    "ruleid": rule["ruleid"],
                    "protocol": rule["protocol"],
                    "fromport": rule.get("fromport"),
                    "toport": rule.get("toport"),
                    "fw_partial_uri": fw["id"],
                }
            )

    return allowed_rules, denied_rules


def _transform_firewall_ip_ranges(fw_list: list[dict]) -> list[dict]:
    """
    Transform firewall source ranges to IP range objects for loading.
    :param fw_list: List of transformed firewall objects
    :return: List of IP range objects with their associated rule IDs
    """
    ip_ranges: list[dict] = []
    seen_range_rule_pairs: set[tuple] = set()

    for fw in fw_list:
        source_ranges = fw.get("sourceRanges", [])
        for list_type in ["transformed_allow_list", "transformed_deny_list"]:
            for rule in fw.get(list_type, []):
                for ip_range in source_ranges:
                    pair = (ip_range, rule["ruleid"])
                    if pair not in seen_range_rule_pairs:
                        seen_range_rule_pairs.add(pair)
                        ip_ranges.append(
                            {
                                "range": ip_range,
                                "ruleid": rule["ruleid"],
                            }
                        )

    return ip_ranges


def _transform_firewall_target_tags(fw_list: list[dict]) -> list[dict]:
    """
    Transform firewall target tags for loading.
    :param fw_list: List of transformed firewall objects
    :return: List of target tag relationship objects
    """
    target_tags: list[dict] = []
    seen_fw_tag_pairs: set[tuple] = set()

    for fw in fw_list:
        for tag in fw.get("targetTags", []):
            tag_id = _create_gcp_network_tag_id(fw["vpc_partial_uri"], tag)
            pair = (fw["id"], tag_id)
            if pair not in seen_fw_tag_pairs:
                seen_fw_tag_pairs.add(pair)
                target_tags.append(
                    {
                        "tag_id": tag_id,
                        "value": tag,
                        "vpc_partial_uri": fw["vpc_partial_uri"],
                        "fw_partial_uri": fw["id"],
                    }
                )

    return target_tags


@timeit
def load_gcp_ingress_firewalls(
    neo4j_session: neo4j.Session,
    fw_list: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    """
    Load the firewall list to Neo4j using data models.
    :param neo4j_session: The Neo4j session
    :param fw_list: The transformed list of firewalls
    :param gcp_update_tag: The timestamp
    :param project_id: The GCP project ID
    :return: Nothing
    """
    # Load firewalls
    load(
        neo4j_session,
        GCPFirewallSchema(),
        fw_list,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )

    # Transform and load IP rules (allowed)
    allowed_rules, denied_rules = _transform_firewall_ip_rules(fw_list)
    if allowed_rules:
        load(
            neo4j_session,
            GCPIpRuleAllowedSchema(),
            allowed_rules,
            lastupdated=gcp_update_tag,
            PROJECT_ID=project_id,
        )
    if denied_rules:
        load(
            neo4j_session,
            GCPIpRuleDeniedSchema(),
            denied_rules,
            lastupdated=gcp_update_tag,
            PROJECT_ID=project_id,
        )

    # Transform and load IP ranges
    ip_ranges = _transform_firewall_ip_ranges(fw_list)
    if ip_ranges:
        load(
            neo4j_session,
            IpRangeSchema(),
            ip_ranges,
            lastupdated=gcp_update_tag,
            PROJECT_ID=project_id,
        )

    # Attach target tags to firewalls
    _attach_firewall_target_tags(neo4j_session, fw_list, gcp_update_tag, project_id)


@timeit
def _attach_firewall_target_tags(
    neo4j_session: neo4j.Session,
    fw_list: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    """
    Attach target tags to firewall objects.
    This creates the TARGET_TAG relationship from GCPFirewall to GCPNetworkTag.
    :param neo4j_session: The Neo4j session
    :param fw_list: The firewall list
    :param gcp_update_tag: The timestamp
    :param project_id: The GCP project ID
    :return: Nothing
    """
    target_tags = _transform_firewall_target_tags(fw_list)
    if target_tags:
        load(
            neo4j_session,
            GCPFirewallTargetTagSchema(),
            target_tags,
            lastupdated=gcp_update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def cleanup_gcp_instances(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Delete out-of-date GCP instance nodes and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    GraphJob.from_node_schema(GCPInstanceSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(GCPNetworkInterfaceSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(GCPNicAccessConfigSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(GCPNetworkTagSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_gcp_vpcs(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    """
    Delete out-of-date GCP VPC nodes and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    GraphJob.from_node_schema(
        GCPVpcSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def cleanup_gcp_vpc_peerings(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Delete out-of-date GCP VPC peering nodes and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    GraphJob.from_node_schema(
        GCPVpcPeeringSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def cleanup_gcp_vpn_gateways(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Delete out-of-date GCP VPN gateway nodes and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    GraphJob.from_node_schema(
        GCPVpnGatewaySchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def cleanup_gcp_vpn_tunnels(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Delete out-of-date GCP VPN tunnel nodes and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    GraphJob.from_node_schema(
        GCPVpnTunnelSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def cleanup_gcp_subnets(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Delete out-of-date GCP VPC subnet nodes and relationships using data model
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    GraphJob.from_node_schema(GCPSubnetSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_orphan_gcp_vpc_stubs(neo4j_session: neo4j.Session) -> None:
    """
    Delete GCPVpc stub nodes that are no longer referenced by anything.

    Stubs are created for peering peer networks whose project is not synced, so
    they have no owning `(:GCPProject)-[:RESOURCE]->` edge and are invisible to
    project-scoped cleanup. Once the last peering referencing a stub disappears
    (or the stub never belonged to a synced project), it would otherwise stay
    in the graph forever. Real VPCs always carry a RESOURCE edge from their
    project and are never matched.
    """
    run_write_query(
        neo4j_session,
        """
        MATCH (v:GCPVpc)
        WHERE NOT (:GCPProject)-[:RESOURCE]->(v)
        AND NOT (:GCPVpcPeering)-[:PEER_NETWORK]->(v)
        DETACH DELETE v
        """,
    )


@timeit
def cleanup_orphan_gcp_vpn_gateway_stubs(neo4j_session: neo4j.Session) -> None:
    """
    Delete GCPVpnGateway stub nodes that are no longer referenced by anything.

    Stubs are created for tunnel peer gateways whose project is not synced, so
    they have no owning `(:GCPProject)-[:RESOURCE]->` edge and are invisible to
    project-scoped cleanup. Once the last tunnel referencing a stub disappears,
    it would otherwise stay in the graph forever. Real gateways always carry a
    RESOURCE edge from their project and are never matched.
    """
    run_write_query(
        neo4j_session,
        """
        MATCH (g:GCPVpnGateway)
        WHERE NOT (:GCPProject)-[:RESOURCE]->(g)
        AND NOT (:GCPVpnTunnel)-[:CONNECTS_TO_GATEWAY]->(g)
        AND NOT (:GCPVpnTunnel)-[:USES_GATEWAY]->(g)
        DETACH DELETE g
        """,
    )


@timeit
def cleanup_gcp_forwarding_rules(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Delete out-of-date GCP forwarding rules and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    GraphJob.from_node_schema(GCPForwardingRuleSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_gcp_firewall_rules(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Delete out of date GCP firewalls and their relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    GraphJob.from_node_schema(GCPFirewallSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(GCPIpRuleAllowedSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(GCPIpRuleDeniedSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(IpRangeSchema(), common_job_parameters).run(neo4j_session)
    # Clean up firewall target tags (GCPNetworkTag nodes created by firewalls and their TARGET_TAG relationships)
    GraphJob.from_node_schema(GCPFirewallTargetTagSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_gcp_instances(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    zones: list[dict] | None,
    gcp_update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Get GCP instances using the Compute resource object, ingest to Neo4j, and clean up old data.
    :param neo4j_session: The Neo4j session object
    :param compute: The GCP Compute resource object
    :param project_id: The project ID number to sync.  See  the `projectId` field in
    https://cloud.google.com/resource-manager/reference/rest/v1/projects
    :param zones: The list of all zone names that are enabled for this project; this is the output of
    `get_zones_in_project()`
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    instance_responses = get_gcp_instance_responses(project_id, zones, compute)
    instance_list = transform_gcp_instances(instance_responses)
    load_gcp_instances(neo4j_session, instance_list, gcp_update_tag, project_id)
    # Sync unified GCPLabel nodes - use transformed list since it has partial_uri set
    sync_labels(
        neo4j_session,
        instance_list,
        "gcp_instance",
        project_id,
        gcp_update_tag,
        common_job_parameters,
    )
    cleanup_gcp_instances(neo4j_session, common_job_parameters)


@timeit
def update_gcp_project_compute_metadata(
    neo4j_session: neo4j.Session,
    project_id: str,
    project_metadata: dict,
    gcp_update_tag: int,
) -> None:
    metadata_items = {
        item.get("key"): item.get("value")
        for item in project_metadata.get("commonInstanceMetadata", {}).get("items", [])
        if item.get("key")
    }
    load(
        neo4j_session,
        GCPProjectComputeMetadataSchema(),
        [
            {
                "id": project_id,
                "compute_project_enable_oslogin": metadata_items.get("enable-oslogin"),
            },
        ],
        lastupdated=gcp_update_tag,
    )


@timeit
def sync_gcp_vpcs(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Get GCP VPCs, ingest to Neo4j, and clean up old data.
    :param neo4j_session: The Neo4j session
    :param compute: The GCP Compute resource object
    :param project_id: The project ID to sync
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    vpc_res = get_gcp_vpcs(project_id, compute)
    vpcs = transform_gcp_vpcs(vpc_res)
    load_gcp_vpcs(neo4j_session, vpcs, gcp_update_tag, project_id)
    sync_gcp_vpc_peerings(
        neo4j_session,
        vpc_res,
        project_id,
        gcp_update_tag,
        common_job_parameters,
    )
    cleanup_gcp_vpcs(neo4j_session, common_job_parameters)


@timeit
def sync_gcp_vpc_peerings(
    neo4j_session: neo4j.Session,
    vpc_res: dict,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Extract VPC Network Peerings from the networks.list response, ingest to
    Neo4j, and clean up old data. Peerings are embedded in the VPC response, so
    this reuses the data already fetched by get_gcp_vpcs(). Creates stub GCPVpc
    nodes for peer networks whose projects have not been synced.
    :param neo4j_session: The Neo4j session
    :param vpc_res: The return data from get_gcp_vpcs()
    :param project_id: The project ID to sync
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    peerings = transform_gcp_vpc_peerings(vpc_res)
    # Create peer VPC stubs first so that PEER_NETWORK relationships resolve
    # even when the peer project is not synced.
    _create_vpc_stubs(
        neo4j_session,
        _get_vpc_stubs_from_peerings(peerings),
        gcp_update_tag,
    )
    load_gcp_vpc_peerings(neo4j_session, peerings, gcp_update_tag, project_id)
    cleanup_gcp_vpc_peerings(neo4j_session, common_job_parameters)
    # Remove stub VPCs left behind by peerings that no longer exist. Runs after
    # peering cleanup so stale peerings release their references first.
    cleanup_orphan_gcp_vpc_stubs(neo4j_session)


@timeit
def sync_gcp_vpn_gateways(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Sync GCP HA VPN gateways across all regions via one aggregatedList call
    chain, ingest to Neo4j, and clean up old data.
    Must run after sync_gcp_vpcs so PART_OF_VPC relationships resolve in the same cycle.
    :param neo4j_session: The Neo4j session
    :param compute: The GCP Compute resource object
    :param project_id: The project ID to sync
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    gateway_items, incomplete = get_gcp_vpn_gateways(project_id, compute)
    gateways = transform_gcp_vpn_gateways(gateway_items, project_id)
    load_gcp_vpn_gateways(neo4j_session, gateways, gcp_update_tag, project_id)
    if incomplete:
        logger.warning(
            "Skipping VPN gateway cleanup for project %s because the aggregated "
            "list returned incomplete data. Existing gateway data will be preserved.",
            project_id,
        )
    else:
        cleanup_gcp_vpn_gateways(neo4j_session, common_job_parameters)


@timeit
def sync_gcp_vpn_tunnels(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Sync GCP VPN tunnels across all regions via one aggregatedList call chain,
    ingest to Neo4j, and clean up old data.
    Must run after sync_gcp_vpn_gateways so USES_GATEWAY relationships resolve in
    the same cycle. Creates stub GCPVpnGateway nodes for peer gateways whose
    projects have not been synced.
    :param neo4j_session: The Neo4j session
    :param compute: The GCP Compute resource object
    :param project_id: The project ID to sync
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    tunnel_items, incomplete = get_gcp_vpn_tunnels(project_id, compute)
    tunnels = transform_gcp_vpn_tunnels(tunnel_items, project_id)
    # Create peer gateway stubs first so that CONNECTS_TO_GATEWAY
    # relationships resolve even when the peer project is not synced.
    _create_vpn_gateway_stubs(
        neo4j_session,
        _get_vpn_gateway_stubs_from_tunnels(tunnels),
        gcp_update_tag,
    )
    load_gcp_vpn_tunnels(neo4j_session, tunnels, gcp_update_tag, project_id)
    if incomplete:
        logger.warning(
            "Skipping VPN tunnel cleanup for project %s because the aggregated "
            "list returned incomplete data. Existing tunnel data will be preserved.",
            project_id,
        )
    else:
        cleanup_gcp_vpn_tunnels(neo4j_session, common_job_parameters)
    # Remove stub gateways left behind by tunnels that no longer exist. Safe
    # even when cleanup was suppressed: stale tunnels still reference their
    # stubs, so only truly unreferenced stubs are deleted.
    cleanup_orphan_gcp_vpn_gateway_stubs(neo4j_session)


@timeit
def sync_gcp_subnets(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    regions: list[str],
    gcp_update_tag: int,
    common_job_parameters: dict,
) -> None:
    incomplete = False
    for r in regions:
        subnet_res = get_gcp_subnets(project_id, r, compute)
        if subnet_res is None:
            # Invalid region or timeout, skip this one
            incomplete = True
            continue
        subnets = transform_gcp_subnets(subnet_res)
        load_gcp_subnets(neo4j_session, subnets, gcp_update_tag, project_id)
    if incomplete:
        logger.warning(
            "Skipping subnet cleanup for project %s because one or more regions "
            "returned incomplete data. Existing subnet data will be preserved.",
            project_id,
        )
    else:
        cleanup_gcp_subnets(neo4j_session, common_job_parameters)


@timeit
def sync_gcp_forwarding_rules(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    regions: list[str],
    gcp_update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Sync GCP Both Global and Regional Forwarding Rules, ingest to Neo4j, and clean up old data.
    :param neo4j_session: The Neo4j session
    :param compute: The GCP Compute resource object
    :param project_id: The project ID to sync
    :param regions: List of regions.
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    global_fwd_response = get_gcp_global_forwarding_rules(project_id, compute)
    forwarding_rules = transform_gcp_forwarding_rules(global_fwd_response)
    load_gcp_forwarding_rules(
        neo4j_session, forwarding_rules, gcp_update_tag, project_id
    )

    for r in regions:
        fwd_response = get_gcp_regional_forwarding_rules(project_id, r, compute)
        if fwd_response is None:
            # Invalid region, skip this one
            continue
        forwarding_rules = transform_gcp_forwarding_rules(fwd_response)
        load_gcp_forwarding_rules(
            neo4j_session, forwarding_rules, gcp_update_tag, project_id
        )

    cleanup_gcp_forwarding_rules(neo4j_session, common_job_parameters)


@timeit
def sync_gcp_firewall_rules(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Sync GCP firewalls
    :param neo4j_session: The Neo4j session
    :param compute: The Compute resource object
    :param project_id: The project ID that the firewalls are in
    :param common_job_parameters: dict of other job params to pass to Neo4j
    :return: Nothing
    """
    fw_response = get_gcp_firewall_ingress_rules(project_id, compute)
    fw_list = transform_gcp_firewall(fw_response)
    load_gcp_ingress_firewalls(neo4j_session, fw_list, gcp_update_tag, project_id)
    cleanup_gcp_firewall_rules(neo4j_session, common_job_parameters)


def _zones_to_regions(zones: list[dict]) -> list[str]:
    """
    Return list of regions from the input list of zones
    :param zones: List of zones. This is the output from `get_zones_in_project()`.
    :return: List of regions available to the project
    """
    regions: set[str] = set()
    for zone in zones:
        # Extract region from the zone's region URL
        # The region field is a URL like
        # "https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}"
        region_url = zone.get("region", "")
        if region_url:
            region = region_url.split("/")[-1]
            regions.add(region)
    return list(regions)


def sync(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Sync all objects that we need the GCP Compute resource object for.
    :param neo4j_session: The Neo4j session object
    :param compute: The GCP Compute resource object
    :param project_id: The project ID number to sync.
    :param project_id: The project ID number to sync.  See  the `projectId` field in
    https://cloud.google.com/resource-manager/reference/rest/v1/projects
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    logger.info("Syncing Compute objects for project %s.", project_id)
    zones = get_zones_in_project(project_id, compute)
    # Only pull additional assets for this project if the Compute API is enabled
    if zones is None:
        return
    else:
        try:
            project_metadata = get_gcp_compute_project_metadata(project_id, compute)
        except HttpError as e:
            # zones.list already succeeded above, so the Compute API is enabled and
            # the project exists -- the only realistic 403 left here is missing the
            # compute.projects.get permission specifically. Same skip-and-log
            # treatment as get_zones_in_project() uses two lines above.
            if is_permission_denied_error(e):
                logger.info(
                    "Your GCP identity does not have the compute.projects.get permission for project %s; "
                    "skipping compute sync for this project. %s",
                    project_id,
                    summarize_gcp_http_error(e),
                )
                return
            raise
        update_gcp_project_compute_metadata(
            neo4j_session,
            project_id,
            project_metadata,
            gcp_update_tag,
        )
        regions = _zones_to_regions(zones)
        sync_gcp_vpcs(
            neo4j_session,
            compute,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )
        sync_gcp_firewall_rules(
            neo4j_session,
            compute,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )
        sync_gcp_subnets(
            neo4j_session,
            compute,
            project_id,
            regions,
            gcp_update_tag,
            common_job_parameters,
        )
        # VPN gateways must exist before tunnels so USES_GATEWAY rels resolve
        # in the same sync cycle; both need VPCs already loaded (PART_OF_VPC).
        sync_gcp_vpn_gateways(
            neo4j_session,
            compute,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )
        sync_gcp_vpn_tunnels(
            neo4j_session,
            compute,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )
        sync_gcp_instances(
            neo4j_session,
            compute,
            project_id,
            zones,
            gcp_update_tag,
            common_job_parameters,
        )
        sync_gcp_instance_groups(
            neo4j_session,
            compute,
            project_id,
            zones,
            regions,
            gcp_update_tag,
            common_job_parameters,
        )
        # Cloud Armor policies must exist before backend services so PROTECTS rels
        # can resolve in the same sync cycle.
        sync_gcp_cloud_armor(
            neo4j_session,
            compute,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )
        sync_gcp_backend_services(
            neo4j_session,
            compute,
            project_id,
            regions,
            gcp_update_tag,
            common_job_parameters,
        )
        # SSL policies must exist before target proxies (USES rel), and target
        # proxies must exist before forwarding rules (ROUTES_TO rel) -- same
        # load-before-reference requirement as Cloud Armor -> backend services above.
        sync_gcp_ssl_policies(
            neo4j_session,
            compute,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )
        sync_gcp_target_https_proxies(
            neo4j_session,
            compute,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )
        sync_gcp_target_ssl_proxies(
            neo4j_session,
            compute,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )
        sync_gcp_forwarding_rules(
            neo4j_session,
            compute,
            project_id,
            regions,
            gcp_update_tag,
            common_job_parameters,
        )
