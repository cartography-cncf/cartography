import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any

from dateutil.parser import parse as parse_date

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeSchema

logger = logging.getLogger(__name__)


def data_dict_cleanup(
    node_schema: CartographyNodeSchema, data: dict[str, Any]
) -> dict[str, Any]:
    """This function cleans up a data dictionary based on the provided node schema.

    This function will remove any keys that are not defined in the node schema,
    and will also auto-format the values according to the `auto_format` specified in the
    `PropertyRef` of the node schema.

    :param node_schema: The schema defining the properties and structure of the node.
    :type node_schema: CartographyNodeSchema
    :param data: The data dictionary to be cleaned up.
    :type data: dict[str, Any]
    :return: A cleaned-up dictionary containing only the properties defined in the node schema,
             with values auto-formatted according to the schema's `PropertyRef` definitions.
    :rtype: dict[str, Any]
    """
    keys = _node_schema_to_property_refs(node_schema)
    return _recursive_cleanup(data, keys)


def _recursive_cleanup(data: dict, keys: dict[str, PropertyRef]) -> dict:
    """This function recursively cleans up a data dictionary based on the provided keys."""
    cleaned_data = {}
    sub_dicts_keys: dict[str, dict[str, PropertyRef]] = {}

    for key, p_ref in keys.items():
        if p_ref.set_in_kwargs:
            continue  # Skip keys that are set in kwargs, not in the data dict
        # Check if the key is a simple key (not nested)
        if "." not in key:
            if key not in data:
                continue
            cleaned_data[key] = _auto_format_field(p_ref, data[key])
        else:
            # If it's a nested key, split it into prefix and suffix
            prefix, suffix = key.split(".", 1)
            if data.get(prefix) is None:
                continue
            sub_dicts_keys.setdefault(prefix, {})[suffix] = p_ref
    # Now we can handle the sub-dictionaries
    for prefix, suffixes in sub_dicts_keys.items():
        sub_result = _recursive_cleanup(data[prefix], suffixes)
        if len(sub_result) > 0:
            cleaned_data[prefix] = sub_result
    return cleaned_data


def _node_schema_to_property_refs(
    node_schema: CartographyNodeSchema,
) -> dict[str, PropertyRef]:
    """This function extracts property references from a CartographyNodeSchema.
    It collects all properties defined in the node schema, including those in sub-resource relationships
    and other relationships, and returns them as a dictionary where the keys are property names
    and the values are PropertyRef instances."""
    results: dict[str, PropertyRef] = {}

    for p_ref in asdict(node_schema.properties).values():
        results[p_ref.name] = p_ref

    if node_schema.sub_resource_relationship:
        for p_ref in asdict(node_schema.sub_resource_relationship.properties).values():
            results[p_ref.name] = p_ref
        for p_ref in asdict(
            node_schema.sub_resource_relationship.target_node_matcher
        ).values():
            results[p_ref.name] = p_ref

    if node_schema.other_relationships:
        for rel in node_schema.other_relationships.rels:
            for p_ref in asdict(rel.properties).values():
                results[p_ref.name] = p_ref
            for p_ref in asdict(rel.target_node_matcher).values():
                results[p_ref.name] = p_ref

    return results


def _auto_format_field(p_ref: PropertyRef, value: Any) -> Any:
    """This function auto-formats a field based on the PropertyRef's auto_format type."""
    try:
        if value is None:
            return None
        if p_ref.auto_format is None:
            return value
        if p_ref.auto_format == str:
            value = str(value)
            if len(value) == 0:
                return None
            return value
        if p_ref.auto_format == int:
            return int(value)
        if p_ref.auto_format == float:
            return float(value)
        if p_ref.auto_format == dict or p_ref.auto_format == list:
            if len(value) == 0:
                return None
            return value
        if p_ref.auto_format == datetime:
            if isinstance(value, datetime):
                return value
            if isinstance(value, int) or isinstance(value, float):
                return datetime.fromtimestamp(value)
            return parse_date(value)
        if p_ref.auto_format == bool:
            if isinstance(value, str):
                if value.lower() in ("true", "1", "yes"):
                    return True
                if value.lower() in ("false", "0", "no"):
                    return False
                return value
            if isinstance(value, bool):
                return value
            if isinstance(value, int):
                return bool(value)
            raise ValueError(f"Cannot convert {value} to bool")
    # Handling broad exceptions is generally discouraged, but here we log the error
    # and return a string representation of the value to avoid breaking the data flow.
    except Exception as e:
        logger.warning("Error formatting field '%s': %s.", p_ref, e)
        # If any error occurs, we fallback to string representation
        return str(value)
