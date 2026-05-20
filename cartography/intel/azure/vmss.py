import logging
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.compute import ComputeManagementClient

logger = logging.getLogger(__name__)


def _get_vm_scale_set_vms_part_of_relations(
    client: ComputeManagementClient,
    vm_scale_sets_list: List[Dict],
    subscription_id: str,
) -> List[Dict]:
    """
    Fetch VMSS instances and build VM->VMSS relationship payload.

    Relationship payload items:
      - vm_id: AzureVirtualMachine resource id
      - vmss_id: AzureVirtualMachineScaleSet resource id
    """

    relations: List[Dict] = []
    for vm_scale_set in vm_scale_sets_list:
        try:
            vms = list(
                map(
                    lambda x: x.as_dict(),
                    client.virtual_machine_scale_set_vms.list(
                        resource_group_name=vm_scale_set["resource_group"],
                        vm_scale_set_name=vm_scale_set["name"],
                    ),
                ),
            )
            for vm in vms:
                vm_id = vm.get("id")
                if vm_id:
                    relations.append({"vm_id": vm_id, "vmss_id": vm_scale_set["id"]})
        except HttpResponseError as e:
            logger.warning(
                "Error while retrieving VMSS instances (subscription=%s, vmss=%s). Error=%s",
                subscription_id,
                vm_scale_set.get("id"),
                e,
            )

    return relations


def _load_vm_scale_set_vms_part_of_relationships_tx(
    tx: neo4j.Transaction,
    relations: List[Dict],
    update_tag: int,
) -> None:
    ingest_part_of = """
    UNWIND $relations AS rel
    MATCH (vm:AzureVirtualMachine {id: rel.vm_id})
    MATCH (vmss:AzureVirtualMachineScaleSet {id: rel.vmss_id})
    MERGE (vm)-[r:PART_OF]->(vmss)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_part_of,
        relations=relations,
        update_tag=update_tag,
    )


def sync_vm_scale_sets_vms_part_of_relationships(
    neo4j_session: neo4j.Session,
    client: ComputeManagementClient,
    vm_scale_sets_list: List[Dict],
    update_tag: int,
    subscription_id: str,
) -> None:
    """
    Ingest VMSS instances and create VM->VMSS `:PART_OF` relationships.
    """

    relations = _get_vm_scale_set_vms_part_of_relations(
        client=client,
        vm_scale_sets_list=vm_scale_sets_list,
        subscription_id=subscription_id,
    )
    if not relations:
        return

    neo4j_session.execute_write(
        _load_vm_scale_set_vms_part_of_relationships_tx,
        relations,
        update_tag,
    )
