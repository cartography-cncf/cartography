import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import determine_role_type_and_scope
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.models.gcp.iam import GCPOrgRoleSchema
from cartography.models.gcp.iam import GCPProjectRoleSchema
from cartography.models.gcp.iam import GCPServiceAccountSchema
from cartography.models.gcp.iam_keys import GCPServiceAccountKeySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_service_accounts(
    iam_client: Resource, project_id: str
) -> List[Dict[str, Any]]:
    """
    Retrieve a list of GCP service accounts for a given project.

    :param iam_client: The IAM resource object created by googleapiclient.discovery.build().
    :param project_id: The GCP Project ID to retrieve service accounts from.
    :return: A list of dictionaries representing GCP service accounts.
    """
    service_accounts: List[Dict[str, Any]] = []
    request = (
        iam_client.projects()
        .serviceAccounts()
        .list(
            name=f"projects/{project_id}",
        )
    )
    while request is not None:
        response = gcp_api_execute_with_retry(request)
        if "accounts" in response:
            service_accounts.extend(response["accounts"])
        request = (
            iam_client.projects()
            .serviceAccounts()
            .list_next(
                previous_request=request,
                previous_response=response,
            )
        )
    return service_accounts


@timeit
def get_gcp_service_account_keys(
    iam_client: Resource, service_account_name: str
) -> List[Dict[str, Any]]:
    """
    Retrieve user-managed keys for a single GCP service account.

    System-managed keys are intentionally skipped: Google rotates them
    automatically and they are not a credential-management concern.

    :param iam_client: The IAM resource object created by googleapiclient.discovery.build().
    :param service_account_name: Full SA resource name, e.g.
        "projects/{project_id}/serviceAccounts/{email}".
    :return: A list of dictionaries representing GCP service account keys.
    """
    response = gcp_api_execute_with_retry(
        iam_client.projects()
        .serviceAccounts()
        .keys()
        .list(
            name=service_account_name,
            keyTypes=["USER_MANAGED"],
        ),
    )
    return response.get("keys", [])


@timeit
def get_gcp_predefined_roles(iam_client: Resource) -> List[Dict]:
    """
    Retrieve all predefined (Google-managed) IAM roles.

    Predefined roles are global and not project-specific.

    :param iam_client: The IAM resource object created by googleapiclient.discovery.build().
    :return: A list of dictionaries representing GCP predefined roles.
    """
    roles: List[Dict] = []
    predefined_req = iam_client.roles().list(view="FULL")
    while predefined_req is not None:
        resp = gcp_api_execute_with_retry(predefined_req)
        roles.extend(resp.get("roles", []))
        predefined_req = iam_client.roles().list_next(predefined_req, resp)
    return roles


@timeit
def get_gcp_org_roles(iam_client: Resource, org_id: str) -> List[Dict]:
    """
    Retrieve custom organization-level IAM roles.

    :param iam_client: The IAM resource object created by googleapiclient.discovery.build().
    :param org_id: The GCP Organization ID (e.g., "organizations/123456789012").
    :return: A list of dictionaries representing GCP custom organization roles.
    """
    roles: List[Dict] = []
    req = iam_client.organizations().roles().list(parent=org_id, view="FULL")
    while req is not None:
        resp = gcp_api_execute_with_retry(req)
        roles.extend(resp.get("roles", []))
        req = iam_client.organizations().roles().list_next(req, resp)
    return roles


@timeit
def get_gcp_project_custom_roles(iam_client: Resource, project_id: str) -> List[Dict]:
    """
    Retrieve custom project-level IAM roles only (not predefined roles).

    :param iam_client: The IAM resource object created by googleapiclient.discovery.build().
    :param project_id: The GCP Project ID to retrieve roles from.
    :return: A list of dictionaries representing GCP custom project roles.
    """
    roles: List[Dict] = []
    custom_req = (
        iam_client.projects().roles().list(parent=f"projects/{project_id}", view="FULL")
    )
    while custom_req is not None:
        resp = gcp_api_execute_with_retry(custom_req)
        roles.extend(resp.get("roles", []))
        custom_req = iam_client.projects().roles().list_next(custom_req, resp)
    return roles


