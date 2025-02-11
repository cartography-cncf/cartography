import base64
import json
import logging
import os
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

from cartography.config import Config
from cartography.intel.gsuite import api
from cartography.util import timeit

OAUTH_SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.user.readonly',
    'https://www.googleapis.com/auth/admin.directory.group.readonly',
    'https://www.googleapis.com/auth/admin.directory.group.member',
    'https://www.googleapis.com/auth/cloud-platform',
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

    creds: OAuth2Credentials | ServiceAccountCredentials
    if config.gsuite_auth_method == 'delegated':  # Legacy delegated method
        logger.info('Attempting to authenticate to GSuite using legacy delegated method')
        try:
            creds = service_account.Credentials.from_service_account_file(
                config.gsuite_config,
                scopes=OAUTH_SCOPES,
            )
            creds = creds.with_subject(os.environ.get('GSUITE_DELEGATED_ADMIN'))

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
    elif config.gsuite_auth_method == 'oauth':
        auth_tokens = json.loads(str(base64.b64decode(config.gsuite_config).decode()))
        logger.info('Attempting to authenticate to GSuite using OAuth')
        try:
            creds = credentials.Credentials(
                token=None,
                client_id=auth_tokens['client_id'],
                client_secret=auth_tokens['client_secret'],
                refresh_token=auth_tokens['refresh_token'],
                expiry=None,
                token_uri=auth_tokens['token_uri'],
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
    elif config.gsuite_auth_method == 'default':
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
    api.sync_gsuite_users(neo4j_session, resources.admin, config.update_tag, common_job_parameters)
    api.sync_gsuite_groups(neo4j_session, resources.admin, config.update_tag, common_job_parameters)
