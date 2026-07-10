import logging
from typing import Any

logger = logging.getLogger(__name__)


def extract_identity_principal_ids(identity: Any) -> list[str]:
    """
    Collect the object (principal) ids of a resource's managed identities from
    the ARM `identity` block: the system-assigned principal plus every
    user-assigned identity. These ids match an EntraServicePrincipal.id and an
    AzureRoleAssignment.principal_id, so they anchor the workload-identity
    (RUNS_AS / ASSUMES) edges. Handles both camelCase (ARM wire) and snake_case
    key spellings defensively.
    """
    if not isinstance(identity, dict):
        return []
    ids: list[str] = []
    system_pid = identity.get("principalId") or identity.get("principal_id")
    if system_pid:
        ids.append(system_pid)
    user_assigned = (
        identity.get("userAssignedIdentities")
        or identity.get("user_assigned_identities")
        or {}
    )
    if isinstance(user_assigned, dict):
        for entry in user_assigned.values():
            if isinstance(entry, dict):
                pid = entry.get("principalId") or entry.get("principal_id")
                if pid:
                    ids.append(pid)
    # Preserve order, drop duplicates.
    return list(dict.fromkeys(ids))


def get_resource_group_from_id(resource_id: str) -> str:
    """
    Helper function to parse the resource group name from a full resource ID string.
    e.g. /subscriptions/sub_id/resourceGroups/rg_name/providers/...
    """
    parts = resource_id.lower().split("/")
    rg_index = parts.index("resourcegroups")
    return parts[rg_index + 1]
