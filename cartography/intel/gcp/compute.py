# Google Compute Engine API-centric functions
# https://cloud.google.com/compute/docs/concepts
import ipaddress
import json
import logging
import time
from collections import namedtuple
from ipaddress import AddressValueError
from ipaddress import NetmaskValueError
from string import Template
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

import neo4j
from botocore.exceptions import ClientError
from cloudconsolelink.clouds.gcp import GCPLinker
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from . import iam
from . import instance_groups
from . import label
from cartography.util import batch
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
gcp_console_link = GCPLinker()
InstanceUriPrefix = namedtuple("InstanceUriPrefix", "zone_name project_id")


@timeit
def get_compute_disks(compute: Resource, project_id: str, zones: list, common_job_parameters) -> List[Dict]:
    if not zones:
        return []
    disks = []
    try:
        for zone in zones:
            req = compute.disks().list(project=project_id, zone=zone["name"])
            while req is not None:
                res = req.execute()
                if res.get("items"):
                    for disk in res["items"]:
                        disk["consolelink"] = gcp_console_link.get_console_link(
                            project_id=project_id,
                            zone=zone["name"],
                            disk_name=disk["name"],
                            resource_name="compute_instance_disk",
                        )
                        disk["project_id"] = project_id
                        disk["id"] = f"projects/{project_id}/disks/{disk['name']}"
                        x = zone["name"].split("-")
                        disk["region"] = f"{x[0]}-{x[1]}"

                        os_feature_types = [feature["type"] for feature in disk.get("guestOsFeatures", [])]
                        disk["osFeatures"] = "WINDOWS" if "WINDOWS" in os_feature_types else "LINUX"

                        disks.append(disk)
                req = compute.disks().list_next(previous_request=req, previous_response=res)

        return disks
    except HttpError as e:
        err = json.loads(e.content.decode("utf-8"))["error"]
        if err.get("status", "") == "PERMISSION_DENIED" or err.get("message", "") == "Forbidden":
            logger.warning(
                ("Could not retrieve compute disks on project %s due to permissions issues. Code: %s, Message: %s"),
                project_id,
                err["code"],
                err["message"],
            )
            return []
        else:
            raise


@timeit
def load_compute_disks(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_compute_disks_tx, data_list, project_id, update_tag)


