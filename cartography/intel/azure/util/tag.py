import logging

logger = logging.getLogger(__name__)


def transform_tags(
    resource_list: list[dict], resource_id_field: str = "id"
) -> list[dict]:
    """
    Transforms tags from a list of Azure resources into a standardized list of tag dictionaries.
    """
    tags_list = []
    for resource in resource_list:
        resource_id = resource.get(resource_id_field)
        tags = resource.get("tags")

        if not resource_id or not tags:
            continue

        for key, value in tags.items():
            # Generate the deterministic ID: "key:value"
            tag_id = f"{key}:{value}"
            tags_list.append(
                {
                    "id": tag_id,
                    "key": key,
                    "value": value,
                    "resource_id": resource_id,
                }
            )

    return tags_list
