"""
Data sanitization and formatting utilities for Cartography node schemas.

This module provides functionality to clean up and format data dictionaries based on 
CartographyNodeSchema definitions. It ensures that data conforms to the expected 
structure and types defined in the schema, while automatically formatting values 
according to their PropertyRef specifications.

The main functionality includes:
- Filtering data to include only schema-defined properties
- Automatic type conversion and formatting based on PropertyRef settings
- Recursive handling of nested data structures
- Error-resilient data processing with fallback mechanisms
"""

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
    """
    Clean up and sanitize a data dictionary based on a CartographyNodeSchema.

    This function performs comprehensive data sanitization by:
    1. Filtering out properties not defined in the node schema
    2. Auto-formatting values according to their PropertyRef specifications
    3. Handling nested data structures recursively
    4. Ensuring data consistency and type safety

    Args:
        node_schema (CartographyNodeSchema): The schema defining the expected 
            properties and structure of the node. This schema contains PropertyRef 
            definitions that specify how each field should be formatted.
        data (dict[str, Any]): The raw data dictionary to be cleaned up. This 
            may contain extra fields, incorrectly typed values, or nested structures
            that need to be sanitized.

    Returns:
        dict[str, Any]: A cleaned-up dictionary containing only the properties 
            defined in the node schema, with values auto-formatted according to 
            the schema's PropertyRef definitions. Nested objects are recursively 
            processed.

    Example:
        >>> from cartography.models.core.nodes import CartographyNodeSchema
        >>> from cartography.models.core.common import PropertyRef
        >>> 
        >>> # Assuming we have a schema with auto_format specifications
        >>> schema = CartographyNodeSchema(...)
        >>> raw_data = {
        ...     "id": "123",
        ...     "created_at": "2023-01-01T00:00:00Z",
        ...     "is_active": "true",
        ...     "extra_field": "should_be_removed"
        ... }
        >>> cleaned = data_dict_cleanup(schema, raw_data)
        >>> # Result contains only schema-defined fields with proper types
    """
    keys = _node_schema_to_property_refs(node_schema)
    return _recursive_cleanup(data, keys)


def _recursive_cleanup(data: dict, keys: dict[str, PropertyRef]) -> dict:
    """
    Recursively clean up a data dictionary based on provided property references.
    
    This function handles both simple properties and nested data structures by:
    - Processing simple keys directly with auto-formatting
    - Identifying nested keys (containing dots) and grouping them by prefix
    - Recursively processing nested dictionaries
    
    Args:
        data (dict): The data dictionary to clean up. Can contain both simple 
            key-value pairs and nested dictionaries.
        keys (dict[str, PropertyRef]): A mapping of property names to their 
            PropertyRef definitions. Nested properties are represented with 
            dot notation (e.g., "address.street").
    
    Returns:
        dict: A cleaned dictionary containing only the specified properties,
            with nested structures properly processed.
            
    Note:
        This function preserves the original data structure while filtering
        and formatting according to the provided property references.
    """
    cleaned_data = {}
    sub_dicts_keys: dict[str, dict[str, PropertyRef]] = {}

    for key, p_ref in keys.items():
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
    """
    Extract property references from a CartographyNodeSchema.
    
    This function comprehensively collects PropertyRef definitions from all parts
    of a node schema, including:
    - Direct node properties
    - Sub-resource relationship properties and target node matchers
    - Other relationship properties and target node matchers
    
    Properties marked with `set_in_kwargs=True` are excluded as they are 
    typically handled separately in the data processing pipeline.
    
    Args:
        node_schema (CartographyNodeSchema): The schema to extract properties from.
            This schema may contain various types of relationships and property
            definitions.
    
    Returns:
        dict[str, PropertyRef]: A mapping of property names to their PropertyRef
            definitions. The keys are property names and values are PropertyRef
            instances containing formatting and validation rules.
            
    Note:
        This function flattens the hierarchical schema structure into a single
        dictionary for easier processing during data cleanup.
    """
    results: dict[str, PropertyRef] = {}

    for p_ref in asdict(node_schema.properties).values():
        if p_ref.set_in_kwargs:
            continue
        results[p_ref.name] = p_ref

    if node_schema.sub_resource_relationship:
        for p_ref in asdict(node_schema.sub_resource_relationship.properties).values():
            if p_ref.set_in_kwargs:
                continue
            results[p_ref.name] = p_ref
        for p_ref in asdict(
            node_schema.sub_resource_relationship.target_node_matcher
        ).values():
            if p_ref.set_in_kwargs:
                continue
            results[p_ref.name] = p_ref

    if node_schema.other_relationships:
        for rel in node_schema.other_relationships.rels:
            for p_ref in asdict(rel.properties).values():
                if p_ref.set_in_kwargs:
                    continue
                results[p_ref.name] = p_ref
            for p_ref in asdict(rel.target_node_matcher).values():
                if p_ref.set_in_kwargs:
                    continue
                results[p_ref.name] = p_ref

    return results


def _auto_format_field(p_ref: PropertyRef, value: Any) -> Any:
    """
    Auto-format a field value based on its PropertyRef specification.
    
    This function performs type conversion and formatting based on the `auto_format`
    attribute of the PropertyRef. It handles various data types including:
    - String conversion with empty string handling
    - Numeric conversions (int, float)
    - DateTime parsing from multiple formats (timestamps, ISO strings)
    - Boolean conversion with multiple string representations
    - Collection types (dict, list) with empty value handling
    
    Args:
        p_ref (PropertyRef): The property reference containing formatting rules.
            The `auto_format` attribute specifies the target type for conversion.
        value (Any): The raw value to be formatted. Can be of any type.
    
    Returns:
        Any: The formatted value according to the PropertyRef specification.
            Returns None for empty strings, empty collections, or null values.
            On formatting errors, returns a string representation as fallback.
    
    Raises:
        ValueError: When boolean conversion fails for unsupported value types.
        
    Examples:
        >>> # String conversion
        >>> p_ref = PropertyRef(auto_format=str)
        >>> _auto_format_field(p_ref, 123) == "123"
        
        >>> # DateTime conversion from timestamp
        >>> p_ref = PropertyRef(auto_format=datetime)
        >>> result = _auto_format_field(p_ref, 1640995200)
        >>> isinstance(result, datetime)
        
        >>> # Boolean conversion from string
        >>> p_ref = PropertyRef(auto_format=bool)
        >>> _auto_format_field(p_ref, "true") == True
        >>> _auto_format_field(p_ref, "false") == False
        
    Note:
        This function is designed to be error-resilient. If any conversion fails,
        it logs a warning and returns a string representation of the value to
        prevent data pipeline failures.
    """
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
                logger.warning(
                    "Cannot convert string '%s' to bool. Falling back to string.",
                    value,
                )
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
