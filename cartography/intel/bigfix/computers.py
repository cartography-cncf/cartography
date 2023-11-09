import base64
import logging
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

import neo4j
import requests
import xmltodict

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.bigfix.bigfix_computer import BigfixComputerSchema
from cartography.models.bigfix.bigfix_root import BigfixRootSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)

DEFAULT_SUPPORTED_KEYS = {
    'Active Directory Path',
    'Agent Type',
    'Agent Version',
    'Average Evaluation Cycle',
    'BES Relay Selection Method',
    'BES Root Server',
    'BIOS',
    'Computer Name',
    'Computer Type',
    'CPU',
    'Device Type',
    'Distance to BES Relay',
    'DNS Name',
    'Enrollment Date',
    'Free Space on System Drive',
    'ID',
    'IP Address',
    'IPv6 Address',
    'Last Report Time',
    'Location By IP Range',
    'Locked',
    'Logged on User',
    'MAC Address',
    'OS',
    'Provider Name',
    'RAM',
    'Relay',
    'Remote Desktop Enabled',
    'Subnet Address',
    'Total Size of System Drive',
    'User Name',
}


@timeit
def sync(
        neo4j_session: neo4j.Session,
        bigfix_root_url: str,
        bigfix_username: str,
        bigfix_password: str,
        update_tag: int,
        common_job_parameters: Dict[str, Any],
        computer_keys: Optional[Set[str]] = None,
) -> None:
    if not computer_keys:
        computer_keys = DEFAULT_SUPPORTED_KEYS
    headers = _get_headers(bigfix_username, bigfix_password)
    computers = get(bigfix_root_url, headers, computer_keys)
    load_computers(neo4j_session, computers, bigfix_root_url, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(bigfix_api_url: str, headers: Dict[str, str], computer_keys: Set[str]) -> List[Dict[str, Any]]:
    result = []
    computer_list = get_computer_list(bigfix_api_url, headers)
    logger.info(f"Retrieving details for {len(computer_list)} BigFix Computers")
    for computer in computer_list:
        details = get_computer_details(bigfix_api_url, headers, computer['ID'], computer_keys)
        processed_comp: Dict[str, Any] = computer.copy()

        # Property names have spaces. Neo4j properties can't have spaces so let's clean this up.
        for key, val in details.items():
            transformed_key = key.replace(' ', '')
            processed_comp[transformed_key] = val

        # Post-processing transforms
        processed_comp['EnrollmentDateTime'] = datetime.strptime(
            processed_comp['EnrollmentDate'],
            "%a, %d %b %Y %H:%M:%S %z",
        )
        processed_comp['LastReportDateTime'] = datetime.strptime(
            processed_comp['LastReportTime'],
            "%a, %d %b %Y %H:%M:%S %z",
        )
        processed_comp['RemoteDesktopIsEnabled'] = processed_comp['RemoteDesktopEnabled'] == 'True'
        processed_comp['IsLocked'] = processed_comp['Locked'] == 'Yes'

        result.append(processed_comp)
    return result


def get_computer_list(bigfix_api_url: str, headers: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Returned shape: [
      {'@Resource': 'https://{URI}/api/computer/123', 'LastReportTime': 'Tue, 18 Apr 2023 21:59:44 +0000', 'ID': '123'},
    ]
    """
    xml_text = _get_computer_list_raw_xml(bigfix_api_url, headers)
    as_dict = xmltodict.parse(xml_text)
    return as_dict['BESAPI']['Computer']


def get_computer_details(
        bigfix_api_url: str,
        headers: Dict[str, str],
        computer_id: str,
        computer_keys: Set[str],
) -> Dict[str, Any]:
    xml_text = _get_computer_details_raw_xml(bigfix_api_url, headers, computer_id)
    as_dict = xmltodict.parse(xml_text)
    processed_computer = {}
    for prop in as_dict['BESAPI']['Computer']['Property']:
        prop_name = prop['@Name']
        if prop_name in computer_keys:
            processed_computer[prop_name] = prop['#text']
    return processed_computer


def _get_computer_list_raw_xml(bigfix_api_url: str, headers: Dict[str, str]) -> str:
    list_endpoint = f"{bigfix_api_url}/api/computers"
    resp = requests.get(list_endpoint, headers=headers, verify=False, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def _get_computer_details_raw_xml(bigfix_api_url: str, headers: Dict[str, str], computer_id: str) -> str:
    details_endpoint = f"{bigfix_api_url}/api/computer/{computer_id}"
    resp = requests.get(details_endpoint, headers=headers, verify=False, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.text


@timeit
def load_computers(
        neo4j_session: neo4j.Session,
        data: List[Dict[str, Any]],
        bigfix_root_url: str,
        update_tag: int,
) -> None:
    load(
        neo4j_session,
        BigfixRootSchema(),
        [{'id': bigfix_root_url}],
        lastupdated=update_tag,
    )

    logger.info(f"Loading {len(data)} BigFix computers to the graph")
    load(
        neo4j_session,
        BigfixComputerSchema(),
        data,
        lastupdated=update_tag,
        ROOT_URL=bigfix_root_url,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(BigfixComputerSchema(), common_job_parameters).run(neo4j_session)


def _get_headers(bigfix_username: str, bigfix_password: str) -> Dict[str, str]:
    creds = {"username": bigfix_username, "password": bigfix_password}
    bigfix_creds = base64.b64encode(
        f"{creds['username']}:{creds['password']}".encode(),
    )
    headers = {
        "Authorization": f"Basic {bigfix_creds.decode()}",
        "Accept": "application/json",
    }
    return headers
