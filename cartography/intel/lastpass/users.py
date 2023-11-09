import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from dateutil import parser as dt_parse
from requests import Session

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.lastpass.tenant import LastpassTenantSchema
from cartography.models.lastpass.user import LastpassUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    lastpass_provhash: str,
    tenant_id: int,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    users = get(lastpass_provhash, tenant_id)
    formated_users = transform(users)
    load_users(neo4j_session, formated_users, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(lastpass_provhash: str, tenant_id: int) -> Dict[str, Any]:
    payload = {
        'cid': tenant_id,
        'provhash': lastpass_provhash,
        'cmd': 'getuserdata',
        'data': None,
    }
    session = Session()
    req = session.post('https://lastpass.com/enterpriseapi.php', data=payload, timeout=_TIMEOUT)
    req.raise_for_status()
    return req.json()


@timeit
def transform(api_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for uid, user in api_result['Users'].items():
        n_user = user.copy()
        n_user['id'] = int(uid)
        for k in ('created', 'last_pw_change', 'last_login'):
            n_user[k] = int(dt_parse.parse(user[k]).timestamp() * 1000) if user[k] else None
        result.append(n_user)
    return result


def load_users(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    tenant_id: int,
    update_tag: int,
) -> None:

    load(
        neo4j_session,
        LastpassTenantSchema(),
        [{'id': tenant_id}],
        lastupdated=update_tag,
    )

    load(
        neo4j_session,
        LastpassUserSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(LastpassUserSchema(), common_job_parameters).run(neo4j_session)
