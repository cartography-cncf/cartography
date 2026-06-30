import dataclasses
import logging
from collections.abc import Callable
from enum import Enum
from typing import Any
from typing import TypeVar

from scaleway_core.api import ScalewayException

logger = logging.getLogger(__name__)

# Zone does not really matter for readonly access, but we need to set it
DEFAULT_ZONE = "fr-par-1"

# Scaleway regions. Most regional APIs (Object Storage, VPC, IPAM, Load
# Balancer, ...) list per-region, so we fan out over all of them. Not every
# service is deployed in every region; list_all_regions skips the gaps.
DEFAULT_REGIONS = ("fr-par", "nl-ams", "pl-waw", "it-mil")

T = TypeVar("T")


def list_all_regions(fetcher: Callable[..., list[T]], **kwargs: Any) -> list[T]:
    """Call a region-scoped SDK ``list_*_all`` fetcher across every region.

    Each region is passed as the ``region`` keyword. Regions where the service
    is not deployed answer with an "unknown service" error; those are skipped
    rather than aborting the whole sync.
    """
    items: list[T] = []
    for region in DEFAULT_REGIONS:
        try:
            items.extend(fetcher(region=region, **kwargs))
        except ScalewayException as exc:
            if "unknown service" in str(exc).lower():
                logger.info(
                    "Scaleway service %s not available in region %s, skipping.",
                    getattr(fetcher, "__name__", "list"),
                    region,
                )
                continue
            raise
    return items


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
    elif isinstance(element, Enum):
        return element.value
    return element
