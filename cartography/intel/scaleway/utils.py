from typing import Any

# Zone does not really matter for readonly access, but we need to set it
DEFAULT_ZONE = "fr-par-1"


def scaleway_obj_to_dict(obj: Any) -> dict[str, Any]:
    # DOC
    result: dict[str, Any] = obj.__dict__
    # Remove empty string
    for k in list(result.keys()):
        if isinstance(result[k], str) and result[k] == "":
            result.pop(k)
        elif isinstance(result[k], list) and len(result[k]) == 0:
            result.pop(k)
    return result
