import logging
import re
from typing import Any

import neo4j
import oci

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.oci.compartment import OCICompartmentSchema
from cartography.models.oci.group import OCIGroupSchema
from cartography.models.oci.group import OCIGroupWithMembersSchema
from cartography.models.oci.policy import OCIPolicySchema
from cartography.models.oci.policy import OCIPolicyWithReferencesSchema
from cartography.models.oci.region import OCIRegionSchema
from cartography.models.oci.user import OCIUserSchema
from cartography.util import timeit

from . import utils

logger = logging.getLogger(__name__)


def _normalize_oci_keys(data: dict[str, Any]) -> dict[str, Any]:
    """
    Transform OCI API response keys from hyphenated to underscored format.
    For example: 'compartment-id' becomes 'compartment_id'.
    """
    return {key.replace("-", "_"): value for key, value in data.items()}


@timeit
def get_compartment_list_data_recurse(
    iam: oci.identity.identity_client.IdentityClient,
    compartment_list: dict[str, Any],
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


@timeit
def get_compartment_list_data(
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
) -> dict[str, Any]:
    compartment_list: dict[str, Any] = {"Compartments": []}
    get_compartment_list_data_recurse(iam, compartment_list, current_tenancy_id)
    return compartment_list


def transform_compartments(
    compartments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Transform compartments data to use underscored keys.
    """
    return [_normalize_oci_keys(c) for c in compartments]


@timeit
def load_compartments(
    neo4j_session: neo4j.Session,
    compartments: list[dict[str, Any]],
    current_oci_tenancy_id: str,
    oci_update_tag: int,
) -> None:
    load(
        neo4j_session,
        OCICompartmentSchema(),
        compartments,
        lastupdated=oci_update_tag,
        OCI_TENANCY_ID=current_oci_tenancy_id,
    )


@timeit
def sync_compartments(
    neo4j_session: neo4j.Session,
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Syncing IAM compartments for account '%s'.", current_tenancy_id)
    data = get_compartment_list_data(iam, current_tenancy_id)
    transformed = transform_compartments(data["Compartments"])
    load_compartments(
        neo4j_session,
        transformed,
        current_tenancy_id,
        oci_update_tag,
    )
    GraphJob.from_node_schema(OCICompartmentSchema(), common_job_parameters).run(
        neo4j_session
    )


def transform_users(users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform users data to flatten capabilities and use underscored keys.
    """
    result = []
    for user in users:
        normalized = _normalize_oci_keys(user)
        transformed = {
            **normalized,
            "can_use_api_keys": user["capabilities"]["can-use-api-keys"],
            "can_use_auth_tokens": user["capabilities"]["can-use-auth-tokens"],
            "can_use_console_password": user["capabilities"][
                "can-use-console-password"
            ],
            "can_use_customer_secret_keys": user["capabilities"][
                "can-use-customer-secret-keys"
            ],
            "can_use_smtp_credentials": user["capabilities"][
                "can-use-smtp-credentials"
            ],
        }
        result.append(transformed)
    return result


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    users: list[dict[str, Any]],
    current_oci_tenancy_id: str,
    oci_update_tag: int,
) -> None:
    load(
        neo4j_session,
        OCIUserSchema(),
        users,
        lastupdated=oci_update_tag,
        OCI_TENANCY_ID=current_oci_tenancy_id,
    )


@timeit
def get_user_list_data(
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
) -> dict[str, list[dict[str, Any]]]:
    response = oci.pagination.list_call_get_all_results(
        iam.list_users,
        current_tenancy_id,
    )
    return {"Users": utils.oci_object_to_json(response.data)}


@timeit
def sync_users(
    neo4j_session: neo4j.Session,
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Syncing IAM users for account '%s'.", current_tenancy_id)
    data = get_user_list_data(iam, current_tenancy_id)
    transformed = transform_users(data["Users"])
    load_users(neo4j_session, transformed, current_tenancy_id, oci_update_tag)
    GraphJob.from_node_schema(OCIUserSchema(), common_job_parameters).run(neo4j_session)


@timeit
def get_group_list_data(
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
) -> dict[str, list[dict[str, Any]]]:
    response = oci.pagination.list_call_get_all_results(
        iam.list_groups,
        current_tenancy_id,
    )
    return {"Groups": utils.oci_object_to_json(response.data)}


def transform_groups(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform groups data to use underscored keys.
    """
    return [_normalize_oci_keys(g) for g in groups]


@timeit
def load_groups(
    neo4j_session: neo4j.Session,
    groups: list[dict[str, Any]],
    current_tenancy_id: str,
    oci_update_tag: int,
) -> None:
    load(
        neo4j_session,
        OCIGroupSchema(),
        groups,
        lastupdated=oci_update_tag,
        OCI_TENANCY_ID=current_tenancy_id,
    )


@timeit
def sync_groups(
    neo4j_session: neo4j.Session,
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[str]:
    logger.debug("Syncing IAM groups for account '%s'.", current_tenancy_id)
    data = get_group_list_data(iam, current_tenancy_id)
    transformed = transform_groups(data["Groups"])
    load_groups(neo4j_session, transformed, current_tenancy_id, oci_update_tag)
    GraphJob.from_node_schema(OCIGroupSchema(), common_job_parameters).run(
        neo4j_session
    )
    return [g["id"] for g in data["Groups"]]


@timeit
def get_group_membership_data(
    iam: oci.identity.identity_client.IdentityClient,
    group_id: str,
    current_tenancy_id: str,
) -> dict[str, list[dict[str, Any]]]:
    response = oci.pagination.list_call_get_all_results(
        iam.list_user_group_memberships,
        compartment_id=current_tenancy_id,
        group_id=group_id,
    )
    return {"GroupMemberships": utils.oci_object_to_json(response.data)}


def transform_group_memberships(
    groups: list[dict[str, Any]],
    groups_membership: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Transform group data to include user_ids for the one-to-many relationship.
    Filters memberships by group-id to ensure correct user-group associations.
    """
    result = []
    for group in groups:
        group_ocid = group["id"]
        membership_data = groups_membership.get(group_ocid, {"GroupMemberships": []})
        # Filter memberships to only include those for this specific group
        user_ids = [
            m["user-id"]
            for m in membership_data["GroupMemberships"]
            if m.get("group-id") == group_ocid
        ]
        normalized = _normalize_oci_keys(group)
        transformed = {
            **normalized,
            "user_ids": user_ids,
        }
        result.append(transformed)
    return result


@timeit
def load_group_memberships(
    neo4j_session: neo4j.Session,
    groups_with_members: list[dict[str, Any]],
    current_tenancy_id: str,
    oci_update_tag: int,
) -> None:
    """
    Load groups with their user memberships using the OCIGroupWithMembersSchema.
    """
    load(
        neo4j_session,
        OCIGroupWithMembersSchema(),
        groups_with_members,
        lastupdated=oci_update_tag,
        OCI_TENANCY_ID=current_tenancy_id,
    )


@timeit
def sync_group_memberships(
    neo4j_session: neo4j.Session,
    iam: oci.identity.identity_client.IdentityClient,
    group_ids: list[str],
    current_tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Syncing IAM group membership for account '%s'.", current_tenancy_id)
    groups_membership = {
        group_id: get_group_membership_data(iam, group_id, current_tenancy_id)
        for group_id in group_ids
    }
    group_data = get_group_list_data(iam, current_tenancy_id)
    transformed = transform_group_memberships(group_data["Groups"], groups_membership)
    load_group_memberships(
        neo4j_session,
        transformed,
        current_tenancy_id,
        oci_update_tag,
    )
    GraphJob.from_node_schema(OCIGroupWithMembersSchema(), common_job_parameters).run(
        neo4j_session
    )


def transform_policies(policies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform policies data to use underscored keys.
    """
    return [_normalize_oci_keys(p) for p in policies]


@timeit
def load_policies(
    neo4j_session: neo4j.Session,
    policies: list[dict[str, Any]],
    current_tenancy_id: str,
    oci_update_tag: int,
) -> None:
    load(
        neo4j_session,
        OCIPolicySchema(),
        policies,
        lastupdated=oci_update_tag,
        OCI_TENANCY_ID=current_tenancy_id,
    )


@timeit
def get_policy_list_data(
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
) -> dict[str, list[dict[str, Any]]]:
    response = oci.pagination.list_call_get_all_results(
        iam.list_policies,
        compartment_id=current_tenancy_id,
    )
    return {"Policies": utils.oci_object_to_json(response.data)}


@timeit
def sync_policies(
    neo4j_session: neo4j.Session,
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: dict[str, Any],
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
            transformed = transform_policies(data["Policies"])
            load_policies(
                neo4j_session,
                transformed,
                current_tenancy_id,
                oci_update_tag,
            )
    GraphJob.from_node_schema(OCIPolicySchema(), common_job_parameters).run(
        neo4j_session
    )


def transform_policy_references(
    policies: list[dict[str, Any]],
    groups: list[dict[str, Any]],
    compartments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Parse policy statements to extract references to groups and compartments.
    Returns policies with referenced_group_ids and referenced_compartment_ids lists.
    """
    # Build lookup maps for faster matching
    group_name_to_ocid = {g["name"].lower(): g["ocid"] for g in groups}
    compartment_ocid_to_parent = {c["ocid"]: c["compartmentid"] for c in compartments}

    result = []
    for policy in policies:
        referenced_group_ids: list[str] = []
        referenced_compartment_ids: list[str] = []
        check_compart = policy["compartmentid"]

        for statement in policy["statements"]:
            # Extract group references
            m = re.search("(?<=group\\s)[^ ]*(?=\\s)", statement)
            if m:
                group_name = m.group(0).lower()
                if group_name in group_name_to_ocid:
                    group_ocid = group_name_to_ocid[group_name]
                    if group_ocid not in referenced_group_ids:
                        referenced_group_ids.append(group_ocid)

            # Extract compartment references
            m = re.search("(?<=compartment\\s)[^ ]*(?=$)", statement)
            if m:
                compartment_name = m.group(0).lower()
                # Only look at the compartment or subcompartment name referenced in the policy statement
                # in which the policy is a member of.
                for comp in compartments:
                    if (
                        comp["ocid"] == check_compart
                        or compartment_ocid_to_parent.get(comp["ocid"]) == check_compart
                    ):
                        if comp["name"].lower() == compartment_name:
                            if comp["ocid"] not in referenced_compartment_ids:
                                referenced_compartment_ids.append(comp["ocid"])

        result.append(
            {
                **policy,
                "referenced_group_ids": referenced_group_ids,
                "referenced_compartment_ids": referenced_compartment_ids,
            }
        )

    return result


@timeit
def load_policy_references(
    neo4j_session: neo4j.Session,
    policies_with_refs: list[dict[str, Any]],
    tenancy_id: str,
    oci_update_tag: int,
) -> None:
    """
    Load policies with their semantic references to groups and compartments.
    """
    load(
        neo4j_session,
        OCIPolicyWithReferencesSchema(),
        policies_with_refs,
        lastupdated=oci_update_tag,
        OCI_TENANCY_ID=tenancy_id,
    )


@timeit
def sync_oci_policy_references(
    neo4j_session: neo4j.Session,
    tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Parse the statements inside OCI Policies and load the corresponding
    relationships they reference (to groups and compartments).
    """
    groups = list(utils.get_groups_in_tenancy(neo4j_session, tenancy_id))
    compartments = list(utils.get_compartments_in_tenancy(neo4j_session, tenancy_id))
    policies = list(utils.get_policies_in_tenancy(neo4j_session, tenancy_id))

    if not policies:
        return

    policies_with_refs = transform_policy_references(policies, groups, compartments)
    load_policy_references(
        neo4j_session, policies_with_refs, tenancy_id, oci_update_tag
    )
    GraphJob.from_node_schema(
        OCIPolicyWithReferencesSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def get_region_subscriptions_list_data(
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
) -> dict[str, list[dict[str, Any]]]:
    response = oci.pagination.list_call_get_all_results(
        iam.list_region_subscriptions,
        current_tenancy_id,
    )
    return {"RegionSubscriptions": utils.oci_object_to_json(response.data)}


def transform_regions(regions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform regions data to use underscored keys.
    """
    return [_normalize_oci_keys(r) for r in regions]


@timeit
def load_region_subscriptions(
    neo4j_session: neo4j.Session,
    regions: list[dict[str, Any]],
    tenancy_id: str,
    oci_update_tag: int,
) -> None:
    load(
        neo4j_session,
        OCIRegionSchema(),
        regions,
        lastupdated=oci_update_tag,
        OCI_TENANCY_ID=tenancy_id,
    )


@timeit
def sync_region_subscriptions(
    neo4j_session: neo4j.Session,
    iam: oci.identity.identity_client.IdentityClient,
    current_tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug(
        "Syncing IAM region subscriptions for account '%s'.",
        current_tenancy_id,
    )
    data = get_region_subscriptions_list_data(iam, current_tenancy_id)
    transformed = transform_regions(data["RegionSubscriptions"])
    load_region_subscriptions(
        neo4j_session,
        transformed,
        current_tenancy_id,
        oci_update_tag,
    )
    GraphJob.from_node_schema(OCIRegionSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    iam: oci.identity.identity_client.IdentityClient,
    tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Syncing IAM for account '%s'.", tenancy_id)
    sync_users(neo4j_session, iam, tenancy_id, oci_update_tag, common_job_parameters)
    group_ids = sync_groups(
        neo4j_session, iam, tenancy_id, oci_update_tag, common_job_parameters
    )
    sync_group_memberships(
        neo4j_session,
        iam,
        group_ids,
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
