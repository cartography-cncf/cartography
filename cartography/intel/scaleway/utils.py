from typing import Any

def scaleway_obj_to_dict(obj: Any) -> dict[str, Any]:
    # DOC
    result: dict[str, Any] = obj.__dict__
    # Remove empty string
    for k in list(result.keys()):
        if isinstance(result[k], str) and result[k] == 0:
            result.pop(k)
    return result
