import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

logger = logging.getLogger(__name__)


def get_opal_groups_to_okta_groups_map(groups: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Create a map of Opal Groups to their Okta groups using the remote_info field.
    """
    logger.info("Mapping opal groups to okta groups")

    opal_to_okta_map = {}
    for group in groups:
        opal_group_id = group.get('group_id')
        okta_group_info = group.get('remote_info', {}).get('okta_group', {})
        okta_group_id = okta_group_info.get('group_id')
        if opal_group_id and okta_group_id:
            opal_to_okta_map[opal_group_id] = okta_group_id
    return opal_to_okta_map


def get_manual_approved_access(
    request_config: Dict[str, Any],
    opal_admin_to_okta_map: Dict[str, str],
    resource_id: str,
) -> List[Dict[str, Any]]:
    """
    Return manual approved access in an OpalResource that is tied back to the OktaGroup that has manual approval.
    """
    manual_approved_access = []
    request_stages = request_config.get('reviewer_stages', {})
    for stage in request_stages:
        owner_ids = stage.get('owner_ids', [])
        for owner_id in owner_ids:
            okta_group_id = opal_admin_to_okta_map.get(owner_id)
            if okta_group_id:
                manual_approved_access.append({
                    'resource_id': resource_id,
                    'okta_group_id': okta_group_id,
                    'num_of_approvals': len(request_stages),
                })
    return manual_approved_access


def get_auto_approved_access(
    request_config: Dict[str, Any],
    opal_to_okta_map: Dict[str, str],
    resource_id: str,
) -> List[Dict[str, Any]]:
    """
    Return auto approved access in an OpalResource that is tied back to the OktaGroup that has auto-approved access.
    """
    auto_approved_access = []
    group_ids = request_config.get("condition", {}).get('group_ids', [])
    for group_id in group_ids:
        okta_group_id = opal_to_okta_map.get(group_id)
        if okta_group_id:
            auto_approved_access.append({
                'resource_id': resource_id,
                'okta_group_id': okta_group_id,
            })
    return auto_approved_access


def parse_opal_resource_access_configuration(
        opal_resources: List[Dict[str, Any]],
        opal_to_okta_map: Dict[str, str],
        opal_admin_to_okta_map: Dict[str, str],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Return auto approved access in an OpalResource that is tied back to the OktaGroup that has autoapproved access.
    """
    logger.info(f"Getting auto approved and manual approved access for {len(opal_resources)} opal resources")
    auto_approved_access = []
    manual_approved_access = []
    for resource in opal_resources:
        resource_id: str = str(resource.get('resource_id', ""))
        for request_config in resource.get('request_configurations', []):
            if request_config.get('auto_approval'):
                auto_approved_access.extend(
                    get_auto_approved_access(
                        request_config, opal_to_okta_map, resource_id,
                    ),
                )
            else:
                # If there is no auto approval, then there is manual approval.
                manual_approved_access.extend(
                    get_manual_approved_access(
                        request_config, opal_admin_to_okta_map, resource_id,
                    ),
                )
    return auto_approved_access, manual_approved_access


def load_auto_approved_access(neo4j_session: Any, update_tag: int, auto_approved_access: List[Dict[str, Any]]) -> None:
    """
    Load the auto approved access relationships into the graph.
    """
    logger.info(f"Loading {len(auto_approved_access)} auto approved access relationships")
    neo4j_session.run(
        """
        UNWIND $auto_approved_access AS access
        MATCH (opal_resource:OpalResource {id: access.resource_id})
        MATCH (okta_group:OktaGroup {id: access.okta_group_id})
        MERGE (okta_group)-[r:CAN_AUTO_APPROVE_ACCESS]->(opal_resource)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        """,
        auto_approved_access=auto_approved_access, update_tag=update_tag,
    )


def load_manual_approvers(neo4j_session: Any, update_tag: int, manual_approved_access: List[Dict[str, Any]]) -> None:
    """
    Load the mapping of OktaGroup to OpalResources they can manually approve access for into Neo4j.
    """
    logger.info(f"Loading {len(manual_approved_access)} manual approved access relationships")
    neo4j_session.run(
        """
        UNWIND $manual_approved_access AS access
        MATCH (g:OktaGroup {id: access.okta_group_id})
        MATCH (r:OpalResource {id: access.resource_id})
        MERGE (g)-[rel:CAN_MANUALLY_APPROVE_ACCESS]->(r)
        ON CREATE SET rel.firstseen = timestamp()
        SET rel.lastupdated = $update_tag,
        rel.num_of_approvals = access.num_of_approvals
        """,
        manual_approved_access=manual_approved_access,
        update_tag=update_tag,
    )