def transform_gcp_service_accounts(
    raw_accounts: List[Dict[str, Any]],
    project_id: str,
) -> List[Dict[str, Any]]:
    """
    Transform raw GCP service accounts into loader-friendly dicts.
    """
    result: List[Dict[str, Any]] = []
    for sa in raw_accounts:
        result.append(
            {
                "id": sa["uniqueId"],
                "email": sa.get("email"),
                "displayName": sa.get("displayName"),
                "oauth2ClientId": sa.get("oauth2ClientId"),
                "uniqueId": sa.get("uniqueId"),
                "disabled": sa.get("disabled", False),
                "projectId": project_id,
            },
        )
    return result


@timeit
def load_gcp_service_accounts(
    neo4j_session: neo4j.Session,
    service_accounts: List[Dict[str, Any]],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Load GCP service account data into Neo4j.
    """
    logger.debug(
        f"Loading {len(service_accounts)} service accounts for project {project_id}"
    )

    load(
        neo4j_session,
        GCPServiceAccountSchema(),
        service_accounts,
        lastupdated=gcp_update_tag,
        projectId=project_id,
    )


def transform_gcp_service_account_keys(
    raw_keys: List[Dict[str, Any]],
    service_account_email: str,
) -> List[Dict[str, Any]]:
    """
    Transform raw GCP service account keys into loader-friendly dicts.

    The full key resource name is used as the node id so that the same key
    is represented identically across ingestions.
    """
    result: List[Dict[str, Any]] = []
    for key in raw_keys:
        key_name = key.get("name")
        if not key_name:
            # The IAM API contract guarantees `name` on every key; a record
            # missing it is a real anomaly worth surfacing rather than
            # silently dropping. Log only known-safe descriptive fields so
            # future API additions cannot leak identifiers into the log.
            logger.warning(
                "Skipping GCP service account key without a 'name' field "
                "(keyType=%s, keyAlgorithm=%s)",
                key.get("keyType"),
                key.get("keyAlgorithm"),
            )
            continue
        result.append(
            {
                "id": key_name,
                "name": key_name,
                "keyType": key.get("keyType"),
                "keyOrigin": key.get("keyOrigin"),
                "keyAlgorithm": key.get("keyAlgorithm"),
                "validAfterTime": key.get("validAfterTime"),
                "validBeforeTime": key.get("validBeforeTime"),
                "disabled": key.get("disabled", False),
                "serviceAccountEmail": service_account_email,
            },
        )
    return result


@timeit
def load_gcp_service_account_keys(
    neo4j_session: neo4j.Session,
    keys: List[Dict[str, Any]],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Load GCP service account key data into Neo4j.
    """
    if not keys:
        return
    logger.debug(f"Loading {len(keys)} service account keys for project {project_id}")

    load(
        neo4j_session,
        GCPServiceAccountKeySchema(),
        keys,
        lastupdated=gcp_update_tag,
        projectId=project_id,
    )


def transform_org_roles(
    raw_roles: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Transform raw GCP organization-level roles (predefined + custom org roles) into loader-friendly dicts.

    These roles are sub-resources of the organization.
    """
    result: List[Dict[str, Any]] = []
    for role in raw_roles:
        role_name = role["name"]
        role_type, scope = determine_role_type_and_scope(role_name)

        result.append(
            {
                "name": role_name,
                "title": role.get("title"),
                "description": role.get("description"),
                "deleted": role.get("deleted", False),
                "etag": role.get("etag"),
                "includedPermissions": role.get("includedPermissions", []),
                "roleType": role_type,
                "scope": scope,
            },
        )
    return result


def transform_project_roles(
    raw_roles: List[Dict[str, Any]],
    project_id: str,
) -> List[Dict[str, Any]]:
    """
    Transform raw GCP project-level custom roles into loader-friendly dicts.

    These roles are sub-resources of the project.
    """
    result: List[Dict[str, Any]] = []
    for role in raw_roles:
        role_name = role["name"]
        role_type, scope = determine_role_type_and_scope(role_name)

        result.append(
            {
                "name": role_name,
                "title": role.get("title"),
                "description": role.get("description"),
                "deleted": role.get("deleted", False),
                "etag": role.get("etag"),
                "includedPermissions": role.get("includedPermissions", []),
                "roleType": role_type,
                "scope": scope,
                "projectId": project_id,
            },
        )
    return result


def build_role_permissions_by_name(
    roles: list[dict[str, Any]],
) -> dict[str, list[str]]:
    role_permissions_by_name: dict[str, list[str]] = {}
    for role in roles:
        name = role.get("name")
        permissions = role.get("includedPermissions")
        if name and permissions:
            role_permissions_by_name[name] = permissions
    return role_permissions_by_name


@timeit
def load_org_roles(
    neo4j_session: neo4j.Session,
    roles: List[Dict[str, Any]],
    organization_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Load organization-level GCP roles (predefined + custom org) into Neo4j.

    :param neo4j_session: The Neo4j session.
    :param roles: List of transformed role dictionaries.
    :param organization_id: The organization ID (e.g., "organizations/123456789012").
    :param gcp_update_tag: The timestamp of the current sync run.
    """
    logger.debug(f"Loading {len(roles)} org-level roles for {organization_id}")

    load(
        neo4j_session,
        GCPOrgRoleSchema(),
        roles,
        lastupdated=gcp_update_tag,
        organizationId=organization_id,
    )


@timeit
def load_project_roles(
    neo4j_session: neo4j.Session,
    roles: List[Dict[str, Any]],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Load project-level GCP roles into Neo4j.

    :param neo4j_session: The Neo4j session.
    :param roles: List of transformed role dictionaries.
    :param project_id: The project ID.
    :param gcp_update_tag: The timestamp of the current sync run.
    """
    logger.debug(f"Loading {len(roles)} project-level roles for {project_id}")

    load(
        neo4j_session,
        GCPProjectRoleSchema(),
        roles,
        lastupdated=gcp_update_tag,
        projectId=project_id,
    )


@timeit
def cleanup_service_account_keys(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    """
    Run cleanup job for GCP service account keys in Neo4j.

    Keys are leaf nodes hanging off service accounts; clean them up before
    cleaning up service accounts to avoid orphan HAS_KEY relationships.
    """
    logger.debug("Running GCP service account key cleanup job")
    job_params = {
        **common_job_parameters,
        "projectId": common_job_parameters.get("PROJECT_ID"),
    }

    cleanup_job = GraphJob.from_node_schema(GCPServiceAccountKeySchema(), job_params)
    cleanup_job.run(neo4j_session)


@timeit
def cleanup_service_accounts(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    """
    Run cleanup job for GCP service accounts in Neo4j.

    Service accounts are scoped to projects.

    :param neo4j_session: The Neo4j session.
    :param common_job_parameters: Common job parameters for cleanup.
    """
    logger.debug("Running GCP service account cleanup job")
    job_params = {
        **common_job_parameters,
        "projectId": common_job_parameters.get("PROJECT_ID"),
    }

    cleanup_job = GraphJob.from_node_schema(GCPServiceAccountSchema(), job_params)
    cleanup_job.run(neo4j_session)


@timeit
def cleanup_org_roles(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    """
    Run cleanup job for organization-level GCP roles in Neo4j.

    :param neo4j_session: The Neo4j session.
    :param common_job_parameters: Common job parameters for cleanup.
    """
    logger.debug("Running GCP org-level role cleanup job")
    job_params = {
        **common_job_parameters,
        "organizationId": common_job_parameters.get("ORG_RESOURCE_NAME"),
    }

    cleanup_job = GraphJob.from_node_schema(GCPOrgRoleSchema(), job_params)
    cleanup_job.run(neo4j_session)


@timeit
def cleanup_project_roles(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    """
    Run cleanup job for project-level GCP roles in Neo4j.

    :param neo4j_session: The Neo4j session.
    :param common_job_parameters: Common job parameters for cleanup.
    """
    logger.debug("Running GCP project-level role cleanup job")
    job_params = {
        **common_job_parameters,
        "projectId": common_job_parameters.get("PROJECT_ID"),
    }

    cleanup_job = GraphJob.from_node_schema(GCPProjectRoleSchema(), job_params)
    cleanup_job.run(neo4j_session)


@timeit
def sync_org_iam(
    neo4j_session: neo4j.Session,
    iam_client: Resource,
    org_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Sync organization-level IAM resources (predefined roles + custom org roles).

    This should be called once per organization, before syncing project-level resources.
    It syncs:
    - Predefined/basic roles (roles/*) - global, same everywhere
    - Custom organization roles (organizations/{org}/roles/*) - org-specific

    Cleanup for org-level roles should be called after all project syncs are complete.

    :param neo4j_session: The Neo4j session.
    :param iam_client: The IAM resource object created by googleapiclient.discovery.build().
    :param org_id: The GCP Organization ID (e.g., "organizations/123456789012").
    :param gcp_update_tag: The timestamp of the current sync run.
    :param common_job_parameters: Common job parameters for the sync.
    """
    logger.info(f"Syncing organization-level IAM for {org_id}")

    # Fetch predefined roles (global)
    predefined_roles_raw = get_gcp_predefined_roles(iam_client)
    logger.info(f"Found {len(predefined_roles_raw)} predefined roles")

    # Fetch custom organization roles
    org_roles_raw = get_gcp_org_roles(iam_client, org_id)
    logger.info(f"Found {len(org_roles_raw)} custom organization roles in {org_id}")

    # Combine and transform
    all_org_roles = predefined_roles_raw + org_roles_raw
    roles = transform_org_roles(all_org_roles)

    # Load roles with organization as parent
    load_org_roles(neo4j_session, roles, org_id, gcp_update_tag)
    return roles


@timeit
def sync(
    neo4j_session: neo4j.Session,
    iam_client: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Sync GCP IAM resources for a given project.

    This syncs:
    - Service accounts (project-specific)
    - User-managed service account keys (per service account)
    - Custom project-level roles (projects/{project}/roles/*)

    Note: Predefined roles and custom org roles are synced separately via sync_org_iam().

    Cleanup is NOT run here - it should be called separately after syncing all projects.

    Side effect: sets ``_iam_keys_sync_complete`` on ``common_job_parameters`` to
    ``False`` if any service account's keys could not be listed. The caller is
    expected to read this flag before running ``cleanup_service_account_keys``;
    skipping cleanup on failure prevents stale keys from being silently deleted
    when the failure was a transient quota/permission issue on a single SA.

    :param neo4j_session: The Neo4j session.
    :param iam_client: The IAM resource object created by googleapiclient.discovery.build().
    :param project_id: The GCP Project ID to sync.
    :param gcp_update_tag: The timestamp of the current sync run.
    :param common_job_parameters: Common job parameters for the sync.
    """
    logger.info(f"Syncing GCP IAM for project {project_id}")

    # Sync service accounts (project-specific)
    service_accounts_raw = get_gcp_service_accounts(iam_client, project_id)
    logger.info(
        f"Found {len(service_accounts_raw)} service accounts in project {project_id}"
    )
    service_accounts = transform_gcp_service_accounts(service_accounts_raw, project_id)
    load_gcp_service_accounts(
        neo4j_session, service_accounts, project_id, gcp_update_tag
    )

    # Sync user-managed keys for each service account.
    # Track per-SA failures: if any fetch fails we cannot safely run the keys
    # cleanup job — keys we did not refresh would be deleted as stale.
    all_keys: list[dict[str, Any]] = []
    keys_sync_complete = True
    for sa in service_accounts_raw:
        sa_email = sa.get("email")
        sa_name = sa.get("name")
        if not sa_email or not sa_name:
            continue
        try:
            keys_raw = get_gcp_service_account_keys(iam_client, sa_name)
            all_keys.extend(transform_gcp_service_account_keys(keys_raw, sa_email))
        except Exception as e:
            keys_sync_complete = False
            # Log the SA's opaque uniqueId rather than the email so log
            # aggregators do not pick up identifiers that double as account
            # names. Operators can resolve the uniqueId back to a SA via the
            # synced graph if they need to triage.
            logger.warning(
                "Failed to list keys for service account uniqueId=%s in "
                "project %s: %s. Skipping service account key cleanup for "
                "this project to avoid deleting keys that were not "
                "re-ingested.",
                sa.get("uniqueId", "<unknown>"),
                project_id,
                e,
            )
    common_job_parameters["_iam_keys_sync_complete"] = keys_sync_complete
    if all_keys:
        load_gcp_service_account_keys(
            neo4j_session, all_keys, project_id, gcp_update_tag
        )

    # Sync custom project-level roles only (not predefined roles)
    project_roles_raw = get_gcp_project_custom_roles(iam_client, project_id)
    logger.info(
        f"Found {len(project_roles_raw)} custom project roles in project {project_id}"
    )

    roles = transform_project_roles(project_roles_raw, project_id)
    if roles:
        load_project_roles(neo4j_session, roles, project_id, gcp_update_tag)

    return roles
