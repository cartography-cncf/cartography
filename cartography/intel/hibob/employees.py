import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Set
from typing import Tuple

import neo4j
from dateutil import parser as dt_parse
from requests import Session

from cartography.client.core.tx import load_graph_data
from cartography.graph.querybuilder import build_ingestion_query
from cartography.models.hibob.company import HiBobCompanySchema
from cartography.models.hibob.department import HiBobDepartmentSchema
from cartography.models.hibob.employee import HiBobEmployeeSchema
from cartography.models.hibob.human import HumanSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    data = get(api_session)
    companies, departments, employees = transform(data)
    load(neo4j_session, companies, departments, employees, common_job_parameters)


@timeit
def get(api_session: Session) -> Dict[str, Any]:
    req = api_session.get('https://api.hibob.com/v1/people', params={'humanReadable': 'true'}, timeout=_TIMEOUT)
    req.raise_for_status()
    return req.json()


@timeit
def transform(response_objects: Dict[str, List]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """  Strips list of API response objects to return list of group objects only
    :param response_objects:
    :return: list of dictionary objects as defined in /docs/schema/hibob.md
    """
    companies = {}
    departments = {}
    users: List[Dict] = []

    transformed_users = {}

    for user in response_objects['employees']:
        # Extract company
        if user['companyId'] not in companies:
            companies[user['companyId']] = {'id': user['companyId']}
        # Extract department
        if user['work']['department'] not in departments:
            departments[user['work']['department']] = {
                'id': user['work']['department'],
                'name': user['work']['department'],
                'company_id': user['companyId'],
            }
        # Add junk reportsTo id if needed
        if 'reportsTo' not in user['work']:
            user['work']['reportsTo'] = None
        user['work']['startDate'] = int(dt_parse.parse(user['work']['startDate']).timestamp() * 1000)
        transformed_users[user['id']] = user

    # Order users to ensure work.reportsTo refer to an existing user
    seen_users: Set[str] = set()
    initial_len = len(transformed_users)
    while len(transformed_users) > 0:
        for uid in list(transformed_users.keys()):
            user = transformed_users[uid]
            if user['work']['reportsTo'] is None:
                users.append(user)
                transformed_users.pop(uid)
                seen_users.add(user['displayName'])
            elif user['work']['reportsTo'] in seen_users:
                users.append(user)
                transformed_users.pop(uid)
                seen_users.add(user['displayName'])
        # Avoid infinite loop
        if initial_len == len(transformed_users):
            users += transformed_users

    return list(companies.values()), list(departments.values()), users


def load(
    neo4j_session: neo4j.Session,
    companies: List[Dict],
    departments: List[Dict],
    employees: List[Dict],
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Transform and load employees information
    """

    # Humans
    query_humans = build_ingestion_query(HumanSchema())
    load_graph_data(
        neo4j_session,
        query_humans,
        employees,
        lastupdated=common_job_parameters['UPDATE_TAG'],
    )
    # Employees
    query_employees = build_ingestion_query(HiBobEmployeeSchema())
    load_graph_data(
        neo4j_session,
        query_employees,
        employees,
        lastupdated=common_job_parameters['UPDATE_TAG'],
    )
    # Departments
    query_departments = build_ingestion_query(HiBobDepartmentSchema())
    load_graph_data(
        neo4j_session,
        query_departments,
        departments,
        lastupdated=common_job_parameters['UPDATE_TAG'],
    )
    # Companies
    query_companies = build_ingestion_query(HiBobCompanySchema())
    load_graph_data(
        neo4j_session,
        query_companies,
        companies,
        lastupdated=common_job_parameters['UPDATE_TAG'],
    )