@timeit
def load_compute_disks_tx(
    tx: neo4j.Transaction,
    data: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    query = """
    UNWIND $Records as record
    MERGE (disk:GCPComputeDisk{id:record.id})
    ON CREATE SET
        disk.firstseen = timestamp()
    SET
        disk.lastupdated = $gcp_update_tag,
        disk.region = record.region,
        disk.name = record.name,
        disk.creation_timestamp = record.creationTimestamp,
        disk.description = record.description,
        disk.zone = record.zone,
        disk.status = record.status,
        disk.source_snapshot = record.sourceSnapshot,
        disk.source_snapshot_id = record.sourceSnapshotId,
        disk.source_storage_object = record.sourceStorageObject,
        disk.options = record.options,
        disk.self_link = record.selfLink,
        disk.source_image = record.sourceImage,
        disk.architecture = record.architecture,
        disk.os_features = record.osFeatures,
        disk.last_attach_timestamp = record.lastAttachTimestamp,
        disk.last_detach_timestamp = record.lastDetachTimestamp,
        disk.physical_block_size_bytes = record.physicalBlockSizeBytes,
        disk.source_disk = record.sourceDisk,
        disk.source_disk_id = record.sourceDiskId,
        disk.consolelink = record.consolelink,
        disk.source_image_id = record.sourceImageId
    WITH disk
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(disk)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        query,
        Records=data,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_compute_disks(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("gcp_compute_disks_cleanup.json", neo4j_session, common_job_parameters)


@timeit
def sync_compute_disks(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    zones: Optional[List[Dict]],
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    disks = get_compute_disks(compute, project_id, zones, common_job_parameters)

    load_compute_disks(neo4j_session, disks, project_id, gcp_update_tag)
    cleanup_compute_disks(neo4j_session, common_job_parameters)


@timeit
def get_https_proxies(compute: Resource, project_id: str, common_job_parameters) -> List[Dict]:
    https_proxies = []
    try:
        req = compute.targetHttpsProxies().list(project=project_id)
        while req is not None:
            res = req.execute()
            if "items" in res:
                https_proxies.extend(res["items"])
            req = compute.targetHttpsProxies().list_next(previous_request=req, previous_response=res)

        return https_proxies

    except HttpError as e:
        err = json.loads(e.content.decode("utf-8"))["error"]
        if err.get("status", "") == "PERMISSION_DENIED" or err.get("message", "") == "Forbidden":
            logger.warning(
                ("Could not retrieve https proxies on project %s due to permissions issues. Code: %s, Message: %s"),
                project_id,
                err["code"],
                err["message"],
            )
            return []
        else:
            raise


@timeit
def transform_https_proxies(proxies: List, project_id: str) -> List[Resource]:
    list_proxies = []
    for proxy in proxies:
        proxy["consolelink"] = gcp_console_link.get_console_link(project_id=project_id, resource_name="vpc_home")
        proxy["id"] = f"projects/{project_id}/global/targetHttpsProxies/{proxy['name']}"
        proxy["type"] = "https"
        list_proxies.append(proxy)

    return list_proxies


@timeit
def get_ssl_proxies(compute: Resource, project_id: str, common_job_parameters) -> List[Dict]:
    ssl_proxies = []
    try:
        req = compute.targetSslProxies().list(project=project_id)
        while req is not None:
            res = req.execute()
            if "items" in res:
                ssl_proxies.extend(res["items"])
            req = compute.targetSslProxies().list_next(previous_request=req, previous_response=res)

        return ssl_proxies

    except HttpError as e:
        err = json.loads(e.content.decode("utf-8"))["error"]
        if err.get("status", "") == "PERMISSION_DENIED" or err.get("message", "") == "Forbidden":
            logger.warning(
                ("Could not retrieve ssl proxies on project %s due to permissions issues. Code: %s, Message: %s"),
                project_id,
                err["code"],
                err["message"],
            )
            return []
        else:
            raise


@timeit
def transform_ssl_proxies(proxies: List, project_id: str) -> List[Resource]:
    list_proxies = []
    for proxy in proxies:
        proxy["consolelink"] = gcp_console_link.get_console_link(project_id=project_id, resource_name="vpc_home")
        proxy["id"] = f"projects/{project_id}/global/targetSslProxies/{proxy['name']}"
        proxy["type"] = "ssl"
        list_proxies.append(proxy)

    return list_proxies


@timeit
def load_proxies(session: neo4j.Session, proxies: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_proxies_tx, proxies, project_id, update_tag)


@timeit
def load_proxies_tx(
    tx: neo4j.Transaction,
    proxies: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    query = """
    UNWIND $Proxies as p
    MERGE (proxy:GCPProxy{id:p.id})
    ON CREATE SET
        proxy.firstseen = timestamp()
    SET
        proxy.lastupdated = $gcp_update_tag,
        proxy.uniqueId = p.id,
        proxy.consolelink = p.consolelink,
        proxy.type = p.type,
        proxy.name = p.name,
        proxy.certificateMap = p.certificateMap,
        proxy.sslPolicy = p.sslPolicy
    WITH proxy
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(proxy)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    tx.run(
        query,
        Proxies=proxies,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def attach_compute_disks_to_instance(
    session: neo4j.Session,
    data_list: List[Dict],
    instance_id: str,
    update_tag: int,
) -> None:
    session.execute_write(attach_compute_disks_to_instance_tx, data_list, instance_id, update_tag)


@timeit
def attach_compute_disks_to_instance_tx(
    tx: neo4j.Transaction,
    data: List[Dict],
    instance_id: str,
    gcp_update_tag: int,
) -> None:
    query = """
    UNWIND $Records as record
    MERGE (disk:GCPComputeDisk{id:record.id})
    ON CREATE SET
        disk.firstseen = timestamp()
    SET
        disk.lastupdated = $gcp_update_tag
    WITH disk
    MATCH (i:GCPInstance{id: $InstanceId})
    MERGE (i)-[r:USES]->(disk)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        query,
        Records=data,
        InstanceId=instance_id,
        gcp_update_tag=gcp_update_tag,
    )


def _get_error_reason(http_error: HttpError) -> str:
    """
    Helper function to get an error reason out of the googleapiclient's HttpError object
    This function copies the structure of
    https://github.com/googleapis/google-api-python-client/blob/1d2e240a74d2bc0074dffbc57cf7d62b8146cb82/
                                  googleapiclient/http.py#L111
    At the moment this is the best way we know of to extract the HTTP failure reason.
    Additionally, see https://github.com/googleapis/google-api-python-client/issues/662.
    :param http_error: The googleapi HttpError object
    :return: The error reason as a string
    """
    try:
        data = json.loads(http_error.content.decode("utf-8"))
        if isinstance(data, dict):
            reason = data["error"]["errors"][0]["reason"]
        else:
            reason = data[0]["error"]["errors"]["reason"]
    except (UnicodeDecodeError, ValueError, KeyError):
        logger.warning(f"HttpError: {data}")
        return ""
    return reason


@timeit
def get_zones_in_project(project_id: str, compute: Resource, max_results: Optional[int] = None) -> Optional[List[Dict]]:
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
        res = req.execute()
        return res["items"]
    except HttpError as e:
        reason = _get_error_reason(e)
        if reason == "accessNotConfigured":
            logger.info(
                ("Google Compute Engine API access is not configured for project %s; skipping. " "Full details: %s"),
                project_id,
                e,
            )
            return None
        elif reason == "notFound":
            logger.info(
                ("Project %s returned a 404 not found error. " "Full details: %s"),
                project_id,
                e,
            )
            return None
        elif reason == "forbidden":
            logger.info(
                (
                    "Your GCP identity does not have the compute.zones.list permission for project %s; skipping "
                    "compute sync for this project. Full details: %s"
                ),
                project_id,
                e,
            )
            return None
        else:
            raise


@timeit
def get_gcp_instances(project_id: str, zones: Optional[List[Dict]], compute: Resource) -> List[Resource]:
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
    response_objects: List[Resource] = []
    for zone in zones:
        logger.info("Instance zone %s.", zone["name"])
        req = compute.instances().list(project=project_id, zone=zone["name"])
        res = req.execute()
        response_objects.extend(res.get("items", []))
    return response_objects


@timeit
def get_gcp_instance_policy_entities(item: Dict, compute: Resource) -> List[Resource]:
    """
    Return list of GCP instance policy users response objects for a given project and zones
    :param project_id: The project ID
    :param zones: The list of zones to query for instances
    :param compute: The compute resource object
    :return: A list of iam_policy users
    """
    try:
        project_id = item["project_id"]
        iam_policy = (
            compute.instances()
            .getIamPolicy(
                project=project_id,
                zone=item["zone_name"],
                resource=item.get("id"),
            )
            .execute()
        )
        bindings = iam_policy.get("bindings", [])
        entity_list, public_access = iam.transform_bindings(bindings, project_id)
        return entity_list, public_access
    except HttpError as e:
        err = json.loads(e.content.decode("utf-8"))["error"]
        if err.get("status", "") == "PERMISSION_DENIED" or err.get("message", "") == "Forbidden":
            logger.warning(
                (
                    "Could not GCP instance policy on project %s due to permissions issues.\
                         Code: %s, Message: %s"
                ),
                project_id,
                err["code"],
                err["message"],
            )
            return [], False

        elif err.get("status", "") == "NOT_FOUND" or err.get("code", "") == 404:
            logger.warning(
                (
                    "Could not retrieve GCP instance policy for Project %s \
                         Code: %s, Message: %s"
                ),
                project_id,
                err["code"],
                err["message"],
            )
            return [], False
        else:
            raise


@timeit
def get_gcp_subnets(projectid: str, region: str, compute: Resource) -> Resource:
    """
    Return list of all subnets in the given projectid and region
    :param projectid: THe projectid
    :param region: The region to pull subnets from
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Response object containing data on all GCP subnets for a given project
    """
    req = compute.subnetworks().list(project=projectid, region=region)
    return req.execute()


@timeit
def get_gcp_vpcs(projectid: str, compute: Resource) -> Resource:
    """
    Get VPC data for given project
    :param projectid: The project ID
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: VPC response object
    """
    req = compute.networks().list(project=projectid)
    return req.execute()


@timeit
def get_gcp_regional_forwarding_rules(project_id: str, region: str, compute: Resource) -> Resource:
    """
    Return list of all regional forwarding rules in the given project_id and region
    :param project_id: The project ID
    :param region: The region to pull forwarding rules from
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Response object containing data on all GCP forwarding rules for a given project
    """
    req = compute.forwardingRules().list(project=project_id, region=region)
    return req.execute()


@timeit
def get_gcp_global_forwarding_rules(project_id: str, compute: Resource) -> Resource:
    """
    Return list of all global forwarding rules in the given project_id and region
    :param project_id: The project ID
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Response object containing data on all GCP forwarding rules for a given project
    """
    req = compute.globalForwardingRules().list(project=project_id)
    return req.execute()


@timeit
def get_gcp_firewall_ingress_rules(project_id: str, compute: Resource) -> Resource:
    """
    Get ingress Firewall data for a given project
    :param project_id: The project ID to get firewalls for
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Firewall response object
    """
    req = compute.firewalls().list(project=project_id, filter='(direction="INGRESS")')
    return req.execute()


@timeit
def transform_gcp_instances(response_objects: List[Dict], compute: Resource) -> List[Dict]:
    """
    Process the GCP instance response objects and return a flattened list of GCP instances with all the necessary fields
    we need to load it into Neo4j
    :param response_objects: The return data from get_gcp_instance_responses()
    :return: A list of GCP instances
    """
    instance_list = []
    for res in response_objects:
        # prefix is of the form-
        # https://www.googleapis.com/compute/v1/projects/<project_id>/zones/<zone_name>/<resource_name>
        prefix = res["zone"]

        prefix_fields = _parse_instance_uri_prefix(prefix)

        res["instance_id"] = res["id"]
        res["id"] = f"projects/{prefix_fields.project_id}/zones/{prefix_fields.zone_name}/instances/{res['name']}"
        res["partial_uri"] = res["id"]

        res["project_id"] = prefix_fields.project_id
        res["zone_name"] = prefix_fields.zone_name
        res["accessConfig"] = res.get("accessConfig", None)
        res["public_access"] = res.get("public_access", [])
        res["consolelink"] = gcp_console_link.get_console_link(
            resource_name="compute_instance",
            instance_name=res["name"],
            project_id=res["project_id"],
            zone=res["zone_name"],
        )
        x = res["zone_name"].split("-")
        res["region"] = f"{x[0]}-{x[1]}"

        # Extract GKE metadata labels if this instance is a Kubernetes node.
        # GCP automatically attaches these labels to all GKE-managed Compute instances.
        labels = res.get("labels", {})
        res["gke_cluster_name"] = labels.get("goog-gke-cluster-name")
        res["gke_node_pool_name"] = labels.get("goog-gke-nodepool")

        scheduling = res.get("scheduling", {})
        res["is_spot_instance"] = scheduling.get("provisioningModel") == "SPOT" or scheduling.get("preemptible") is True

        for disk in res.get("disks", []):
            if disk.get("boot"):
                res["diskName"] = disk.get("initializeParams", {}).get("diskName")
                os_feature_types = [feature["type"] for feature in disk.get("guestOsFeatures", [])]
                res["osFeatures"] = "WINDOWS" if "WINDOWS" in os_feature_types else "LINUX"
                break

        for nic in res.get("networkInterfaces", []):
            res["networkIP"] = nic.get("networkIP", None)
            nic["subnet_partial_uri"] = _parse_compute_full_uri_to_partial_uri(nic["subnetwork"])
            nic["vpc_partial_uri"] = _parse_compute_full_uri_to_partial_uri(nic["network"])
            nic["consolelink"] = gcp_console_link.get_console_link(
                project_id=prefix_fields.project_id,
                network_name=nic["network"],
                resource_name="compute_instance_vpc_network",
            )
            for accessconfig in nic.get("accessConfigs", []):
                accessconfig["consolelink"] = gcp_console_link.get_console_link(
                    project_id=prefix_fields.project_id,
                    network_name=nic["network"],
                    resource_name="compute_instance_vpc_network",
                )
                if not res.get("natIP", None):
                    res["natIP"] = accessconfig.get("natIP", None)
                else:
                    break
            for ipv6AccessConfig in nic.get("ipv6AccessConfigs", []):
                if not res.get("ipv6natIP", None):
                    res["ipv6natIP"] = ipv6AccessConfig.get("natIP", None)
                else:
                    break
        for disk in res.get("disks", []):
            if disk.get("boot"):
                res["sourceImage"] = disk.get("initializeParams", {}).get("sourceImage")
                break
        instance_list.append(res)
    return instance_list


def _parse_instance_uri_prefix(prefix: str) -> InstanceUriPrefix:
    """
    Helper function to parse a GCP prefix string of the form `projects/{project}/zones/{zone}/instances`
    :param prefix: String of the form `projects/{project}/zones/{zone}/instances`
    :return: namedtuple with fields project_id and zone_name
    """
    split_list = prefix.split("/")
    return InstanceUriPrefix(
        project_id=split_list[6],
        zone_name=split_list[8],
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
    items = full_uri.split(f"compute/{version}/")
    if len(items) > 1:
        return full_uri.split(f"compute/{version}/")[1]
    else:
        return full_uri


def _create_gcp_network_tag_id(vpc_partial_uri: str, tag: str) -> str:
    """
    Generate an ID for a GCP network tag
    :param vpc_partial_uri: The VPC that this tag applies to
    :return: An ID for the GCP network tag
    """
    return f"{vpc_partial_uri}/tags/{tag}"


@timeit
def transform_gcp_vpcs(vpc_res: Dict) -> List[Dict]:
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
        vpc["consolelink"] = gcp_console_link.get_console_link(
            resource_name="compute_instance_vpc_network",
            project_id=projectid,
            network_name=v["name"],
        )
        vpc["id"] = f"projects/{projectid}/global/networks/{v['name']}"
        vpc["partial_uri"] = vpc["id"]
        vpc["name"] = v["name"]
        vpc["self_link"] = v["selfLink"]
        vpc["project_id"] = projectid
        vpc["auto_create_subnetworks"] = v.get("autoCreateSubnetworks", None)
        vpc["description"] = v.get("description", None)
        vpc["routing_config_routing_mode"] = v.get("routingConfig", {}).get("routingMode", None)

        if v.get("name") == "default" and v.get("autoCreateSubnetworks"):
            vpc["isDefault"] = True
        else:
            vpc["isDefault"] = False

        vpc_list.append(vpc)
    return vpc_list


def get_default_vpc(projectId: str, compute: Resource):
    vpc_response = get_gcp_vpcs(projectid=projectId, compute=compute)

    if not vpc_response or 'items' not in vpc_response:
        return None

    default_vpc = next(
        (
            network for network in vpc_response['items']
            if network['name'] == 'default' and
            network.get('autoCreateSubnetworks', False)
        ),
        None,
    )

    return default_vpc


@timeit
def transform_gcp_subnets(subnet_res: Dict, projectId: str, compute: Resource) -> List[Dict]:
    """
    Add additional fields to the subnet object to make it easier to process in `load_gcp_subnets()`.
    :param subnet_res: The response object returned from compute.subnetworks.list()
    :return: A transformed subnet_res
    """
    # The `id` in the response object has the form `projects/{project}/regions/{region}/subnetworks`.
    # We can include this in each subnet object in the list to form the partial_uri later on.
    prefix = subnet_res["id"]

    projectid = prefix.split("/")[1]
    subnet_list: List[Dict] = []
    for s in subnet_res.get("items", []):
        subnet = {}

        # Has the form `projects/{project}/locations/{region}/subnetworks/{subnet_name}`
        subnet["id"] = f"projects/{projectid}/locations/{s['region'].split('/')[-1]}/subnetworks/{s['name']}"
        subnet["partial_uri"] = subnet["id"]

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
        subnet["consolelink"] = gcp_console_link.get_console_link(
            resource_name="compute_instance_vpc_network_subnet",
            project_id=projectid,
            region=subnet["region"],
            subnet_name=subnet["name"],
        )
        subnet["private_ip_google_access"] = s.get("privateIpGoogleAccess", None)

        default_vpc = get_default_vpc(projectId=projectId, compute=compute)
        if default_vpc and default_vpc.get("selfLink") == s.get("network") and default_vpc.get("autoCreateSubnetworks"):
            subnet["isDefault"] = True
        else:
            subnet["isDefault"] = False

        subnet_list.append(subnet)
    return subnet_list


@timeit
def transform_gcp_forwarding_rules(fwd_response: Resource) -> List[Dict]:
    """
    Add additional fields to the forwarding rule object to make it easier to process in `load_gcp_forwarding_rules()`.
    :param fwd_response: The response object returned from compute.forwardRules.list()
    :return: A transformed fwd_response
    """
    fwd_list: List[Dict] = []
    prefix = fwd_response["id"]

    project_id = prefix.split("/")[1]
    for fwd in fwd_response.get("items", []):
        forwarding_rule: Dict[str, Any] = {}

        forwarding_rule["project_id"] = project_id
        # Region looks like "https://www.googleapis.com/compute/v1/projects/{project}/regions/{region name}"
        region = fwd.get("region", None)
        forwarding_rule["region"] = region.split("/")[-1] if region else "global"

        forwarding_rule["id"] = (
            f"projects/{project_id}/locations/{forwarding_rule['region']}/forwardingRules/{fwd['name']}"
        )
        forwarding_rule["partial_uri"] = forwarding_rule["id"]

        forwarding_rule["ip_address"] = fwd.get("IPAddress", None)
        forwarding_rule["ip_protocol"] = fwd.get("IPProtocol", None)
        forwarding_rule["allow_global_access"] = fwd.get("allowGlobalAccess", None)

        forwarding_rule["load_balancing_scheme"] = fwd.get("loadBalancingScheme", None)
        forwarding_rule["name"] = fwd["name"]
        forwarding_rule["port_range"] = fwd.get("portRange", None)
        forwarding_rule["ports"] = fwd.get("ports", None)
        forwarding_rule["self_link"] = fwd["selfLink"]
        forwarding_rule["consolelink"] = gcp_console_link.get_console_link(
            resource_name="compute_forwarding_rule",
            project_id=project_id,
            rule_name=forwarding_rule["name"],
            region=forwarding_rule["region"],
        )
        target = fwd.get("target", None)
        if target:
            forwarding_rule["target"] = _parse_compute_full_uri_to_partial_uri(target)
        else:
            forwarding_rule["target"] = None

        network = fwd.get("network", None)
        if network:
            forwarding_rule["network"] = network
            forwarding_rule["network_partial_uri"] = _parse_compute_full_uri_to_partial_uri(network)

        subnetwork = fwd.get("subnetwork", None)
        if subnetwork:
            forwarding_rule["subnetwork"] = subnetwork
            forwarding_rule["subnetwork_partial_uri"] = _parse_compute_full_uri_to_partial_uri(subnetwork)

        fwd_list.append(forwarding_rule)
    return fwd_list


@timeit
def transform_gcp_firewall(fw_response: Resource) -> List[Dict]:
    """
    Adjust the firewall response objects into a format that is easy to write to Neo4j.
    Also see _transform_fw_entry and _parse_port_string_to_rule().
    :param fw_response: Firewall response object from the GCP API
    :return: List of transformed firewall rule objects.
    """
    fw_list: List[Dict] = []
    prefix = fw_response["id"]

    projectid = prefix.split("/")[1]
    for fw in fw_response.get("items", []):
        fw_partial_uri = f"{prefix}/{fw['name']}"
        fw["id"] = f"projects/{projectid}/global/firewalls/{fw['name']}"
        fw["vpc_partial_uri"] = _parse_compute_full_uri_to_partial_uri(fw["network"])
        fw["consolelink"] = gcp_console_link.get_console_link(
            resource_name="compute_firewall_rule",
            project_id=projectid,
            rule_name=fw["name"],
        )
        fw["transformed_allow_list"] = []
        fw["transformed_deny_list"] = []
        # Mark whether this FW is defined on a target service account.
        # In future we will need to ingest GCP IAM objects but for now we simply mark the presence of svc accounts here.
        fw["has_target_service_accounts"] = True if "targetServiceAccounts" in fw else False

        for allow_rule in fw.get("allowed", []):
            transformed_allow_rules = _transform_fw_entry(allow_rule, fw_partial_uri, is_allow_rule=True)
            fw["transformed_allow_list"].extend(transformed_allow_rules)

        for deny_rule in fw.get("denied", []):
            transformed_deny_rules = _transform_fw_entry(deny_rule, fw_partial_uri, is_allow_rule=False)
            fw["transformed_deny_list"].extend(transformed_deny_rules)

        fw_list.append(fw)
    return fw_list


def _transform_fw_entry(rule: Dict, fw_partial_uri: str, is_allow_rule: bool) -> List[Dict]:
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
    result: List[Dict] = []
    # rule['ruleid'] = f"{fw_partial_uri}/"
    protocol = rule["IPProtocol"]

    # If the protocol covered is TCP or UDP then we need to handle ports
    if protocol == "tcp" or protocol == "udp":
        # If ports are specified then create rules for each port and range
        if "ports" in rule:
            for port in rule["ports"]:
                rule = _parse_port_string_to_rule(port, protocol, fw_partial_uri, is_allow_rule)
                result.append(rule)
            return result

        # If ports are not specified then the rule applies to every port
        else:
            rule = _parse_port_string_to_rule("0-65535", protocol, fw_partial_uri, is_allow_rule)
            result.append(rule)
            return result

    # The protocol is  ICMP, ESP, AH, IPIP, SCTP, or proto numbers and ports don't apply
    else:
        rule = _parse_port_string_to_rule(None, protocol, fw_partial_uri, is_allow_rule)
        result.append(rule)
        return result


def _parse_port_string_to_rule(port: Optional[str], protocol: str, fw_partial_uri: str, is_allow_rule: bool) -> Dict:
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


@timeit
def load_gcp_instances(session: neo4j.Session, instances_list: List[Dict], gcp_update_tag: int) -> None:
    logger.info(f"Loading instances  {len(instances_list)}")
    for paginated_instances in batch(instances_list, size=500):
        session.execute_write(load_gcp_instances_tx, paginated_instances, gcp_update_tag)

    for instance in instances_list:
        _attach_instance_tags(session, instance, gcp_update_tag)
        _attach_gcp_nics(session, instance, gcp_update_tag)
        _attach_gcp_vpc(session, instance["partial_uri"], gcp_update_tag)
        _attach_instance_service_account(session, instance, gcp_update_tag)
        # Link to GKE cluster and node pool when the instance carries GKE metadata labels.
        # These labels (goog-gke-cluster-name, goog-gke-nodepool) are attached automatically
        # by GCP to every Compute instance that is a GKE node.
        if instance.get("gke_cluster_name"):
            _link_instance_to_gke_cluster(session, instance, gcp_update_tag)
        if instance.get("gke_cluster_name") and instance.get("gke_node_pool_name"):
            _link_instance_to_gke_node_pool(session, instance, gcp_update_tag)

    load_gcp_instance_image_relations(session, instances_list, gcp_update_tag)


@timeit
def _link_instance_to_gke_cluster(
    neo4j_session: neo4j.Session, instance: Dict, gcp_update_tag: int,
) -> None:
    """
    Create a (GKECluster)-[:HAS_NODE]->(GCPInstance) relationship.

    Uses MATCH for GKECluster (not MERGE) so that if the GKE sync has not yet
    run for this project the relationship is simply skipped rather than creating
    a dangling, property-less GKECluster stub.

    The cluster ID is reconstructed with the same format as get_gke_clusters():
        projects/{project_id}/locations/{region}/clusters/{cluster_name}

    :type neo4j_session: neo4j.Session
    :param neo4j_session: The Neo4j session
    :type instance: Dict
    :param instance: A single transformed GCP instance dict.
                     Must contain 'project_id', 'region', and 'gke_cluster_name'.
    :type gcp_update_tag: int
    :param gcp_update_tag: Timestamp to stamp on the relationship
    :rtype: NoneType
    :return: Nothing
    """
    query = """
    MATCH (cluster:GKECluster{id: $ClusterId})
    MATCH (i:GCPInstance{id: $InstanceId})
    MERGE (cluster)-[r:HAS_NODE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    cluster_id = (
        f"projects/{instance['project_id']}/locations/{instance['region']}"
        f"/clusters/{instance['gke_cluster_name']}"
    )
    neo4j_session.run(
        query,
        ClusterId=cluster_id,
        InstanceId=instance["partial_uri"],
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def _link_instance_to_gke_node_pool(
    neo4j_session: neo4j.Session, instance: Dict, gcp_update_tag: int,
) -> None:
    """
    Create a (GKENodePool)-[:HAS_NODE]->(GCPInstance) relationship.

    Uses MATCH for GKENodePool (not MERGE) so that if the GKE sync has not yet
    run for this project the relationship is simply skipped.

    The node pool ID is reconstructed with the same format as _load_gke_node_pools_tx():
        projects/{project_id}/locations/{region}/clusters/{cluster_name}/nodePools/{pool_name}

    :type neo4j_session: neo4j.Session
    :param neo4j_session: The Neo4j session
    :type instance: Dict
    :param instance: A single transformed GCP instance dict.
                     Must contain 'project_id', 'region', 'gke_cluster_name', and 'gke_node_pool_name'.
    :type gcp_update_tag: int
    :param gcp_update_tag: Timestamp to stamp on the relationship
    :rtype: NoneType
    :return: Nothing
    """
    query = """
    MATCH (pool:GKENodePool{id: $NodePoolId})
    MATCH (i:GCPInstance{id: $InstanceId})
    MERGE (pool)-[r:HAS_NODE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    cluster_id = (
        f"projects/{instance['project_id']}/locations/{instance['region']}"
        f"/clusters/{instance['gke_cluster_name']}"
    )
    node_pool_id = f"{cluster_id}/nodePools/{instance['gke_node_pool_name']}"
    neo4j_session.run(
        query,
        NodePoolId=node_pool_id,
        InstanceId=instance["partial_uri"],
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_gcp_instance_image_relations(
    session: neo4j.Session,
    instances_list: List[Dict],
    gcp_update_tag: int,
) -> None:
    session.execute_write(_load_gcp_instance_image_relations_tx, instances_list, gcp_update_tag)


def _load_gcp_instance_image_relations_tx(
    tx: neo4j.Transaction,
    instances: List[Dict],
    gcp_update_tag: int,
) -> None:
    ingest_image = """
    UNWIND $instances AS instance
    WITH instance
    WHERE instance.sourceImage IS NOT NULL
    MERGE (img:GCPImage {id: instance.sourceImage})
    ON CREATE SET img.firstseen = timestamp()
    SET img.lastupdated = $gcp_update_tag,
        img.self_link = instance.sourceImage
    WITH img, instance
    MATCH (i:GCPInstance {id: instance.partial_uri})
    MERGE (i)-[:HAS]->(img)
    MERGE (i)-[rel:HAS]->(img)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_image,
        instances=instances,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_gcp_instances_tx(tx: neo4j.Transaction, instances: Dict, gcp_update_tag: int) -> None:
    """
    Ingest GCP instance objects to Neo4j
    :param neo4j_session: The Neo4j session object
    :param data: List of GCP instances to ingest. Basically the output of
    https://cloud.google.com/compute/docs/reference/rest/v1/instances/list
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :return: Nothing
    """
    ingest_instances = """
    UNWIND $instances as instance
    MERGE (p:GCPProject{id:instance.project_id})
    ON CREATE SET p.firstseen = timestamp()
    SET p.lastupdated = $gcp_update_tag

    MERGE (i:Instance:GCPInstance{id:instance.partial_uri})
    ON CREATE SET i.firstseen = timestamp(),
    i.partial_uri = instance.partial_uri
    SET i:GCPComputeInstance
    SET i.self_link = instance.selfLink,
    i.instancename = instance.name,
    i.instance_id = instance.instance_id,
    i.hostname = instance.hostname,
    i.region = instance.region,
    i.zone_name = instance.zone_name,
    i.project_id = instance.project_id,
    i.natIP = instance.natIP,
    i.networkIP = instance.networkIP,
    i.ipv6_nat_ip = instance.ipv6natIP,
    i.accessConfig = instance.accessConfig,
    i.status = instance.status,
    i.consolelink = instance.consolelink,
    i.lastupdated = $gcp_update_tag,
    i.machine_type = instance.machineType,
    i.source_image = instance.sourceImage,
    i.disk_name = instance.diskName,
    i.os_features = instance.osFeatures,
    i.gke_cluster_name = instance.gke_cluster_name,
    i.gke_node_pool_name = instance.gke_node_pool_name,
    i.is_spot_instance = instance.is_spot_instance
    WITH i, p

    MERGE (p)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    tx.run(
        ingest_instances,
        instances=instances,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_compute_entity_relation(session: neo4j.Session, instance: Dict, update_tag: int) -> None:
    session.execute_write(load_compute_entity_relation_tx, instance, update_tag)


@timeit
def load_compute_entity_relation_tx(tx: neo4j.Transaction, instance: Dict, gcp_update_tag: int) -> None:
    """
    :type neo4j_session: Neo4j session object
    :param neo4j session: The Neo4j session object

    :type instance: Dict
    :param instance: instance Dict object

    :type project_id: str
    :param project_id: Current Google Project Id

    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :rtype: NoneType
    :return: Nothing
    """
    ingest_entities = """
    UNWIND $entities AS entity
    MATCH (principal:GCPPrincipal{email:entity.email})
    WITH principal
    MATCH (i:GCPInstance{id: $instance_id})
    MERGE (principal)-[r:USES]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag    """
    tx.run(
        ingest_entities,
        instance_id=instance.get("name", None),
        entities=instance.get("entities", []),
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_gcp_vpcs(neo4j_session: neo4j.Session, vpcs: List[Dict], gcp_update_tag: int) -> None:
    """
    Ingest VPCs to Neo4j
    :param neo4j_session: The Neo4j session object
    :param vpcs: List of VPCs to ingest
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :return: Nothing
    """
    query = """
    MERGE (p:GCPProject{id: $ProjectId})
    ON CREATE SET p.firstseen = timestamp()
    SET p.lastupdated = $gcp_update_tag

    MERGE (vpc:GCPVpc{id: $PartialUri})
    ON CREATE SET vpc.firstseen = timestamp(),
    vpc.partial_uri = $PartialUri
    SET vpc.self_link = $SelfLink,
    vpc.region = $region,
    vpc.name = $VpcName,
    vpc.project_id =  $ProjectId,
    vpc.auto_create_subnetworks = $AutoCreateSubnetworks,
    vpc.routing_config_routing_mode = $RoutingMode,
    vpc.description = $Description,
    vpc.consolelink = $consolelink,
    vpc.lastupdated = $gcp_update_tag,
    vpc.is_default = $isDefault

    MERGE (p)-[r:RESOURCE]->(vpc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    for vpc in vpcs:
        neo4j_session.run(
            query,
            ProjectId=vpc["project_id"],
            PartialUri=vpc["partial_uri"],
            SelfLink=vpc["self_link"],
            VpcName=vpc["name"],
            AutoCreateSubnetworks=vpc["auto_create_subnetworks"],
            RoutingMode=vpc["routing_config_routing_mode"],
            Description=vpc["description"],
            region=vpc.get("region"),
            consolelink=vpc.get("consolelink"),
            gcp_update_tag=gcp_update_tag,
            isDefault=vpc.get("isDefault"),
        )


@timeit
def load_gcp_subnets(neo4j_session: neo4j.Session, subnets: List[Dict], gcp_update_tag: int) -> None:
    """
    Ingest GCP subnet data to Neo4j
    :param neo4j_session: The Neo4j session
    :param subnets: List of the subnets
    :param gcp_update_tag: The timestamp to set these Neo4j nodes with
    :return: Nothing
    """
    query = """
    MERGE (vpc:GCPVpc{id: $VpcPartialUri})
    ON CREATE SET vpc.firstseen = timestamp(),
    vpc.partial_uri = $VpcPartialUri
    SET vpc.lastupdated = $gcp_update_tag

    MERGE (subnet:GCPSubnet{id: $PartialUri})
    ON CREATE SET subnet.firstseen = timestamp(),
    subnet.partial_uri = $PartialUri
    SET subnet.self_link = $SubnetSelfLink,
    subnet.project_id = $ProjectId,
    subnet.name = $SubnetName,
    subnet.region = $Region,
    subnet.gateway_address = $GatewayAddress,
    subnet.ip_cidr_range = $IpCidrRange,
    subnet.private_ip_google_access = $PrivateIpGoogleAccess,
    subnet.vpc_partial_uri = $VpcPartialUri,
    subnet.consolelink = $consolelink,
    subnet.lastupdated = $gcp_update_tag,
    subnet.is_default = $isDefault

    MERGE (vpc)-[r:RESOURCE]->(subnet)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    for s in subnets:
        neo4j_session.run(
            query,
            VpcPartialUri=s["vpc_partial_uri"],
            VpcSelfLink=s["vpc_self_link"],
            PartialUri=s["partial_uri"],
            SubnetSelfLink=s["self_link"],
            ProjectId=s["project_id"],
            SubnetName=s["name"],
            Region=s["region"],
            GatewayAddress=s["gateway_address"],
            IpCidrRange=s["ip_cidr_range"],
            PrivateIpGoogleAccess=s["private_ip_google_access"],
            consolelink=s["consolelink"],
            gcp_update_tag=gcp_update_tag,
            isDefault=s["isDefault"],
        )


@timeit
def load_gcp_forwarding_rules(neo4j_session: neo4j.Session, fwd_rules: List[Dict], gcp_update_tag: int) -> None:
    """
    Ingest GCP forwarding rules data to Neo4j
    :param neo4j_session: The Neo4j session
    :param fwd_rules: List of forwarding rules
    :param gcp_update_tag: The timestamp to set these Neo4j nodes with
    :return: Nothing
    """

    query = """
        MERGE (fwd:GCPForwardingRule{id: $PartialUri})
        ON CREATE SET fwd.firstseen = timestamp(),
        fwd.partial_uri = $PartialUri
        SET fwd.ip_address = $IPAddress,
        fwd.ip_protocol = $IPProtocol,
        fwd.load_balancing_scheme = $LoadBalancingScheme,
        fwd.name = $Name,
        fwd.network = $NetworkPartialUri,
        fwd.port_range = $PortRange,
        fwd.ports = $Ports,
        fwd.project_id = $ProjectId,
        fwd.region = $Region,
        fwd.self_link = $SelfLink,
        fwd.subnetwork = $SubNetworkPartialUri,
        fwd.target = $TargetPartialUri,
        fwd.consolelink = $consolelink,
        fwd.lastupdated = $gcp_update_tag
    """

    for fwd in fwd_rules:
        network = fwd.get("network", None)
        subnetwork = fwd.get("subnetwork", None)

        neo4j_session.run(
            query,
            PartialUri=fwd["partial_uri"],
            IPAddress=fwd["ip_address"],
            IPProtocol=fwd["ip_protocol"],
            LoadBalancingScheme=fwd["load_balancing_scheme"],
            Name=fwd["name"],
            Network=network,
            NetworkPartialUri=fwd.get("network_partial_uri", None),
            PortRange=fwd.get("port_range", None),
            Ports=fwd.get("ports", None),
            ProjectId=fwd["project_id"],
            Region=fwd.get("region", "global"),
            SelfLink=fwd["self_link"],
            SubNetwork=subnetwork,
            SubNetworkPartialUri=fwd.get("subnetwork_partial_uri", None),
            TargetPartialUri=fwd["target"],
            consolelink=fwd.get("consolelink", None),
            gcp_update_tag=gcp_update_tag,
        )

        if subnetwork:
            _attach_fwd_rule_to_subnet(neo4j_session, fwd, gcp_update_tag)
        elif network:
            _attach_fwd_rule_to_vpc(neo4j_session, fwd, gcp_update_tag)


@timeit
def _attach_fwd_rule_to_subnet(neo4j_session: neo4j.Session, fwd: Dict, gcp_update_tag: int) -> None:
    query = """
        MERGE (subnet:GCPSubnet{id: $SubNetworkPartialUri})
        ON CREATE SET subnet.firstseen = timestamp(),
        subnet.partial_uri = $SubNetworkPartialUri
        SET subnet.lastupdated = $gcp_update_tag

        WITH subnet
        MATCH(fwd:GCPForwardingRule{id: $PartialUri})

        MERGE (subnet)-[p:RESOURCE]->(fwd)
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        query,
        PartialUri=fwd["partial_uri"],
        SubNetworkPartialUri=fwd.get("subnetwork_partial_uri", None),
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def _attach_fwd_rule_to_vpc(neo4j_session: neo4j.Session, fwd: Dict, gcp_update_tag: int) -> None:
    query = """
        MERGE (vpc:GCPVpc{id: $NetworkPartialUri})
        ON CREATE SET vpc.firstseen = timestamp(),
        vpc.partial_uri = $NetworkPartialUri
        SET vpc.lastupdated = $gcp_update_tag

        WITH vpc
        MATCH (fwd:GCPForwardingRule{id: $PartialUri})

        MERGE (vpc)-[r:RESOURCE]->(fwd)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        query,
        PartialUri=fwd["partial_uri"],
        NetworkPartialUri=fwd.get("network_partial_uri", None),
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def _attach_instance_tags(neo4j_session: neo4j.Session, instance: Resource, gcp_update_tag: int) -> None:
    """
    Attach tags to GCP instance and to the VPCs that they are defined in.
    :param neo4j_session: The session
    :param instance: The instance object
    :param gcp_update_tag: The timestamp
    :return: Nothing
    """
    query = """
    MATCH (i:GCPInstance{id: $InstanceId})

    MERGE (t:GCPNetworkTag{id: $TagId})
    ON CREATE SET t.tag_id = $TagId,
    t.value = $TagValue,
    t.firstseen = timestamp()
    SET t.lastupdated = $gcp_update_tag

    MERGE (i)-[h:TAGGED]->(t)
    ON CREATE SET h.firstseen = timestamp()
    SET h.lastupdated = $gcp_update_tag

    WITH t
    MATCH (vpc:GCPVpc{id: $VpcPartialUri})

    MERGE (vpc)<-[d:DEFINED_IN]-(t)
    ON CREATE SET d.firstseen = timestamp()
    SET d.lastupdated = $gcp_update_tag
    """
    for tag in instance.get("tags", {}).get("items", []):
        for nic in instance.get("networkInterfaces", []):
            tag_id = _create_gcp_network_tag_id(nic["vpc_partial_uri"], tag)
            neo4j_session.run(
                query,
                InstanceId=instance["partial_uri"],
                TagId=tag_id,
                TagValue=tag,
                VpcPartialUri=nic["vpc_partial_uri"],
                gcp_update_tag=gcp_update_tag,
            )


@timeit
def _attach_gcp_nics(neo4j_session: neo4j.Session, instance: Resource, gcp_update_tag: int) -> None:
    """
    Attach GCP Network Interfaces to GCP Instances and GCP Subnets.
    Then, attach GCP Instances directly to VPCs.
    :param neo4j_session: The Neo4j session
    :param instance: The GCP instance
    :param gcp_update_tag: Timestamp to set the nodes
    :return: Nothing
    """
    query = """
    MATCH (i:GCPInstance{id: $InstanceId})
    MERGE (nic:GCPNetworkInterface{id: $NicId})
    ON CREATE SET nic.firstseen = timestamp(),
    nic.nic_id = $NicId
    SET nic.network = $Network,
    nic.consolelink=$ConsoleLink,
    nic.name = $NicName,
    nic.lastupdated = $gcp_update_tag
    MERGE (i)-[r:NETWORK_INTERFACE]->(nic)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag

    MERGE (subnet:GCPSubnet{id: $SubnetPartialUri})
    ON CREATE SET subnet.firstseen = timestamp(),
    subnet.partial_uri = $SubnetPartialUri
    SET subnet.lastupdated = $gcp_update_tag

    MERGE (nic)-[p:PART_OF_SUBNET]->(subnet)
    ON CREATE SET p.firstseen = timestamp()
    SET p.lastupdated = $gcp_update_tag
    """
    for nic in instance.get("networkInterfaces", []):
        # Make an ID for GCPNetworkInterface nodes because GCP doesn't define one but we need to uniquely identify them
        nic_id = f"{instance['partial_uri']}/networkinterfaces/{nic['name']}"
        neo4j_session.run(
            query,
            InstanceId=instance["partial_uri"],
            NicId=nic_id,
            NetworkIP=nic.get("networkIP"),
            Network=nic.get("network"),
            NicName=nic["name"],
            ConsoleLink=nic.get("consolelink"),
            gcp_update_tag=gcp_update_tag,
            SubnetPartialUri=nic["subnet_partial_uri"],
        )
        _attach_gcp_nic_access_configs(neo4j_session, nic_id, nic, gcp_update_tag)


@timeit
def _attach_gcp_nic_access_configs(
    neo4j_session: neo4j.Session,
    nic_id: str,
    nic: Resource,
    gcp_update_tag: int,
) -> None:
    """
    Attach an access configuration to the GCP NIC.
    :param neo4j_session: The Neo4j session
    :param instance: The GCP instance
    :param gcp_update_tag: The timestamp to set updated nodes to
    :return: Nothing
    """
    query = """
    MATCH (nic{id: $NicId})
    MERGE (ac:GCPNicAccessConfig{id: $AccessConfigId})
    ON CREATE SET ac.firstseen = timestamp(),
    ac.access_config_id = $AccessConfigId
    SET ac.type=$Type,
    ac.name = $Name,
    ac.consolelink=$ConsoleLink,
    ac.public_ip =  $NatIP,
    ac.set_public_ptr = $SetPublicPtr,
    ac.public_ptr_domain_name = $PublicPtrDomainName,
    ac.network_tier = $NetworkTier,
    ac.lastupdated = $gcp_update_tag

    MERGE (nic)-[r:RESOURCE]->(ac)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    for ac in nic.get("accessConfigs", []):
        # Make an ID for GCPNicAccessConfig nodes because GCP doesn't define one but we need to uniquely identify them
        access_config_id = f"{nic_id}/accessconfigs/{ac['type']}"
        neo4j_session.run(
            query,
            NicId=nic_id,
            AccessConfigId=access_config_id,
            Type=ac["type"],
            Name=ac["name"],
            ConsoleLink=ac.get("consolelink"),
            NatIP=ac.get("natIP", None),
            SetPublicPtr=ac.get("setPublicPtr", None),
            PublicPtrDomainName=ac.get("publicPtrDomainName", None),
            NetworkTier=ac.get("networkTier", None),
            gcp_update_tag=gcp_update_tag,
        )


@timeit
def _attach_gcp_vpc(neo4j_session: neo4j.Session, instance_id: str, gcp_update_tag: int) -> None:
    """
    Attach a GCP instance directly to a VPC
    :param neo4j_session: neo4j_session
    :param instance: The GCP instance object
    :param gcp_update_tag:
    :return: Nothing
    """
    query = """
    MATCH (i:GCPInstance{id: $InstanceId})-[:NETWORK_INTERFACE]->(nic:GCPNetworkInterface)
          -[p:PART_OF_SUBNET]->(sn:GCPSubnet)<-[r:RESOURCE]-(vpc:GCPVpc)
    MERGE (i)-[m:MEMBER_OF_GCP_VPC]->(vpc)
    ON CREATE SET m.firstseen = timestamp()
    SET m.lastupdated = $gcp_update_tag
    """
    neo4j_session.run(
        query,
        InstanceId=instance_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def _attach_instance_service_account(neo4j_session: neo4j.Session, instance: Resource, gcp_update_tag: int) -> None:
    """
    Attach service account to GCP instance
    :param neo4j_session: The session
    :param instance: The instance object
    :param gcp_update_tag: The timestamp
    :return: Nothing
    """
    query = """
    MATCH (i:GCPInstance{id: $InstanceId})
    MERGE (sa:GCPServiceAccount{email: $AccountEmail})
    MERGE (i)-[r:USES]->(sa)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    for account in instance.get("serviceAccounts", []):
        neo4j_session.run(
            query,
            InstanceId=instance["partial_uri"],
            AccountEmail=account.get("email", ""),
            gcp_update_tag=gcp_update_tag,
        )


@timeit
def load_gcp_ingress_firewalls(neo4j_session: neo4j.Session, fw_list: List[Resource], gcp_update_tag: int) -> None:
    """
    Load the firewall list to Neo4j
    :param fw_list: The transformed list of firewalls
    :return: Nothing
    """
    query = """
    MERGE (fw:GCPFirewall{id: $FwPartialUri})
    ON CREATE SET fw.firstseen = timestamp(),
    fw.partial_uri = $FwPartialUri
    SET fw.direction = $Direction,
    fw.disabled = $Disabled,
    fw.name = $Name,
    fw.region = $region,
    fw.priority = $Priority,
    fw.self_link = $SelfLink,
    fw.has_target_service_accounts = $HasTargetServiceAccounts,
    fw.consolelink = $consolelink,
    fw.network = $Network,
    fw.lastupdated = $gcp_update_tag

    MERGE (vpc:GCPVpc{id: $VpcPartialUri})
    ON CREATE SET vpc.firstseen = timestamp(),
    vpc.partial_uri = $VpcPartialUri
    SET vpc.lastupdated = $gcp_update_tag

    MERGE (vpc)-[r:RESOURCE]->(fw)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    for fw in fw_list:
        neo4j_session.run(
            query,
            FwPartialUri=fw["id"],
            Direction=fw["direction"],
            Disabled=fw["disabled"],
            Name=fw["name"],
            Priority=fw["priority"],
            SelfLink=fw["selfLink"],
            region="global",
            VpcPartialUri=fw["vpc_partial_uri"],
            HasTargetServiceAccounts=fw["has_target_service_accounts"],
            consolelink=fw["consolelink"],
            Network=fw["network"],
            gcp_update_tag=gcp_update_tag,
        )
        _attach_firewall_rules(neo4j_session, fw, gcp_update_tag)
        _attach_target_tags(neo4j_session, fw, gcp_update_tag)
        _attach_firewall_public_ip_address(neo4j_session, fw, gcp_update_tag)


@timeit
def _attach_firewall_public_ip_address(neo4j_session: neo4j.Session, fw: Resource, gcp_update_tag: int) -> None:
    ingest_public_ip_address = """
    UNWIND $PublicIpAddress as ip
        MERGE (i:GCPPublicIpAddress{ipAddress:ip})
            ON CREATE SET i.firstseen = timestamp()
            SET i.lastupdated = $gcp_update_tag,
                i.IpAddress=ip,
                i.id=ip,
                i.type='Internal',
                i.source='GCP',
                i.resource='FirewallRule',
                i.lastupdated = $gcp_update_tag
        with i
            MATCH (p:GCPFirewall{id: $FwId})
        with i,p
         MERGE (p)-[r:MEMBER_OF_PUBLIC_IP_ADDRESS]->(i)
         ON CREATE SET r.firstseen = timestamp()
         SET
         r.lastupdated = $gcp_update_tag
    """
    public_ip_address = []
    for ip in fw.get("sourceRanges", []):
        try:
            if not ipaddress.IPv4Network(str(ip).split("/")[0]).is_private:
                public_ip_address.append(ip)
        except AddressValueError as e:
            logger.warning(f"failed to check public ip, error related to the address - {e}")
        except NetmaskValueError as e:
            logger.warning(f" failed to check public ip, error related to the net mask - {e}")
        except Exception as e:
            logger.warning(f"failed to check public ip - {e}")
    neo4j_session.run(
        query=ingest_public_ip_address,
        PublicIpAddress=public_ip_address,
        FwId=fw["id"],
        gcp_update_tag=gcp_update_tag,
    )


def determine_ip_type(ip_range: str) -> str:
    """
    Helper function to determine if an IP range is IPv4 or IPv6.
    :param ip_range: The IP range as a string
    :return: 'IPv4' if it's an IPv4 range, 'IPv6' if it's an IPv6 range, or 'Invalid' if neither.
    """
    try:
        ip = ipaddress.ip_network(ip_range.split("/")[0], strict=False)
        if isinstance(ip, ipaddress.IPv4Network):
            return "IPv4"
        elif isinstance(ip, ipaddress.IPv6Network):
            return "IPv6"
    except ValueError:
        return "IPv4"


@timeit
def _attach_firewall_rules(neo4j_session: neo4j.Session, fw: Resource, gcp_update_tag: int) -> None:
    """
    Attach the allow_rules and deny_rules to the Firewall object, forming IpRule nodes.
    This function also creates separate IpRange (for IPv4) and Ipv6Range nodes.

    :param neo4j_session: The Neo4j session
    :param fw: The Firewall object
    :param gcp_update_tag: The timestamp for updates
    :return: None
    """

    # query that makes
    query_ipv4 = Template("""
    MATCH (fw:GCPFirewall{id: $FwPartialUri})

    MERGE (rule:IpRule:IpPermissionInbound:GCPIpRule{id: $RuleId})
    ON CREATE SET rule.firstseen = timestamp(),
    rule.ruleid = $RuleId
    SET rule.protocol = $Protocol,
    rule.fromport = $FromPort,
    rule.toport = $ToPort,
    rule.lastupdated = $gcp_update_tag

    MERGE (rng:IpRange{id: $Range})
    ON CREATE SET rng.firstseen = timestamp(),
    rng.range = $Range
    SET rng.lastupdated = $gcp_update_tag

    MERGE (rng)-[m:MEMBER_OF_IP_RULE]->(rule)
    ON CREATE SET m.firstseen = timestamp()
    SET m.lastupdated = $gcp_update_tag

    MERGE (fw)<-[r:$fw_rule_relationship_label]-(rule)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """)

    query_ipv6 = Template("""
    MATCH (fw:GCPFirewall{id: $FwPartialUri})

    MERGE (rule:IpRule:IpPermissionInbound:GCPIpRule{id: $RuleId})
    ON CREATE SET rule.firstseen = timestamp(),
    rule.ruleid = $RuleId
    SET rule.protocol = $Protocol,
    rule.fromport = $FromPort,
    rule.toport = $ToPort,
    rule.lastupdated = $gcp_update_tag

    MERGE (rng:Ipv6Range{id: $Range})
    ON CREATE SET rng.firstseen = timestamp(),
    rng.range = $Range
    SET rng.lastupdated = $gcp_update_tag

    MERGE (rng)-[m:MEMBER_OF_IP_RULE]->(rule)
    ON CREATE SET m.firstseen = timestamp()
    SET m.lastupdated = $gcp_update_tag

    MERGE (fw)<-[r:$fw_rule_relationship_label]-(rule)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """)

    for list_type in ["transformed_allow_list", "transformed_deny_list"]:
        if list_type == "transformed_allow_list":
            label = "ALLOWED_BY"
        else:
            label = "DENIED_BY"

        for rule in fw.get(list_type, []):
            # Iterate over all source ranges (IP addresses or CIDRs)
            for ip_range in fw.get("sourceRanges", []):
                ip_type = determine_ip_type(ip_range)

                if ip_type == "IPv4":
                    # Run the query for IPv4 ranges
                    neo4j_session.run(
                        query_ipv4.safe_substitute(fw_rule_relationship_label=label),
                        FwPartialUri=fw["id"],
                        RuleId=rule["ruleid"],
                        Protocol=rule["protocol"],
                        FromPort=rule.get("fromport"),
                        ToPort=rule.get("toport"),
                        Range=ip_range,
                        gcp_update_tag=gcp_update_tag,
                    )

                elif ip_type == "IPv6":
                    # Run the query for IPv6 ranges
                    neo4j_session.run(
                        query_ipv6.safe_substitute(fw_rule_relationship_label=label),
                        FwPartialUri=fw["id"],
                        RuleId=rule["ruleid"],
                        Protocol=rule["protocol"],
                        FromPort=rule.get("fromport"),
                        ToPort=rule.get("toport"),
                        Range=ip_range,
                        gcp_update_tag=gcp_update_tag,
                    )


@timeit
def _attach_target_tags(neo4j_session: neo4j.Session, fw: Resource, gcp_update_tag: int) -> None:
    """
    Attach target tags to the firewall object
    :param neo4j_session: The neo4j session
    :param fw: The firewall object
    :param gcp_update_tag: The timestamp
    :return: Nothing
    """
    query = """
    MATCH (fw:GCPFirewall{id: $FwPartialUri})

    MERGE (t:GCPNetworkTag{id: $TagId})
    ON CREATE SET t.firstseen = timestamp(),
    t.tag_id = $TagId,
    t.value = $TagValue
    SET t.lastupdated = $gcp_update_tag

    MERGE (fw)-[h:TARGET_TAG]->(t)
    ON CREATE SET h.firstseen = timestamp()
    SET h.lastupdated = $gcp_update_tag
    """
    for tag in fw.get("targetTags", []):
        tag_id = _create_gcp_network_tag_id(fw["vpc_partial_uri"], tag)
        neo4j_session.run(
            query,
            FwPartialUri=fw["id"],
            TagId=tag_id,
            TagValue=tag,
            gcp_update_tag=gcp_update_tag,
        )


@timeit
def cleanup_gcp_instances(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP instance nodes and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    run_cleanup_job("gcp_compute_instance_cleanup.json", neo4j_session, common_job_parameters)


@timeit
def cleanup_gke_compute_links(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """Removes stale HAS_NODE relationships between GKE resources and Compute instances."""
    run_cleanup_job("gcp_gke_compute_links_cleanup.json", neo4j_session, common_job_parameters)


@timeit
def cleanup_gcp_vpcs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP VPC nodes and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    run_cleanup_job("gcp_compute_vpc_cleanup.json", neo4j_session, common_job_parameters)


@timeit
def cleanup_gcp_subnets(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP VPC subnet nodes and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    run_cleanup_job("gcp_compute_vpc_subnet_cleanup.json", neo4j_session, common_job_parameters)


@timeit
def cleanup_gcp_forwarding_rules(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP forwarding rules and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    run_cleanup_job("gcp_compute_forwarding_rules_cleanup.json", neo4j_session, common_job_parameters)


@timeit
def cleanup_gcp_firewall_rules(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out of date GCP firewalls and their relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    try:
        run_cleanup_job("gcp_compute_firewall_cleanup.json", neo4j_session, common_job_parameters)

    except ClientError as ex:
        logger.error("error while syncing gcp firewall rules", ex)


@timeit
def cleanup_gcp_proxies(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out of date GCP Proxies and their relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    try:
        run_cleanup_job("gcp_compute_proxies_cleanup.json", neo4j_session, common_job_parameters)

    except ClientError as ex:
        logger.error("error while syncing gcp proxies", ex)


@timeit
def sync_gcp_https_proxies(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Get GCP Https Proxies, ingest to Neo4j, and clean up old data.
    :param neo4j_session: The Neo4j session
    :param compute: The GCP Compute resource object
    :param project_id: The project ID to sync
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    h_proxies = get_https_proxies(compute, project_id, common_job_parameters)
    https_proxies = transform_https_proxies(h_proxies, project_id)
    load_proxies(neo4j_session, https_proxies, project_id, gcp_update_tag)

    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_gcp_proxies(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, https_proxies, gcp_update_tag, common_job_parameters, "proxies", "GCPProxy")


@timeit
def sync_gcp_ssl_proxies(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Get GCP SSL Proxies, ingest to Neo4j, and clean up old data.
    :param neo4j_session: The Neo4j session
    :param compute: The GCP Compute resource object
    :param project_id: The project ID to sync
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    s_proxies = get_ssl_proxies(compute, project_id, common_job_parameters)
    ssl_proxies = transform_ssl_proxies(s_proxies, project_id)
    load_proxies(neo4j_session, ssl_proxies, project_id, gcp_update_tag)

    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_gcp_proxies(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, ssl_proxies, gcp_update_tag, common_job_parameters, "proxies", "GCPProxy")


@timeit
def sync_gcp_instances(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    zones: Optional[List[Dict]],
    gcp_update_tag: int,
    common_job_parameters: Dict,
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

    instance_responses = get_gcp_instances(project_id, zones, compute)

    instance_list = transform_gcp_instances(instance_responses, compute)

    load_gcp_instances(neo4j_session, instance_list, gcp_update_tag)

    # attach compute instance to disks
    for instance in instance_list:
        disks = []
        for disk in instance.get("disks", []):
            disk["id"] = f"projects/{project_id}/disks/{disk.get('initializeParams', {}).get('diskName', '')}"
            disks.append(disk)
        attach_compute_disks_to_instance(neo4j_session, disks, instance["partial_uri"], gcp_update_tag)

    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_gcp_instances(neo4j_session, common_job_parameters)
    cleanup_gke_compute_links(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, instance_list, gcp_update_tag, common_job_parameters, "instances", "GCPInstance")


@timeit
def sync_gcp_vpcs(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
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

    load_gcp_vpcs(neo4j_session, vpcs, gcp_update_tag)
    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_gcp_vpcs(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, vpcs, gcp_update_tag, common_job_parameters, "vpcs", "GCPVpc")


@timeit
def sync_gcp_subnets(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    regions: List[str],
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for r in regions:
        logger.info("Subnet Region %s.", r)
        subnet_res = get_gcp_subnets(project_id, r, compute)
        subnets = transform_gcp_subnets(subnet_res, project_id, compute)

        load_gcp_subnets(neo4j_session, subnets, gcp_update_tag)
        # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
        cleanup_gcp_subnets(neo4j_session, common_job_parameters)


@timeit
def sync_gcp_forwarding_rules(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    regions: List[str],
    gcp_update_tag: int,
    common_job_parameters: Dict,
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
    logger.info("Syncing Compute forwarding rule for project %s.", project_id)
    global_fwd_response = get_gcp_global_forwarding_rules(project_id, compute)
    forwarding_rules = transform_gcp_forwarding_rules(global_fwd_response)

    load_gcp_forwarding_rules(neo4j_session, forwarding_rules, gcp_update_tag)
    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_gcp_forwarding_rules(neo4j_session, common_job_parameters)

    for r in regions:
        logger.info("Forwarding Rule Region %s.", r)
        fwd_response = get_gcp_regional_forwarding_rules(project_id, r, compute)
        forwarding_rules = transform_gcp_forwarding_rules(fwd_response)
        load_gcp_forwarding_rules(neo4j_session, forwarding_rules, gcp_update_tag)
        # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
        cleanup_gcp_forwarding_rules(neo4j_session, common_job_parameters)


@timeit
def sync_gcp_firewall_rules(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
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

    load_gcp_ingress_firewalls(neo4j_session, fw_list, gcp_update_tag)
    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_gcp_firewall_rules(neo4j_session, common_job_parameters)


def _zones_to_regions(zones: List[str]) -> List[Set]:
    """
    Return list of regions from the input list of zones
    :param zones: List of zones. This is the output from `get_zones_in_project()`.
    :return: List of regions available to the project
    """
    regions = set()
    for zone in zones:
        # Chop off the last 2 chars to turn the zone to a region
        region = zone["name"][:-2]  # type: ignore
        regions.add(region)
    return list(regions)  # type: ignore


def sync(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict,
    regions: list,
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
    tic = time.perf_counter()

    logger.info(f"Syncing Compute for project {project_id}, at {tic}")

    zones = get_zones_in_project(project_id, compute)
    # Only pull additional assets for this project if the Compute API is enabled
    if zones is None:
        return
    else:
        if regions:
            zones_list = []
            for zone in zones:
                if zone["name"][:-2] in regions:
                    zones_list.append(zone)
            zones = zones_list

        regions = _zones_to_regions(zones)
        sync_gcp_vpcs(neo4j_session, compute, project_id, gcp_update_tag, common_job_parameters)

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
        sync_gcp_instances(
            neo4j_session,
            compute,
            project_id,
            zones,
            gcp_update_tag,
            common_job_parameters,
        )
        instance_groups.sync_managed_instance_groups(
            neo4j_session,
            compute,
            project_id,
            zones,
            regions,
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
        sync_compute_disks(
            neo4j_session,
            compute,
            project_id,
            zones,
            gcp_update_tag,
            common_job_parameters,
        )
        sync_gcp_https_proxies(
            neo4j_session,
            compute,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )
        sync_gcp_ssl_proxies(
            neo4j_session,
            compute,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )

    toc = time.perf_counter()
    logger.info(f"Time to process Compute: {toc - tic:0.4f} seconds")
