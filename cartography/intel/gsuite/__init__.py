import logging
from collections import namedtuple

import googleapiclient.discovery
import neo4j
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError
from google.auth.transport.requests import Request
from google.oauth2 import credentials
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as OAuth2Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import Resource

from cartography.intel.gsuite import api
from cartography.settings import check_module_settings
from cartography.settings import settings
from cartography.util import timeit

OAUTH_SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.user.readonly',
    'https://www.googleapis.com/auth/admin.directory.group.readonly',
    'https://www.googleapis.com/auth/admin.directory.group.member',
]

logger = logging.getLogger(__name__)

Resources = namedtuple('Resources', 'admin')


def _get_admin_resource(credentials: OAuth2Credentials | ServiceAccountCredentials) -> Resource:
    """
    Instantiates a Google API resource object to call the Google API.
    Used to pull users and groups.  See https://developers.google.com/admin-sdk/directory/v1/guides/manage-users

    :param credentials: The credentials object
    :return: An admin api resource object
    """
    return googleapiclient.discovery.build('admin', 'directory_v1', credentials=credentials, cache_discovery=False)


def _initialize_resources(credentials: OAuth2Credentials | ServiceAccountCredentials) -> Resources:
    """
    Create namedtuple of all resource objects necessary for Google API data gathering.
    :param credentials: The credentials object
    :return: namedtuple of all resource objects
    """
    return Resources(
        admin=_get_admin_resource(credentials),
    )


@timeit
def start_gsuite_ingestion(neo4j_session: neo4j.Session) -> None:
    """
    Starts the GSuite ingestion process by initializing

    :param neo4j_session: The Neo4j session
    :return: Nothing
    """
    if not check_module_settings('GSuite', ['auth_method']):
        return

    common_job_parameters = {
        "UPDATE_TAG": settings.common.update_tag,
    }

    creds: OAuth2Credentials | ServiceAccountCredentials
    if settings.gsuite.auth_method == 'delegated':  # Legacy delegated method
        logger.info('Attempting to authenticate to GSuite using legacy delegated method')
        if not check_module_settings('GSuite', ['settings_account_file', 'delegated_admin']):
            return
        try:
            creds = service_account.Credentials.from_service_account_file(
                settings.gsuite.settings_account_file,
                scopes=OAUTH_SCOPES,
            )
            creds = creds.with_subject(settings.gsuite.delegated_admin)

        except DefaultCredentialsError as e:
            logger.error(
                (
                    "Unable to initialize GSuite creds. If you don't have GSuite data or don't want to load "
                    'Gsuite data then you can ignore this message. Otherwise, the error code is: %s '
                    'Make sure your GSuite credentials file (if any) is valid. '
                    'For more details see README'
                ),
                e,
            )
            return
    elif settings.gsuite.auth_method == 'oauth':
        logger.info('Attempting to authenticate to GSuite using OAuth')
        if not check_module_settings('GSuite', ['client_id', 'client_secret', 'refresh_token', 'token_uri']):
            return
        try:
            creds = credentials.Credentials(
                token=None,
                client_id=settings.gsuite.client_id,
                client_secret=settings.gsuite.client_secret,
                refresh_token=settings.gsuite.refresh_token,
                expiry=None,
                token_uri=settings.gsuite.token_uri,
                scopes=OAUTH_SCOPES,
            )
            creds.refresh(Request())
            creds = creds.create_scoped(OAUTH_SCOPES)
        except DefaultCredentialsError as e:
            logger.error(
                (
                    "Unable to initialize GSuite creds. If you don't have GSuite data or don't want to load "
                    'Gsuite data then you can ignore this message. Otherwise, the error code is: %s '
                    'Make sure your GSuite credentials are configured correctly, your credentials are valid. '
                    'For more details see README'
                ),
                e,
            )
            return
    elif settings.gsuite.auth_method == 'default':
        logger.info('Attempting to authenticate to GSuite using default credentials')
        try:
            creds, _ = default(scopes=OAUTH_SCOPES)
        except DefaultCredentialsError as e:
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

    resources = _initialize_resources(creds)
    api.sync_gsuite_users(neo4j_session, resources.admin, settings.common.update_tag, common_job_parameters)
    api.sync_gsuite_groups(neo4j_session, resources.admin, settings.common.update_tag, common_job_parameters)
