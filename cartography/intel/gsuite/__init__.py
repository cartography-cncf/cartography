import base64
import json
import logging
import os
from collections import namedtuple
from typing import TYPE_CHECKING

import neo4j

from cartography.analysis.gsuite.analysis import GSUITE_HUMAN_LINK
from cartography.config import Config
from cartography.util import run_analysis_job
from cartography.util import run_typed_analysis_job
from cartography.util import timeit
from cartography.util.lazy import lazy_callable
from cartography.util.lazy import lazy_import

# Submodules are bound lazily so that the provider SDK only loads once the config
if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials as OAuth2Credentials
    from google.oauth2.service_account import Credentials as ServiceAccountCredentials
    from googleapiclient.discovery import Resource

# gate below has decided that this module has something to sync.
default = lazy_callable("google.auth", "default")
google_auth_exceptions = lazy_import("google.auth.exceptions")
googleapiclient = lazy_import("googleapiclient")
credentials = lazy_import("google.oauth2.credentials")
service_account = lazy_import("google.oauth2.service_account")
Request = lazy_callable("google.auth.transport.requests", "Request")
groups = lazy_import("cartography.intel.gsuite.groups")
users = lazy_import("cartography.intel.gsuite.users")

OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.user.readonly",
    "https://www.googleapis.com/auth/admin.directory.group.readonly",
    "https://www.googleapis.com/auth/admin.directory.group.member",
]

logger = logging.getLogger(__name__)

Resources = namedtuple("Resources", "admin")


def _get_admin_resource(
    credentials: "OAuth2Credentials | ServiceAccountCredentials",
) -> "Resource":
    """
    Instantiates a Google API resource object to call the Google API.
    Used to pull users and groups.  See https://developers.google.com/admin-sdk/directory/v1/guides/manage-users

    :param credentials: The credentials object
    :return: An admin api resource object
    """
    return googleapiclient.discovery.build(
        "admin",
        "directory_v1",
        credentials=credentials,
        cache_discovery=False,
    )


def _initialize_resources(
    credentials: "OAuth2Credentials | ServiceAccountCredentials",
) -> Resources:
    """
    Create namedtuple of all resource objects necessary for Google API data gathering.
    :param credentials: The credentials object
    :return: namedtuple of all resource objects
    """
    return Resources(
        admin=_get_admin_resource(credentials),
    )


@timeit
def start_gsuite_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Starts the GSuite ingestion process by initializing

    :param neo4j_session: The Neo4j session
    :param config: A `cartography.config` object
    :return: Nothing
    """
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    creds: "OAuth2Credentials | ServiceAccountCredentials"
    if config.gsuite_auth_method == "delegated":  # Legacy delegated method
        if config.gsuite_config is None or not os.path.isfile(config.gsuite_config):
            logger.warning(
                (
                    "The GSuite config file is not set or is not a valid file."
                    "Skipping GSuite ingestion."
                ),
            )
            return
        logger.info(
            "Attempting to authenticate to GSuite using legacy delegated method"
        )
        try:
            creds = service_account.Credentials.from_service_account_file(
                config.gsuite_config,
                scopes=OAUTH_SCOPES,
            )
            creds = creds.with_subject(os.environ.get("GSUITE_DELEGATED_ADMIN"))

        except google_auth_exceptions.DefaultCredentialsError as e:
            logger.error(
                (
                    "Unable to initialize GSuite creds. If you don't have GSuite data or don't want to load "
                    "Gsuite data then you can ignore this message. Otherwise, the error code is: %s "
                    "Make sure your GSuite credentials file (if any) is valid. "
                    "For more details see README"
                ),
                e,
            )
            return
    elif config.gsuite_auth_method == "oauth":
        auth_tokens = json.loads(str(base64.b64decode(config.gsuite_config).decode()))
        logger.info("Attempting to authenticate to GSuite using OAuth")
        try:
            creds = credentials.Credentials(
                token=None,
                client_id=auth_tokens["client_id"],
                client_secret=auth_tokens["client_secret"],
                refresh_token=auth_tokens["refresh_token"],
                expiry=None,
                token_uri=auth_tokens["token_uri"],
                scopes=OAUTH_SCOPES,
            )
            creds.refresh(Request())
        except google_auth_exceptions.DefaultCredentialsError as e:
            logger.error(
                (
                    "Unable to initialize GSuite creds. If you don't have GSuite data or don't want to load "
                    "Gsuite data then you can ignore this message. Otherwise, the error code is: %s "
                    "Make sure your GSuite credentials are configured correctly, your credentials are valid. "
                    "For more details see README"
                ),
                e,
            )
            return
    elif config.gsuite_auth_method == "default":
        logger.info("Attempting to authenticate to GSuite using default credentials")
        try:
            creds, _ = default(scopes=OAUTH_SCOPES)
        except google_auth_exceptions.DefaultCredentialsError as e:
            logger.error(
                (
                    "Unable to initialize GSuite creds using default credentials. If you don't have GSuite data or "
                    "don't want to load GSuite data then you can ignore this message. Otherwise, the error code is: %s "
                    "Make sure you have valid application default credentials configured. "
                    "For more details see README"
                ),
                e,
            )
            return

    logger.warning(
        "The GSuite module is deprecated and will no longer receive updates. It will be completely removed in the 1.0.0 release. "
        "For migration, please refer to the Google Workspace module configuration."
    )

    resources = _initialize_resources(creds)
    customer_ids = users.sync_gsuite_users(
        neo4j_session,
        resources.admin,
        config.update_tag,
        common_job_parameters,
    )
    for customer_id in customer_ids:
        scoped_job_parameters = common_job_parameters.copy()
        scoped_job_parameters["CUSTOMER_ID"] = customer_id
        groups.sync_gsuite_groups(
            neo4j_session,
            resources.admin,
            config.update_tag,
            scoped_job_parameters,
        )

    # DEPRECATED: compatibility migration for legacy RESOURCE edge direction. Remove in v1.0.0.
    run_analysis_job(
        "gsuite_resource_edge_direction_migration.json",
        neo4j_session,
        common_job_parameters,
    )

    # Link GSuite users to Human nodes if they exist
    run_typed_analysis_job(
        GSUITE_HUMAN_LINK,
        neo4j_session,
        common_job_parameters,
    )
