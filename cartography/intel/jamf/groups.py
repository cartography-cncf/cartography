import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.intel.jamf.tenant import load_tenant
from cartography.intel.jamf.util import call_jamf_api
from cartography.intel.jamf.util import get_http_status_code
from cartography.intel.jamf.util import get_paginated_jamf_results
from cartography.intel.jamf.util import normalize_group_id
from cartography.models.jamf.computergroup import JamfComputerGroupSchema
from cartography.models.jamf.mobiledevicegroup import JamfMobileDeviceGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(
    api_session: requests.Session,
    jamf_base_uri: str,
) -> list[dict[str, Any]]:
    try:
        return get_paginated_jamf_results(
            "/api/v1/groups",
            jamf_base_uri,
            api_session,
        )
    except requests.HTTPError as err:
        if get_http_status_code(err) not in {404, 405}:
            raise

        logger.info(
            "Jamf: /api/v1/groups unavailable; falling back to legacy Classic API group endpoints.",
        )
        classic_groups = call_jamf_api(
            "/computergroups",
            jamf_base_uri,
            api_session,
        ).get("computer_groups", [])
        try:
            classic_mobile_groups = call_jamf_api(
                "/mobiledevicegroups",
                jamf_base_uri,
                api_session,
            ).get("mobile_device_groups", [])
        except requests.HTTPError as mobile_err:
            if get_http_status_code(mobile_err) not in {404, 405}:
                raise
            logger.info(
                "Jamf: Classic mobile device groups endpoint unavailable; skipping mobile groups in legacy fallback.",
            )
            classic_mobile_groups = []
        return [
            {
                "groupDescription": None,
                "groupJamfProId": group["id"],
                "groupName": group["name"],
                "groupType": "COMPUTER",
                "membershipCount": None,
                "smart": group.get("is_smart"),
            }
            for group in classic_groups
        ] + [
            {
                "groupDescription": None,
                "groupJamfProId": group["id"],
                "groupName": group["name"],
                "groupType": "MOBILE",
                "membershipCount": None,
                "smart": group.get("is_smart"),
            }
            for group in classic_mobile_groups
        ]


def transform(
    api_result: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    computer_groups: list[dict[str, Any]] = []
    mobile_device_groups: list[dict[str, Any]] = []
    for group in api_result:
        transformed_group = {
            "id": normalize_group_id(group["groupJamfProId"]),
            "name": group.get("groupName"),
            "description": group.get("groupDescription"),
            "membership_count": group.get("membershipCount"),
            "is_smart": group.get("smart"),
        }
        if group.get("groupType") == "MOBILE":
            mobile_device_groups.append(transformed_group)
        else:
            computer_groups.append(transformed_group)
    return computer_groups, mobile_device_groups


def load_groups(
    neo4j_session: neo4j.Session,
    computer_groups: list[dict[str, Any]],
    mobile_device_groups: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load_tenant(neo4j_session, tenant_id, update_tag)
    if computer_groups:
        load(
            neo4j_session,
            JamfComputerGroupSchema(),
            computer_groups,
            lastupdated=update_tag,
            TENANT_ID=tenant_id,
        )
    if mobile_device_groups:
        load(
            neo4j_session,
            JamfMobileDeviceGroupSchema(),
            mobile_device_groups,
            lastupdated=update_tag,
            TENANT_ID=tenant_id,
        )


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(JamfComputerGroupSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        JamfMobileDeviceGroupSchema(),
        common_job_parameters,
    ).run(neo4j_session)

    # DEPRECATED: remove orphaned pre-migration computer groups without RESOURCE rel.
    run_write_query(
        neo4j_session,
        """
        MATCH (n:JamfComputerGroup)
        WHERE n.lastupdated <> $UPDATE_TAG
          AND NOT (n)<-[:RESOURCE]-(:JamfTenant)
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n
        """,
        UPDATE_TAG=common_job_parameters["UPDATE_TAG"],
        LIMIT_SIZE=100,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    jamf_base_uri: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_data = get(api_session, jamf_base_uri)
    computer_groups, mobile_device_groups = transform(raw_data)
    load_groups(
        neo4j_session,
        computer_groups,
        mobile_device_groups,
        jamf_base_uri,
        update_tag,
    )
    cleanup(neo4j_session, common_job_parameters)
