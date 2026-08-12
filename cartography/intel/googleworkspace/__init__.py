import base64
import json
import logging
import os
from collections import namedtuple
from typing import TYPE_CHECKING

import neo4j

from cartography.config import Config
from cartography.util import timeit
from cartography.util.lazy import lazy_callable
from cartography.util.lazy import lazy_import

# Submodules are bound lazily so that the provider SDK only loads once the config
if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials as OAuth2Credentials
    from google.oauth2.service_account import Credentials as ServiceAccountCredentials

# gate below has decided that this module has something to sync.
default = lazy_callable("google.auth", "default")
google_auth_exceptions = lazy_import("google.auth.exceptions")
googleapiclient = lazy_import("googleapiclient")
credentials = lazy_import("google.oauth2.credentials")
service_account = lazy_import("google.oauth2.service_account")
Request = lazy_callable("google.auth.transport.requests", "Request")
devices = lazy_import("cartography.intel.googleworkspace.devices")
groups = lazy_import("cartography.intel.googleworkspace.groups")
oauth_apps = lazy_import("cartography.intel.googleworkspace.oauth_apps")
tenant = lazy_import("cartography.intel.googleworkspace.tenant")
users = lazy_import("cartography.intel.googleworkspace.users")

OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.customer.readonly",
    "https://www.googleapis.com/auth/admin.directory.user.readonly",
    "https://www.googleapis.com/auth/admin.directory.user.security",
    "https://www.googleapis.com/auth/cloud-identity.devices.readonly",
    "https://www.googleapis.com/auth/cloud-identity.groups.readonly",
]

logger = logging.getLogger(__name__)

Resources = namedtuple("Resources", ["admin", "cloudidentity"])


def _initialize_resources(
    creds: "OAuth2Credentials | ServiceAccountCredentials",
) -> Resources:
    """
    Create namedtuple of all resource objects necessary for Google API data gathering.
    :param credentials: The credentials object
    :return: namedtuple of all resource objects
    """

    return Resources(
        googleapiclient.discovery.build(
            "admin",
            "directory_v1",
            credentials=creds,
            cache_discovery=False,
        ),
        googleapiclient.discovery.build(
            "cloudidentity",
            "v1",
            credentials=creds,
            cache_discovery=False,
        ),
    )


@timeit
def start_googleworkspace_ingestion(
    neo4j_session: neo4j.Session, config: Config
) -> None:
    """
    Starts the Google Workspace ingestion process by initializing

    :param neo4j_session: The Neo4j session
    :param config: A `cartography.config` object
    :return: Nothing
    """
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    creds: "OAuth2Credentials | ServiceAccountCredentials"
    if config.googleworkspace_auth_method == "delegated":  # Legacy delegated method
        if config.googleworkspace_config is None or not os.path.isfile(
            config.googleworkspace_config
        ):
            logger.warning(
                (
                    "The Google Workspace config file is not set or is not a valid file."
                    "Skipping Google Workspace ingestion."
                ),
            )
            return
        logger.info(
            "Attempting to authenticate to Google Workspace using legacy delegated method"
        )
        try:
            creds = service_account.Credentials.from_service_account_file(
                config.googleworkspace_config,
                scopes=OAUTH_SCOPES,
            )
            creds = creds.with_subject(os.environ.get("GOOGLE_DELEGATED_ADMIN"))

        except google_auth_exceptions.DefaultCredentialsError as e:
            logger.error(
                (
                    "Unable to initialize Google Workspace creds. If you don't have Google Workspace data or don't want to load "
                    "Google Workspace data then you can ignore this message. Otherwise, the error code is: %s "
                    "Make sure your Google Workspace credentials file (if any) is valid. "
                    "For more details see documentation."
                ),
                e,
            )
            return
    elif config.googleworkspace_auth_method == "oauth":
        auth_tokens = json.loads(
            str(base64.b64decode(config.googleworkspace_config).decode())
        )
        logger.info("Attempting to authenticate to Google Workspace using OAuth")
        # Allow scopes to be specified in the auth payload, falling back to defaults.
        # This enables callers to use a subset of scopes (e.g., without devices.readonly
        # if they don't have Cloud Identity Premium).
        oauth_scopes = auth_tokens.get("scopes", OAUTH_SCOPES)
        try:
            creds = credentials.Credentials(
                token=None,
                client_id=auth_tokens["client_id"],
                client_secret=auth_tokens["client_secret"],
                refresh_token=auth_tokens["refresh_token"],
                expiry=None,
                token_uri=auth_tokens["token_uri"],
                scopes=oauth_scopes,
            )
            creds.refresh(Request())
        except google_auth_exceptions.DefaultCredentialsError as e:
            logger.error(
                (
                    "Unable to initialize Google Workspace creds. If you don't have Google Workspace data or don't want to load "
                    "Google Workspace data then you can ignore this message. Otherwise, the error code is: %s "
                    "Make sure your Google Workspace credentials are configured correctly, your credentials are valid. "
                    "For more details see documentation."
                ),
                e,
            )
            return
    elif config.googleworkspace_auth_method == "default":
        logger.info(
            "Attempting to authenticate to Google Workspace using default credentials"
        )
        try:
            creds, _ = default(scopes=OAUTH_SCOPES)
        except google_auth_exceptions.DefaultCredentialsError as e:
            logger.error(
                (
                    "Unable to initialize Google Workspace creds using default credentials. If you don't have Google Workspace data or "
                    "don't want to load Google Workspace data then you can ignore this message. Otherwise, the error code is: %s "
                    "Make sure you have valid application default credentials configured. "
                    "For more details see documentation."
                ),
                e,
            )
            return

    resources = _initialize_resources(creds)
    customer_id = tenant.sync_googleworkspace_tenant(
        neo4j_session,
        resources.admin,
        config.update_tag,
        common_job_parameters,
    )
    common_job_parameters["CUSTOMER_ID"] = customer_id

    # Sync users and get the list of transformed users for OAuth token sync
    user_ids = users.sync_googleworkspace_users(
        neo4j_session,
        resources.admin,
        config.update_tag,
        common_job_parameters,
    )

    # Sync OAuth apps for all users
    oauth_apps.sync_googleworkspace_oauth_apps(
        neo4j_session,
        resources.admin,
        user_ids,
        config.update_tag,
        common_job_parameters,
    )

    groups.sync_googleworkspace_groups(
        neo4j_session,
        resources.cloudidentity,
        config.update_tag,
        common_job_parameters,
    )

    # Only sync devices if the devices scope was authorized (requires Cloud Identity Premium)
    devices_scope = "https://www.googleapis.com/auth/cloud-identity.devices.readonly"
    if hasattr(creds, "scopes") and creds.scopes and devices_scope in creds.scopes:
        devices.sync_googleworkspace_devices(
            neo4j_session,
            resources.cloudidentity,
            config.update_tag,
            common_job_parameters,
        )
    else:
        logger.info(
            "Skipping device sync - cloud-identity.devices.readonly scope not authorized",
        )
