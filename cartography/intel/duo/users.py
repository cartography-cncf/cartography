import logging
from json import dumps
from typing import Any
from typing import Dict
from typing import List

import duo_client
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.duo.user import DuoUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_duo_users(
    client: duo_client.Admin,
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    '''
    Sync Duo Users
    '''
    users = _get_users(client)
    transformed_users = _transform_users(users)
    _load_users(neo4j_session, transformed_users, common_job_parameters)
    _cleanup_users(neo4j_session, common_job_parameters)


@timeit
def _get_users(client: duo_client.Admin) -> List[Dict[str, Any]]:
    '''
    Fetch all users data
    https://duo.com/docs/adminapi#users
    '''
    logger.info("Fetching Duo users")
    return client.get_users()


@timeit
def _transform_users(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    '''
    Reformat the data before loading
    '''
    logger.info(f'Transforming {len(users)} duo users')
    transformed_users = []
    for user in users:
        transformed_user = {
            'alias1': user['alias1'],
            'alias2': user['alias2'],
            'alias3': user['alias3'],
            'alias4': user['alias4'],
            'created': user['created'],
            'email': user['email'],
            'firstname': user['firstname'],
            'is_enrolled': user['is_enrolled'],
            'last_directory_sync': user['last_directory_sync'],
            'last_login': user['last_login'],
            'lastname': user['lastname'],
            'notes': user['notes'],
            'phones': [
                dumps({
                    **phone,
                    'number': None,
                })
                for phone in user['phones']
            ],
            'realname': user['realname'],
            'status': user['status'],
            'tokens': [dumps(token) for token in user['tokens']],
            'u2ftokens': [dumps(u2ftoken) for u2ftoken in user['u2ftokens']],
            'user_id': user['user_id'],
            'username': user['username'],
            'webauthncredentials': [
                dumps(webauthncredential)
                for webauthncredential
                in user['webauthncredentials']
            ],
        }
        transformed_users.append(transformed_user)
        for group in user['groups']:
            match_user = {
                **transformed_user,
                'group_id': group['group_id'],
            }
            transformed_users.append(match_user)
        for phone in user['phones']:
            match_user = {
                **transformed_user,
                'phone_id': phone['phone_id'],
            }
            transformed_users.append(match_user)
        for token in user['tokens']:
            match_user = {
                **transformed_user,
                'token_id': token['token_id'],
            }
            transformed_users.append(match_user)
        for webauthncredential in user['webauthncredentials']:
            match_user = {
                **transformed_user,
                'webauthnkey': webauthncredential['webauthnkey'],
            }
            transformed_users.append(match_user)
    return transformed_users


@timeit
def _load_users(
    neo4j_session: neo4j.Session,
    users: List[Dict[str, Any]],
    common_job_parameters: Dict[str, Any],
) -> None:
    '''
    Load the users into the database
    '''
    logger.info(f'Loading {len(users)} duo users')
    load(
        neo4j_session,
        DuoUserSchema(),
        users,
        DUO_API_HOSTNAME=common_job_parameters['DUO_API_HOSTNAME'],
        lastupdated=common_job_parameters['UPDATE_TAG'],
    )


@timeit
def _cleanup_users(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    '''
    Cleanup endpoints
    '''
    GraphJob.from_node_schema(DuoUserSchema(), common_job_parameters).run(neo4j_session)
