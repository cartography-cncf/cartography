import logging

logger = logging.getLogger(__name__)


def get_resource_group_from_id(resource_id: str) -> str:
    """
    Helper function to parse the resource group name from a full resource ID string.
    e.g. /subscriptions/sub_id/resourceGroups/rg_name/providers/...
    """
    parts = resource_id.lower().split("/")
    rg_index = parts.index("resourcegroups")
    return parts[rg_index + 1]
