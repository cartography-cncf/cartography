import logging
from typing import Any

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.models.googleworkspace.tenant import GoogleWorkspaceTenantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

GOOGLE_API_NUM_RETRIES = 5


@timeit
def get_tenant(admin: Resource) -> dict[str, Any]:
    """
    Return the Google Workspace tenant information
    https://developers.google.com/workspace/admin/directory/reference/rest/v1/customers/get

    :param admin: apiclient discovery resource object
    :return: Google Workspace tenant information
    """
    try:
        req = admin.customers().get(
            customerKey="my_customer",
        )
        resp = req.execute(num_retries=GOOGLE_API_NUM_RETRIES)
        return resp
    except HttpError as e:
        if (
            e.resp.status == 403
            and "Request had insufficient authentication scopes" in str(e)
        ):
            logger.error(
                "Missing required Google Workspace scopes. If using the gcloud CLI, "
                "run: gcloud auth application-default login --scopes="
                "https://www.googleapis.com/auth/admin.directory.customer.readonly,"
                "https://www.googleapis.com/auth/admin.directory.user.readonly,"
                "https://www.googleapis.com/auth/admin.directory.user.security,"
                "https://www.googleapis.com/auth/cloud-identity.devices.readonly,"
                "https://www.googleapis.com/auth/cloud-identity.groups.readonly,"
                "https://www.googleapis.com/auth/cloud-platform"
            )
        raise


@timeit
def load_googleworkspace_tenant(
    neo4j_session: neo4j.Session,
    tenant_data: dict[str, Any],
    googleworkspace_update_tag: int,
) -> None:
    """
    Load Google Workspace tenant
    """
    logger.info("Ingesting %s Google Workspace tenant", tenant_data["id"])
    load(
        neo4j_session,
        GoogleWorkspaceTenantSchema(),
        [tenant_data],
        lastupdated=googleworkspace_update_tag,
    )


@timeit
def sync_googleworkspace_tenant(
    neo4j_session: neo4j.Session,
    admin: Resource,
    googleworkspace_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[str]:
    """Sync Google Workspace tenant data."""
    logger.debug("Syncing Google Workspace Tenant data")

    # GET - Fetch data from API
    resp_obj = get_tenant(admin)

    # LOAD - Ingest to Neo4j using data model
    load_googleworkspace_tenant(neo4j_session, resp_obj, googleworkspace_update_tag)

    # Return the customer ID
    return resp_obj["id"]
