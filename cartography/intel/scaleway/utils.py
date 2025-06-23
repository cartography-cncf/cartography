import dataclasses
from typing import Any

# Zone does not really matter for readonly access, but we need to set it
DEFAULT_ZONE = "fr-par-1"


def scaleway_obj_to_dict(obj: Any) -> dict[str, Any]:
    """Transform a Scaleway object (dataclass, dict, or list) into a dictionary."""
    if isinstance(obj, type) or not dataclasses.is_dataclass(obj):
        raise TypeError(f"Expected a dataclass, got {type(obj).__name__} instead.")
    result: dict[str, Any] = dataclasses.asdict(obj)

    for k in list(result.keys()):
        result[k] = _scaleway_element_sanitize(result[k])
    return result


def _scaleway_element_sanitize(element: Any) -> Any:
    """Sanitize a Scaleway element by removing empty strings and lists."""
    if isinstance(element, str) and element == "":
        return None
    elif isinstance(element, list):
        if len(element) == 0:
            return None
        return [
            _scaleway_element_sanitize(item) for item in element if item is not None
        ]
    elif isinstance(element, dict):
        return {
            k: _scaleway_element_sanitize(v)
            for k, v in element.items()
            if v is not None
        }
    elif dataclasses.is_dataclass(element):
        return scaleway_obj_to_dict(element)
    return element
