import logging
from typing import Any
from urllib.parse import urlsplit

import neo4j
import requests
from azure.core.credentials import TokenCredential
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from cartography.client.core.tx import load
from cartography.config import Config
from cartography.graph.job import GraphJob
from cartography.intel.microsoft import credentials
from cartography.models.microsoft.defender import DefenderAlertSchema
from cartography.models.microsoft.defender import DefenderMachineSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
MACHINES_URL = "https://api.security.microsoft.com/api/machines"
ALERTS_URL = "https://graph.microsoft.com/v1.0/security/alerts_v2"
# The MDE API still requires the legacy resource audience, even on its new host.
MDE_SCOPE = "https://api.securitycenter.microsoft.com/.default"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"
MACHINE_PAGE_SIZE = 10000
ALERT_FILTER = (
    "serviceSource eq 'microsoftDefenderForEndpoint' and status ne 'resolved'"
)


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    session.mount(
        "https://",
        HTTPAdapter(
            max_retries=Retry(
                total=5,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET"],
            ),
        ),
    )
    return session


def get_collection(
    session: requests.Session,
    credential: TokenCredential,
    url: str,
    scope: str,
    params: dict[str, Any],
    *,
    use_skip: bool = False,
) -> list[dict[str, Any]]:
    """Read a complete collection; malformed or incomplete responses are fatal."""
    endpoint = urlsplit(url)
    query: dict[str, Any] | None = dict(params)
    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_links: set[str] = set()
    while True:
        # Azure Identity caches tokens and refreshes them when necessary.
        token = credential.get_token(scope).token
        response = session.get(
            url,
            params=query,
            headers={"Authorization": f"Bearer {token}"},
            timeout=(10, 60),
            allow_redirects=False,
        )
        response.raise_for_status()
        if response.status_code != 200:
            raise ValueError("Defender API returned an unexpected HTTP status")
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("value"), list):
            raise ValueError("Defender API response is missing its value collection")
        items = payload["value"]
        for item in items:
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("id"), str)
                or not item["id"]
            ):
                raise ValueError("Defender API returned a record without an ID")
            if item["id"] in seen_ids:
                raise ValueError("Defender API pagination repeated a record")
            seen_ids.add(item["id"])
        results.extend(items)
        next_link = payload.get("@odata.nextLink")
        if next_link is not None:
            if not isinstance(next_link, str) or not next_link:
                raise ValueError("Defender API returned an invalid nextLink")
            next_url = urlsplit(next_link)
            if (
                next_url.scheme != endpoint.scheme
                or next_url.netloc != endpoint.netloc
                or next_url.path != endpoint.path
                or next_url.fragment
                or next_link in seen_links
            ):
                raise ValueError("Defender API returned an unsafe or repeated nextLink")
            seen_links.add(next_link)
            url, query = next_link, None
        elif use_skip and len(items) == params["$top"]:
            # MDE documents $top/$skip; a full page without nextLink is not EOF.
            url = endpoint.geturl()
            query = {**params, "$skip": len(results)}
        else:
            return results


@timeit
def get_machines(
    session: requests.Session, credential: TokenCredential
) -> list[dict[str, Any]]:
    return get_collection(
        session,
        credential,
        MACHINES_URL,
        MDE_SCOPE,
        {"$top": MACHINE_PAGE_SIZE},
        use_skip=True,
    )


@timeit
def get_alerts(
    session: requests.Session, credential: TokenCredential
) -> list[dict[str, Any]]:
    return get_collection(
        session,
        credential,
        ALERTS_URL,
        GRAPH_SCOPE,
        {"$top": 100, "$filter": ALERT_FILTER},
    )


def transform_machines(
    machines: list[dict[str, Any]], tenant_id: str
) -> list[dict[str, Any]]:
    return [
        {
            **machine,
            "id": f"{tenant_id}/{machine['id']}",
            "machine_id": machine["id"],
            "aadDeviceId": (
                machine.get("aadDeviceId") or None
                if machine.get("aadDeviceId") != "00000000-0000-0000-0000-000000000000"
                else None
            ),
        }
        for machine in machines
    ]


def transform_alerts(
    alerts: list[dict[str, Any]], tenant_id: str
) -> list[dict[str, Any]]:
    result = []
    for alert in alerts:
        if alert.get("tenantId") not in (None, tenant_id):
            raise ValueError("Defender alert belongs to a different tenant")
        evidence = alert.get("evidence", [])
        if not isinstance(evidence, list) or any(
            not isinstance(item, dict) for item in evidence
        ):
            raise ValueError("Defender alert evidence is not a collection")
        result.append(
            {
                **alert,
                "id": f"{tenant_id}/{alert['id']}",
                "alert_id": alert["id"],
                "machine_ids": sorted(
                    {
                        f"{tenant_id}/{item['mdeDeviceId']}"
                        for item in evidence
                        if item.get("@odata.type")
                        == "#microsoft.graph.security.deviceEvidence"
                        and item.get("mdeDeviceId")
                    }
                ),
            },
        )
    return result


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    credential: TokenCredential,
    tenant_id: str,
    update_tag: int,
) -> None:
    # Finish both API reads and transforms before any writes or cleanup. A failed
    # alert page must not remove machines referenced by the previous alert data.
    machines = transform_machines(get_machines(session, credential), tenant_id)
    alerts = transform_alerts(get_alerts(session, credential), tenant_id)
    for schema, data in (
        (DefenderMachineSchema(), machines),
        (DefenderAlertSchema(), alerts),
    ):
        load(neo4j_session, schema, data, lastupdated=update_tag, TENANT_ID=tenant_id)
    parameters = {"TENANT_ID": tenant_id, "UPDATE_TAG": update_tag}
    for schema in (DefenderAlertSchema(), DefenderMachineSchema()):
        GraphJob.from_node_schema(schema, parameters).run(neo4j_session)


@timeit
def start_defender_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.microsoft_defender:
        logger.info("Microsoft Defender import is not enabled - skipping")
        return
    tenant_id = config.microsoft_tenant_id
    client_id = config.microsoft_client_id
    client_secret = config.microsoft_client_secret
    if not tenant_id or not client_id or not client_secret:
        raise ValueError(
            "Microsoft Defender requires Microsoft service principal credentials"
        )
    credential = credentials.make_credential(
        tenant_id,
        client_id,
        client_secret,
    )
    with create_session() as session:
        sync(
            neo4j_session,
            session,
            credential,
            tenant_id,
            config.update_tag,
        )
