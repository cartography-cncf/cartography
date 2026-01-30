# Copyright (c) 2020, Oracle and/or its affiliates.
# OCI Identity API-centric functions
# https://docs.cloud.oracle.com/iaas/Content/Identity/Concepts/overview.htm
import logging
import re
from typing import Any
from typing import Dict
from typing import List

import neo4j
import oci

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.client.core.tx import run_write_query
from cartography.util import run_cleanup_job

from . import utils

logger = logging.getLogger(__name__)


def sync_compartments(
    neo4j_session: neo4j.Session,
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Syncing IAM compartments for account '%s'.", current_tenancy_id)
    data = get_compartment_list_data(iam, current_tenancy_id)
    load_compartments(
        neo4j_session,
        data["Compartments"],
        current_tenancy_id,
        oci_update_tag,
    )
    run_cleanup_job(
        "oci_import_compartments_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


def get_compartment_list_data_recurse(
    iam: oci.identity.identity_client.IdentityClient,
    compartment_list: Dict[str, Any],
    compartment_id: str,
) -> None:

    response = oci.pagination.list_call_get_all_results(
        iam.list_compartments,
        compartment_id,
    )
    if not response.data:
        return
    compartment_list.update(
        {
            "Compartments": list(compartment_list["Compartments"])
            + utils.oci_object_to_json(response.data),
        },
    )
    for compartment in response.data:
        get_compartment_list_data_recurse(iam, compartment_list, compartment.id)


def get_compartment_list_data(
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
) -> Dict[str, Any]:
    compartment_list = {"Compartments": ""}
    get_compartment_list_data_recurse(iam, compartment_list, current_tenancy_id)
    return compartment_list


def load_compartments(
    neo4j_session: neo4j.Session,
    compartments: List[Dict[str, Any]],
    current_oci_tenancy_id: str,
    oci_update_tag: int,
) -> None:
    ingest_compartment = """
    MERGE (cnode:OCICompartment{ocid: $OCID})
    ON CREATE SET cnode:OCICompartment, cnode.firstseen = timestamp(),
    cnode.createdate = $CREATE_DATE
    SET cnode.name = $NAME, cnode.compartmentid = $COMPARTMENT_ID
    WITH cnode
    MATCH (aa) WHERE (aa:OCITenancy OR aa:OCICompartment) AND aa.ocid=$COMPARTMENT_ID
    MERGE (aa)-[r:OCI_COMPARTMENT]->(cnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for compartment in compartments:
        run_write_query(
            neo4j_session,
            ingest_compartment,
            OCID=compartment["id"],
            COMPARTMENT_ID=compartment["compartment-id"],
            DESCRIPTION=compartment["description"],
            NAME=compartment["name"],
            CREATE_DATE=compartment["time-created"],
            OCI_TENANCY_ID=current_oci_tenancy_id,
            oci_update_tag=oci_update_tag,
        )


def load_users(
    neo4j_session: neo4j.Session,
    users: List[Dict[str, Any]],
    current_oci_tenancy_id: str,
    oci_update_tag: int,
) -> None:
    ingest_user = """
    MERGE (unode:OCIUser{ocid: $OCID})
    ON CREATE SET unode:OCIUser, unode.firstseen = timestamp(),
    unode.createdate = $CREATE_DATE
    SET unode.name = $USERNAME, unode.compartmentid = $COMPARTMENT_ID, unode.description = $DESCRIPTION,
    unode.email = $EMAIL, unode.lifecycle_state = $LIFECYCLE_STATE, unode.is_mfa_activated = $IS_MFA_ACTIVATED,
    unode.can_use_api_keys = $CAN_USE_API_KEYS, unode.can_use_auth_tokens = $CAN_USE_AUTH_TOKENS,
    unode.can_use_console_password = $CAN_USE_CONSOLE_PASSWORD,
    unode.can_use_customer_secret_keys = $CAN_USE_CUSTOMER_SECRET_KEYS,
    unode.can_use_smtp_credentials = $CAN_USE_SMTP_CREDENTIALS,
    unode.lastupdated = $oci_update_tag
    WITH unode
    MATCH (aa:OCITenancy{ocid: $OCI_TENANCY_ID})
    MERGE (aa)-[r:RESOURCE]->(unode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for user in users:
        run_write_query(
            neo4j_session,
            ingest_user,
            OCID=user["id"],
            CREATE_DATE=str(user["time-created"]),
            USERNAME=user["name"],
            DESCRIPTION=user["description"],
            EMAIL=user["email"],
            LIFECYCLE_STATE=user["lifecycle-state"],
            IS_MFA_ACTIVATED=user["is-mfa-activated"],
            CAN_USE_API_KEYS=user["capabilities"]["can-use-api-keys"],
            CAN_USE_AUTH_TOKENS=user["capabilities"]["can-use-auth-tokens"],
            CAN_USE_CONSOLE_PASSWORD=user["capabilities"]["can-use-console-password"],
            CAN_USE_CUSTOMER_SECRET_KEYS=user["capabilities"][
                "can-use-customer-secret-keys"
            ],
            CAN_USE_SMTP_CREDENTIALS=user["capabilities"]["can-use-smtp-credentials"],
            COMPARTMENT_ID=user["compartment-id"],
            OCI_TENANCY_ID=current_oci_tenancy_id,
            oci_update_tag=oci_update_tag,
        )


def get_user_list_data(
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    response = oci.pagination.list_call_get_all_results(
        iam.list_users,
        current_tenancy_id,
    )
    return {"Users": utils.oci_object_to_json(response.data)}


def sync_users(
    neo4j_session: neo4j.Session,
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Syncing IAM users for account '%s'.", current_tenancy_id)
    data = get_user_list_data(iam, current_tenancy_id)
    load_users(neo4j_session, data["Users"], current_tenancy_id, oci_update_tag)
    run_cleanup_job(
        "oci_import_users_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


def get_group_list_data(
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    response = oci.pagination.list_call_get_all_results(
        iam.list_groups,
        current_tenancy_id,
    )
    return {"Groups": utils.oci_object_to_json(response.data)}


def load_groups(
    neo4j_session: neo4j.Session,
    groups: List[Dict[str, Any]],
    current_tenancy_id: str,
    oci_update_tag: int,
) -> None:
    ingest_group = """
    MERGE (gnode:OCIGroup{ocid: $OCID})
    ON CREATE SET gnode.firstseen = timestamp(), gnode.createdate = $CREATE_DATE
    SET gnode.name = $GROUP_NAME, gnode.compartmentid = $COMPARTMENT_ID, gnode.lastupdated = $oci_update_tag,
    gnode.description = $DESCRIPTION
    WITH gnode
    MATCH (aa:OCITenancy{ocid: $OCI_TENANCY_ID})
    MERGE (aa)-[r:RESOURCE]->(gnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for group in groups:
        run_write_query(
            neo4j_session,
            ingest_group,
            OCID=group["id"],
            CREATE_DATE=str(group["time-created"]),
            GROUP_NAME=group["name"],
            COMPARTMENT_ID=group["compartment-id"],
            DESCRIPTION=group["description"],
            OCI_TENANCY_ID=current_tenancy_id,
            oci_update_tag=oci_update_tag,
        )


def sync_groups(
    neo4j_session: neo4j.Session,
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Syncing IAM groups for account '%s'.", current_tenancy_id)
    data = get_group_list_data(iam, current_tenancy_id)
    load_groups(neo4j_session, data["Groups"], current_tenancy_id, oci_update_tag)
    run_cleanup_job(
        "oci_import_groups_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


def get_group_membership_data(
    iam: oci.identity.identity_client.IdentityClient,
    group_id: str,
    current_tenancy_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    response = oci.pagination.list_call_get_all_results(
        iam.list_user_group_memberships,
        compartment_id=current_tenancy_id,
        group_id=group_id,
    )
    return {"GroupMemberships": utils.oci_object_to_json(response.data)}


def sync_group_memberships(
    neo4j_session: neo4j.Session,
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Syncing IAM group membership for account '%s'.", current_tenancy_id)
    query = (
        "MATCH (group:OCIGroup)<-[:RESOURCE]-(OCITenancy{ocid: $OCI_TENANCY_ID}) "
        "return group.name as name, group.ocid as ocid;"
    )
    groups = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        query,
        OCI_TENANCY_ID=current_tenancy_id,
    )
    groups_membership = {
        group["ocid"]: get_group_membership_data(iam, group["ocid"], current_tenancy_id)
        for group in groups
    }
    load_group_memberships(neo4j_session, groups_membership, oci_update_tag)
    run_cleanup_job(
        "oci_import_groups_membership_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


def load_group_memberships(
    neo4j_session: neo4j.Session,
    group_memberships: Dict[str, Any],
    oci_update_tag: int,
) -> None:
    ingest_membership = """
    MATCH (group:OCIGroup{ocid: $GROUP_OCID})
    WITH group
    MATCH (user:OCIUser{ocid: $USER_OCID})
    MERGE (user)-[r:MEMBER_OCID_GROUP]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """
    for group_ocid, membership_data in group_memberships.items():
        for info in membership_data["GroupMemberships"]:
            run_write_query(
                neo4j_session,
                ingest_membership,
                COMPARTMENT_ID=info["compartment-id"],
                GROUP_OCID=info["group-id"],
                USER_OCID=info["user-id"],
                oci_update_tag=oci_update_tag,
            )


def load_policies(
    neo4j_session: neo4j.Session,
    policies: List[Dict[str, Any]],
    current_tenancy_id: str,
    oci_update_tag: int,
) -> None:
    ingest_policy = """
    MERGE (pnode:OCIPolicy{ocid: $OCID})
    ON CREATE SET pnode.firstseen = timestamp(), pnode.createdate = $CREATE_DATE
    SET pnode.name = $POLICY_NAME, pnode.compartmentid = $COMPARTMENT_ID, pnode.description = $DESCRIPTION,
    pnode.statements = $STATEMENTS,
    pnode.updatedate = $POLICY_UPDATE, pnode.lastupdated = $oci_update_tag
    WITH pnode
    MATCH (aa) WHERE (aa:OCITenancy OR aa:OCICompartment) AND aa.ocid=$COMPARTMENT_ID
    MERGE (aa)-[r:OCI_POLICY]->(pnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for policy in policies:
        run_write_query(
            neo4j_session,
            ingest_policy,
            OCID=policy["id"],
            POLICY_NAME=policy["name"],
            COMPARTMENT_ID=policy["compartment-id"],
            DESCRIPTION=policy["description"],
            STATEMENTS=policy["statements"],
            CREATE_DATE=str(policy["time-created"]),
            POLICY_UPDATE=str(policy["version-date"]),
            OCI_TENANCY_ID=current_tenancy_id,
            oci_update_tag=oci_update_tag,
        )


def get_policy_list_data(
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    response = oci.pagination.list_call_get_all_results(
        iam.list_policies,
        compartment_id=current_tenancy_id,
    )
    return {"Policies": utils.oci_object_to_json(response.data)}


def sync_policies(
    neo4j_session: neo4j.Session,
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Syncing IAM policies for account '%s'.", current_tenancy_id)
    compartments = utils.get_compartments_in_tenancy(neo4j_session, current_tenancy_id)
    for compartment in compartments:
        logger.debug(
            "Syncing OCI policies for compartment '%s' in account '%s'.",
            compartment["ocid"],
            current_tenancy_id,
        )
        data = get_policy_list_data(iam, compartment["ocid"])
        if data["Policies"]:
            load_policies(
                neo4j_session,
                data["Policies"],
                current_tenancy_id,
                oci_update_tag,
            )
    run_cleanup_job(
        "oci_import_policies_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


def load_oci_policy_group_reference(
    neo4j_session: neo4j.Session,
    policy_id: str,
    group_id: str,
    tenancy_id: str,
    oci_update_tag: int,
) -> None:
    ingest_policy_group_reference = """
    MATCH (aa:OCIPolicy{ocid: $POLICY_ID})
    MATCH (bb:OCIGroup{ocid: $GROUP_ID})
    MERGE (aa)-[r:OCI_POLICY_REFERENCE]->(bb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """
    run_write_query(
        neo4j_session,
        ingest_policy_group_reference,
        POLICY_ID=policy_id,
        GROUP_ID=group_id,
        oci_update_tag=oci_update_tag,
    )


def load_oci_policy_compartment_reference(
    neo4j_session: neo4j.Session,
    policy_id: str,
    compartment_id: str,
    tenancy_id: str,
    oci_update_tag: int,
) -> None:
    ingest_policy_compartment_reference = """
    MATCH (aa:OCIPolicy{ocid: $POLICY_ID})
    MATCH (bb:OCICompartment{ocid: $COMPARTMENT_ID})
    MERGE (aa)-[r:OCI_POLICY_REFERENCE]->(bb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """
    run_write_query(
        neo4j_session,
        ingest_policy_compartment_reference,
        POLICY_ID=policy_id,
        COMPARTMENT_ID=compartment_id,
        oci_update_tag=oci_update_tag,
    )


# Parse the statements inside OCI Policies and load the corresponding relationships they reference.
def sync_oci_policy_references(
    neo4j_session: neo4j.Session,
    tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    groups = list(utils.get_groups_in_tenancy(neo4j_session, tenancy_id))
    compartments = list(utils.get_compartments_in_tenancy(neo4j_session, tenancy_id))
    policies = list(utils.get_policies_in_tenancy(neo4j_session, tenancy_id))
    for policy in policies:
        check_compart = policy["compartmentid"]
        for statement in policy["statements"]:
            m = re.search("(?<=group\\s)[^ ]*(?=\\s)", statement)
            if m:
                for group in groups:
                    if group["name"].lower() == m.group(0).lower():
                        load_oci_policy_group_reference(
                            neo4j_session,
                            policy["ocid"],
                            group["ocid"],
                            tenancy_id,
                            oci_update_tag,
                        )
            m = re.search("(?<=compartment\\s)[^ ]*(?=$)", statement)
            if m:
                for compartment in compartments:
                    # Only look at the compartment or subcompartment name referenced in the policy statement
                    # in which the policy is a member of.
                    if (
                        compartment["ocid"] == check_compart
                        or compartment["compartmentid"] == check_compart
                    ):
                        if compartment["name"].lower() == m.group(0).lower():
                            load_oci_policy_compartment_reference(
                                neo4j_session,
                                policy["ocid"],
                                compartment["ocid"],
                                tenancy_id,
                                oci_update_tag,
                            )


def get_region_subscriptions_list_data(
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    response = oci.pagination.list_call_get_all_results(
        iam.list_region_subscriptions,
        current_tenancy_id,
    )
    return {"RegionSubscriptions": utils.oci_object_to_json(response.data)}


def load_region_subscriptions(
    neo4j_session: neo4j.Session,
    regions: List[Dict[str, Any]],
    tenancy_id: str,
    oci_update_tag: int,
) -> None:
    query = """
    MERGE (aa:OCIRegion{key: $REGION_KEY})
    ON CREATE SET aa.firstseen = timestamp()
    SET aa.lastupdated = $oci_update_tag, aa.name = $REGION_NAME
    WITH aa
    MATCH (bb:OCITenancy{ocid: $OCI_TENANCY_ID})
    MERGE (bb)-[r:OCI_REGION_SUBSCRIPTION]->(aa)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """
    for region in regions:
        run_write_query(
            neo4j_session,
            query,
            REGION_KEY=region["region-key"],
            REGION_NAME=region["region-name"],
            oci_update_tag=oci_update_tag,
            OCI_TENANCY_ID=tenancy_id,
        )


def sync_region_subscriptions(
    neo4j_session: neo4j.Session,
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug(
        "Syncing IAM region subscriptions for account '%s'.",
        current_tenancy_id,
    )
    data = get_region_subscriptions_list_data(iam, current_tenancy_id)
    load_region_subscriptions(
        neo4j_session,
        data["RegionSubscriptions"],
        current_tenancy_id,
        oci_update_tag,
    )
    # run_cleanup_job('oci_import_region_subscriptions_cleanup.json', neo4j_session, common_job_parameters)


def sync(
    neo4j_session: neo4j.Session,
    iam: oci.identity.identity_client.IdentityClient,
    tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.info("Syncing IAM for account '%s'.", tenancy_id)
    sync_users(neo4j_session, iam, tenancy_id, oci_update_tag, common_job_parameters)
    sync_groups(neo4j_session, iam, tenancy_id, oci_update_tag, common_job_parameters)
    sync_group_memberships(
        neo4j_session,
        iam,
        tenancy_id,
        oci_update_tag,
        common_job_parameters,
    )
    sync_compartments(
        neo4j_session,
        iam,
        tenancy_id,
        oci_update_tag,
        common_job_parameters,
    )
    sync_policies(neo4j_session, iam, tenancy_id, oci_update_tag, common_job_parameters)
    sync_oci_policy_references(
        neo4j_session,
        tenancy_id,
        oci_update_tag,
        common_job_parameters,
    )
    sync_region_subscriptions(
        neo4j_session,
        iam,
        tenancy_id,
        oci_update_tag,
        common_job_parameters,
    )
