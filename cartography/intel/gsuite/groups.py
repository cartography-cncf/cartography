import logging
from typing import Any

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gsuite.group import GSuiteGroupSchema
from cartography.models.gsuite.tenant import GSuiteTenantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

GOOGLE_API_NUM_RETRIES = 5


@timeit
def get_all_groups(admin: Resource, customer_id: str = "my_customer") -> list[dict]:
    """
    Return list of Google Groups in your organization
    Returns empty list if we are unable to enumerate the groups for any reasons

    googleapiclient.discovery.build('admin', 'directory_v1', credentials=credentials, cache_discovery=False)

    :param admin: google's apiclient discovery resource object.  From googleapiclient.discovery.build
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :return: list of Google groups in domain
    """
    request = admin.groups().list(
        customer=customer_id,
        maxResults=20,
        orderBy="email",
    )
    response_objects = []
    while request is not None:
        try:
            resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
            response_objects.append(resp)
            request = admin.groups().list_next(request, resp)
        except HttpError as e:
            if (
                e.resp.status == 403
                and "Request had insufficient authentication scopes" in str(e)
            ):
                logger.error(
                    "Missing required GSuite scopes. If using the gcloud CLI, "
                    "run: gcloud auth application-default login --scopes="
                    '"https://www.googleapis.com/auth/admin.directory.user.readonly,'
                    "https://www.googleapis.com/auth/admin.directory.group.readonly,"
                    "https://www.googleapis.com/auth/admin.directory.group.member.readonly,"
                    'https://www.googleapis.com/auth/cloud-platform"'
                )
            raise
    return response_objects


@timeit
def get_members_for_groups(
    admin: Resource, groups_email: list[str]
) -> dict[str, list[dict[str, Any]]]:
    """Get all members for given groups emails

    Args:
        admin (Resource): google's apiclient discovery resource object.  From googleapiclient.discovery.build
        See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
        groups_email (list[str]): List of group email addresses to get members for


    :return: list of dictionaries representing Users or Groups grouped by group email
    """
    results: dict[str, list[dict]] = {}
    for group_email in groups_email:
        request = admin.members().list(
            groupKey=group_email,
            maxResults=500,
        )
        members: list[dict] = []
        while request is not None:
            resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
            members = members + resp.get("members", [])
            request = admin.members().list_next(request, resp)
        results[group_email] = members

    return results


@timeit
def transform_groups(
    group_response: list[dict], group_memberships: dict[str, list[dict[str, Any]]]
) -> tuple[list[dict], list[dict]]:
    """Strips list of API response objects to return list of group objects only and a list of subgroup relationships

    :param response_objects:
    :return: list of dictionary objects as defined in /docs/root/modules/gsuite/schema.md and a list of subgroup relationships
    """
    groups: list[dict] = []
    sub_groups: list[dict] = []
    for response_object in group_response:
        for group in response_object.get("groups", []):
            group_id = group.get("id")
            group_email = group.get("email")
            group["member_emails"] = []
            group["owner_emails"] = []
            for member in group_memberships.get(group_email, []):
                if member.get("type") == "GROUP":
                    sub_groups.append(
                        {
                            "parent_group_id": group_id,
                            "subgroup_email": member.get("email"),
                            "role": member.get("role"),
                        }
                    )
                    continue
                if member.get("role") == "OWNER":
                    group["owner_emails"].append(member.get("email"))
                elif member.get("type") == "USER":
                    group["member_emails"].append(member.get("email"))
            groups.append(group)
    return groups, sub_groups


@timeit
def load_gsuite_groups(
    neo4j_session: neo4j.Session,
    groups: list[dict],
    customer_id: str,
    gsuite_update_tag: int,
) -> None:
    """
    Load GSuite groups using the modern data model
    """
    logger.info(f"Ingesting {len(groups)} gsuite groups")

    # Load tenant first if it doesn't exist
    tenant_data = [{"id": customer_id}]
    load(
        neo4j_session,
        GSuiteTenantSchema(),
        tenant_data,
        lastupdated=gsuite_update_tag,
    )

    # Load groups with relationship to tenant
    load(
        neo4j_session,
        GSuiteGroupSchema(),
        groups,
        lastupdated=gsuite_update_tag,
        CUSTOMER_ID=customer_id,
    )


@timeit
def cleanup_gsuite_groups(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Clean up GSuite groups using the modern data model
    """
    logger.debug("Running GSuite groups cleanup job")
    GraphJob.from_node_schema(GSuiteGroupSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_gsuite_groups(
    neo4j_session: neo4j.Session,
    admin: Resource,
    gsuite_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    GET GSuite group objects using the google admin api resource, load the data into Neo4j and clean up stale nodes.

    :param neo4j_session: The Neo4j session
    :param admin: Google admin resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :param gsuite_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug("Syncing GSuite Groups")

    customer_id = common_job_parameters.get(
        "CUSTOMER_ID", "my_customer"
    )  # Default to "my_customer" for backward compatibility

    # 1. GET - Fetch data from API
    resp_objs = get_all_groups(admin, customer_id)
    group_members = get_members_for_groups(admin, [resp["email"] for resp in resp_objs])

    # 2. TRANSFORM - Shape data for ingestion
    groups, _ = transform_groups(
        resp_objs, group_members
    )  # Subgroup relationships are not yet ingested

    # 3. LOAD - Ingest to Neo4j using data model
    load_gsuite_groups(neo4j_session, groups, customer_id, gsuite_update_tag)

    # 4. CLEANUP - Remove stale data
    cleanup_params = {**common_job_parameters, "CUSTOMER_ID": customer_id}
    cleanup_gsuite_groups(neo4j_session, cleanup_params)
