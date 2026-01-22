import logging

logger = logging.getLogger(__name__)


def transform_tags(
    resource_list: list[dict], subscription_id: str, resource_id_field: str = "id"
) -> list[dict]:
    """
    Transforms tags from a list of Azure resources into a standardized list of tag dictionaries.

    Args:
        resource_list: List of Azure resources with tags
        subscription_id: The Azure subscription ID to scope the tags
        resource_id_field: Field name containing the resource ID (default: "id")

    Returns:
        List of tag dictionaries with subscription-scoped IDs
    """
    tags_list = []
    for resource in resource_list:
        resource_id = resource.get(resource_id_field)
        tags = resource.get("tags")

        if not resource_id or not tags:
            continue

        for key, value in tags.items():
            # Generate the deterministic ID scoped to subscription: "{subscription_id}|{key}:{value}"
            tag_id = f"{subscription_id}|{key}:{value}"
            tags_list.append(
                {
                    "id": tag_id,
                    "key": key,
                    "value": value,
                    "subscription_id": subscription_id,
                    "resource_id": resource_id,
                }
            )

    return tags_list
