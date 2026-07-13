import json
import logging
import re
from typing import Any

import neo4j

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.tailscale.deviceposture import (
    TailscaleDeviceToPostureConditionMatchLink,
)
from cartography.models.tailscale.deviceposture import TailscaleDeviceToPostureMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)

MATCHLINK_SUB_RESOURCE_LABEL = "TailscaleTailnet"
TAILSCALE_VERSION_ATTRIBUTES = {
    "node:osVersion",
    "node:tsVersion",
}


@timeit
def sync(
    neo4j_session: neo4j.Session,
    org: str,
    update_tag: int,
    postures: list[dict[str, Any]],
    posture_conditions: list[dict[str, Any]],
    device_posture_attributes: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    posture_resolution = get(
        postures,
        posture_conditions,
        device_posture_attributes,
    )
    condition_matches, posture_matches = transform(posture_resolution)
    load(
        neo4j_session,
        org,
        update_tag,
        condition_matches,
        posture_matches,
    )
    cleanup(
        neo4j_session,
        org,
        update_tag,
    )
    return posture_matches


@timeit
def get(
    postures: list[dict[str, Any]],
    posture_conditions: list[dict[str, Any]],
    device_posture_attributes: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    return resolve_posture_compliance(
        postures,
        posture_conditions,
        device_posture_attributes,
    )


def transform(
    posture_resolution: tuple[list[dict[str, str]], list[dict[str, str]]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    return posture_resolution


def load(
    neo4j_session: neo4j.Session,
    org: str,
    update_tag: int,
    condition_matches: list[dict[str, str]],
    posture_matches: list[dict[str, str]],
) -> None:

    if condition_matches:
        load_matchlinks(
            neo4j_session,
            TailscaleDeviceToPostureConditionMatchLink(),
            condition_matches,
            lastupdated=update_tag,
            _sub_resource_label=MATCHLINK_SUB_RESOURCE_LABEL,
            _sub_resource_id=org,
        )

    if posture_matches:
        load_matchlinks(
            neo4j_session,
            TailscaleDeviceToPostureMatchLink(),
            posture_matches,
            lastupdated=update_tag,
            _sub_resource_label=MATCHLINK_SUB_RESOURCE_LABEL,
            _sub_resource_id=org,
        )


def cleanup(
    neo4j_session: neo4j.Session,
    org: str,
    update_tag: int,
) -> None:
    GraphJob.from_matchlink(
        TailscaleDeviceToPostureConditionMatchLink(),
        MATCHLINK_SUB_RESOURCE_LABEL,
        org,
        update_tag,
    ).run(neo4j_session)
    GraphJob.from_matchlink(
        TailscaleDeviceToPostureMatchLink(),
        MATCHLINK_SUB_RESOURCE_LABEL,
        org,
        update_tag,
    ).run(neo4j_session)


def resolve_posture_compliance(
    postures: list[dict[str, Any]],
    posture_conditions: list[dict[str, Any]],
    device_posture_attributes: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    conditions_by_posture: dict[str, list[dict[str, Any]]] = {}
    for condition in posture_conditions:
        conditions_by_posture.setdefault(condition["posture_id"], []).append(condition)

    condition_matches: list[dict[str, str]] = []
    posture_matches: list[dict[str, str]] = []

    for device_id, attributes in device_posture_attributes.items():
        matched_condition_ids: set[str] = set()

        for condition in posture_conditions:
            if device_matches_condition(attributes, condition):
                matched_condition_ids.add(condition["id"])
                condition_matches.append(
                    {
                        "device_id": device_id,
                        "condition_id": condition["id"],
                    },
                )

        for posture in postures:
            posture_condition_ids = {
                condition["id"]
                for condition in conditions_by_posture.get(posture["id"], [])
            }
            if posture_condition_ids and posture_condition_ids.issubset(
                matched_condition_ids,
            ):
                posture_matches.append(
                    {
                        "device_id": device_id,
                        "posture_id": posture["id"],
                    },
                )

    logger.info(
        "Resolved %d condition compliance links and %d posture compliance links",
        len(condition_matches),
        len(posture_matches),
    )
    return condition_matches, posture_matches


def device_matches_condition(
    device_attributes: dict[str, Any],
    condition: dict[str, Any],
) -> bool:
    attribute_name = condition["name"]
    operator = condition["operator"].upper()

    if operator == "IS SET":
        return (
            attribute_name in device_attributes
            and device_attributes[attribute_name] is not None
        )
    if operator == "NOT SET":
        return (
            attribute_name not in device_attributes
            or device_attributes[attribute_name] is None
        )

    if attribute_name not in device_attributes:
        return False

    actual_value = device_attributes[attribute_name]
    expected_value = _parse_expected_value(condition["value"])

    if operator == "IN":
        if not isinstance(expected_value, list):
            return False
        return actual_value in expected_value
    if operator == "NOT IN":
        if not isinstance(expected_value, list):
            return False
        return actual_value not in expected_value
    if operator == "==":
        return (
            _compare_values(
                actual_value,
                expected_value,
                attribute_name=attribute_name,
            )
            == 0
        )
    if operator == "!=":
        return (
            _compare_values(
                actual_value,
                expected_value,
                attribute_name=attribute_name,
            )
            != 0
        )
    if operator == ">":
        return (
            _compare_values(
                actual_value,
                expected_value,
                attribute_name=attribute_name,
            )
            > 0
        )
    if operator == ">=":
        return (
            _compare_values(
                actual_value,
                expected_value,
                attribute_name=attribute_name,
            )
            >= 0
        )
    if operator == "<":
        return (
            _compare_values(
                actual_value,
                expected_value,
                attribute_name=attribute_name,
            )
            < 0
        )
    if operator == "<=":
        return (
            _compare_values(
                actual_value,
                expected_value,
                attribute_name=attribute_name,
            )
            <= 0
        )

    logger.debug("Unsupported Tailscale posture operator %s", operator)
    return False


def _parse_expected_value(value: Any) -> Any:
    if value is None:
        return None

    normalized = value.strip()
    if not normalized:
        return None

    if normalized.lower() == "true":
        return True
    if normalized.lower() == "false":
        return False

    if normalized.startswith("["):
        return json.loads(normalized)

    if re.fullmatch(r"-?\d+", normalized):
        return int(normalized)
    if re.fullmatch(r"-?\d+\.\d+", normalized):
        return float(normalized)

    return normalized


def _compare_values(
    left: Any,
    right: Any,
    *,
    attribute_name: str | None = None,
) -> int:
    left_value, right_value = _normalize_comparison_pair(
        left,
        right,
        attribute_name=attribute_name,
    )
    if left_value < right_value:
        return -1
    if left_value > right_value:
        return 1
    return 0


def _normalize_comparison_pair(
    left: Any,
    right: Any,
    *,
    attribute_name: str | None = None,
) -> tuple[Any, Any]:
    if isinstance(left, bool) or isinstance(right, bool):
        return bool(left), bool(right)

    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left, right

    left_string = str(left)
    right_string = str(right)
    if (
        attribute_name in TAILSCALE_VERSION_ATTRIBUTES
        and isinstance(left, str)
        and isinstance(right, str)
    ):
        return _version_key(left_string), _version_key(right_string)

    return left_string, right_string


def _version_key(value: str) -> tuple[Any, ...]:
    version = value.lstrip("v")
    fields: list[Any] = []
    remaining = version
    while remaining:
        non_numeric, remaining = _split_prefix(remaining, numeric=False)
        if non_numeric or not fields:
            fields.append(non_numeric)
        numeric, remaining = _split_prefix(remaining, numeric=True)
        if numeric:
            fields.append(int(numeric))
        elif not remaining:
            fields.append(0)
    if not fields:
        return ("", 0)
    return tuple(fields)


def _split_prefix(value: str, *, numeric: bool) -> tuple[str, str]:
    for index, character in enumerate(value):
        is_numeric = character.isdigit()
        if is_numeric != numeric:
            return value[:index], value[index:]
    return value, ""
