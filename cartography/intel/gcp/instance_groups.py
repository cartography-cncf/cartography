import json
import logging
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from cloudconsolelink.clouds.gcp import GCPLinker
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
gcp_console_link = GCPLinker()


def _parse_mig_zone_region(self_link: str, fallback_zone: Optional[str], fallback_region: Optional[str]) -> Dict:
    """
    Best-effort extraction of zone/region from a MIG selfLink.
    If parsing fails, use fallback values derived from the request scope.
    """

    zone = None
    region = None

    if "/zones/" in self_link:
        zone = self_link.split("/zones/")[1].split("/")[0]
    if "/regions/" in self_link:
        region = self_link.split("/regions/")[1].split("/")[0]

    return {
        "zone": zone or fallback_zone,
        "region": region or fallback_region,
    }


def _get_zonal_managed_instance_groups(
    compute: Resource,
    project_id: str,
    zones: List[Dict],
) -> List[Dict]:
    migs: List[Dict] = []
    for zone in zones:
        zone_name = zone["name"]
        try:
            req = compute.instanceGroupManagers().list(project=project_id, zone=zone_name)
            res = req.execute()
            if "items" in res:
                for igm in res["items"]:
                    zone_region = _parse_mig_zone_region(igm.get("selfLink", ""), zone_name, None)
                    migs.append(
                        {
                            "id": igm["selfLink"],
                            "name": igm["name"],
                            "project_id": project_id,
                            "zone": zone_region["zone"],
                            "region": zone_region["region"],
                            # Used later in listManagedInstances() calls.
                            "instanceGroupManager_name": igm["name"],
                            "consolelink": gcp_console_link.get_console_link(
                                resource_name='global_instance_group',
                                project_id=project_id,
                                zone=zone_region["zone"],
                                instance_group_name=igm["name"],
                            ),
                        },
                    )
        except HttpError as e:
            # Permissions issues are expected sometimes; skip safely.
            err = json.loads(e.content.decode("utf-8")).get("error", {})
            if err.get("status", "") == "PERMISSION_DENIED" or err.get("message", "") == "Forbidden":
                logger.warning("Skipping zonal MIGs for %s due to permissions. Project=%s", zone_name, project_id)
                continue
            raise

    return migs


def _get_regional_managed_instance_groups(compute: Resource, project_id: str, regions: List[str]) -> List[Dict]:
    migs: List[Dict] = []
    for region in regions:
        try:
            req = compute.regionInstanceGroupManagers().list(project=project_id, region=region)
            res = req.execute()
            if "items" in res:
                for igm in res["items"]:
                    zone_region = _parse_mig_zone_region(igm.get("selfLink", ""), None, region)
                    migs.append(
                        {
                            "id": igm["selfLink"],
                            "name": igm["name"],
                            "project_id": project_id,
                            "zone": zone_region["zone"],
                            "region": zone_region["region"],
                            # Used later in listManagedInstances() calls.
                            "instanceGroupManager_name": igm["name"],
                            "consolelink": gcp_console_link.get_console_link(
                                resource_name='regional_instance_group',
                                project_id=project_id,
                                region=zone_region["region"],
                                instance_group_name=igm["name"],
                            ),
                        },
                    )
        except HttpError as e:
            err = json.loads(e.content.decode("utf-8")).get("error", {})
            if err.get("status", "") == "PERMISSION_DENIED" or err.get("message", "") == "Forbidden":
                logger.warning("Skipping regional MIGs for %s due to permissions. Project=%s", region, project_id)
                continue
            raise
    return migs


def _load_managed_instance_groups(
    session: neo4j.Session,
    migs: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    session.execute_write(_load_managed_instance_groups_tx, migs, project_id, gcp_update_tag)


def _load_managed_instance_groups_tx(
    tx: neo4j.Transaction,
    migs: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    query = """
    UNWIND $migs AS mig
    MERGE (ig:GCPInstanceGroup{id: mig.id})
    ON CREATE SET ig.firstseen = timestamp()
    SET
        ig.uniqueId = mig.id,
        ig.lastupdated = $gcp_update_tag,
        ig.name = mig.name,
        ig.project_id = mig.project_id,
        ig.zone = mig.zone,
        ig.region = mig.region,
        ig.consolelink = mig.consolelink
    WITH ig
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(ig)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    tx.run(
        query,
        migs=migs,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


def _get_managed_instances_for_mig(compute: Resource, project_id: str, mig: Dict) -> List[Dict]:
    """
    Returns a list of instance selfLinks for this managed instance group.
    """

    managed_instance_self_links: List[Dict] = []

    try:
        if mig.get("zone"):
            req = compute.instanceGroupManagers().listManagedInstances(
                project=project_id,
                zone=mig["zone"],
                instanceGroupManager=mig["instanceGroupManager_name"],
            )
            res = req.execute()
        else:
            req = compute.regionInstanceGroupManagers().listManagedInstances(
                project=project_id,
                region=mig["region"],
                instanceGroupManager=mig["instanceGroupManager_name"],
            )
            res = req.execute()

        for mi in res.get("managedInstances", []):
            instance_self_link = mi.get("instance")
            if instance_self_link:
                managed_instance_self_links.append(
                    {
                        "vm_self_link": instance_self_link,
                        "mig_id": mig["id"],
                    },
                )
    except HttpError as e:
        err = json.loads(e.content.decode("utf-8")).get("error", {})
        if err.get("status", "") == "PERMISSION_DENIED" or err.get("message", "") == "Forbidden":
            logger.warning(
                "Skipping managed instances for MIG due to permissions. Project=%s MIG=%s",
                project_id,
                mig.get("id"),
            )
            return []
        raise

    return managed_instance_self_links


def _load_vm_to_mig_part_of_relationships(
    session: neo4j.Session,
    relationships: List[Dict],
    gcp_update_tag: int,
) -> None:
    session.execute_write(_load_vm_to_mig_part_of_relationships_tx, relationships, gcp_update_tag)


def _load_vm_to_mig_part_of_relationships_tx(
    tx: neo4j.Transaction,
    relationships: List[Dict],
    gcp_update_tag: int,
) -> None:
    query = """
    UNWIND $relationships AS rel
    MATCH (vm:GCPComputeInstance {self_link: rel.vm_self_link})
    MATCH (mig:GCPInstanceGroup {id: rel.mig_id})
    MERGE (vm)-[r:PART_OF]->(mig)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        query,
        relationships=relationships,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def sync_managed_instance_groups(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    zones: List[Dict],
    regions: List[str],
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Ingest Managed Instance Groups (MIGs) and connect them to their backing VMs via :PART_OF.
    """

    migs: List[Dict] = []
    migs.extend(_get_zonal_managed_instance_groups(compute, project_id, zones))
    migs.extend(_get_regional_managed_instance_groups(compute, project_id, regions))

    if migs:
        _load_managed_instance_groups(neo4j_session, migs, project_id, gcp_update_tag)

    # Create VM -> MIG relationships.
    relationships: List[Dict] = []
    for mig in migs:
        relationships.extend(_get_managed_instances_for_mig(compute, project_id, mig))

    if relationships:
        _load_vm_to_mig_part_of_relationships(neo4j_session, relationships, gcp_update_tag)

    run_cleanup_job("gcp_instance_groups_cleanup.json", neo4j_session, common_job_parameters)
