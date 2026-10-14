import logging
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

import neo4j
import requests
from azure.core.credentials import TokenCredential
from azure.core.exceptions import ClientAuthenticationError
from dateutil.parser import isoparse
from requests.adapters import HTTPAdapter

from cartography.client.core.tx import load
from cartography.client.http import CappedRetry
from cartography.config import Config
from cartography.graph.job import GraphJob
from cartography.intel.microsoft import credentials
from cartography.intel.microsoft.util import normalize_azure_ad_device_id
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.microsoft.defender import DefenderAlertSchema
from cartography.models.microsoft.defender import DefenderMachineSchema
from cartography.util import DEFAULT_MAX_PAGES
from cartography.util import timeit

logger = logging.getLogger(__name__)
MACHINES_URL = "https://api.security.microsoft.com/api/machines"
ALERTS_URL = "https://graph.microsoft.com/v1.0/security/alerts_v2"
# The MDE API still requires the legacy resource audience, even on its new host.
MDE_SCOPE = "https://api.securitycenter.microsoft.com/.default"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"
MACHINE_PAGE_SIZE = 10000
# Token error when the tenant has no Defender for Endpoint service principal.
RESOURCE_NOT_PROVISIONED = "AADSTS500011"
# alerts_v2 documents only `eq` filters, so each unresolved status is queried separately.
UNRESOLVED_ALERT_STATUSES = ("new", "inProgress")


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    session.mount(
        "https://",
        HTTPAdapter(
            max_retries=CappedRetry(
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
    for _ in range(DEFAULT_MAX_PAGES):
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
    raise ValueError("Defender API exceeded the pagination limit; snapshot incomplete")


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
    alerts: dict[str, dict[str, Any]] = {}
    for status in UNRESOLVED_ALERT_STATUSES:
        for alert in get_collection(
            session,
            credential,
            ALERTS_URL,
            GRAPH_SCOPE,
            {
                "$top": 100,
                "$filter": (
                    "serviceSource eq 'microsoftDefenderForEndpoint' "
                    f"and status eq '{status}'"
                ),
            },
        ):
            # An alert whose status changes between queries can appear in both.
            alerts[alert["id"]] = alert
    return list(alerts.values())


def transform_machines(
    machines: list[dict[str, Any]], tenant_id: str
) -> list[dict[str, Any]]:
    result = []
    for machine in machines:
        normalized_id = normalize_azure_ad_device_id(machine.get("aadDeviceId"))
        data = {
            **machine,
            "id": f"{tenant_id}/{machine['id']}",
            "machine_id": machine["id"],
            "aadDeviceId": machine.get("aadDeviceId") if normalized_id else None,
            "aad_device_id_normalized": normalized_id,
        }
        _parse_timestamps(data, ("firstSeen", "lastSeen"))
        result.append(data)
    return result


def _parse_timestamps(record: dict[str, Any], fields: tuple[str, ...]) -> None:
    """Convert optional provider metadata without discarding valid inventory."""
    for field in fields:
        value = record.get(field)
        record[field] = None
        if value is None or value == "":
            continue
        try:
            # RFC 3339 allows lowercase t/z, which fromisoformat rejects.
            parsed = isoparse(value)
            if parsed.tzinfo is None:
                raise ValueError("Expected a timezone in the provider timestamp")
            record[field] = parsed
        except (TypeError, ValueError):
            logger.warning(
                "Defender record %s has invalid %s; omitting optional timestamp",
                record["id"],
                field,
            )


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
        _parse_timestamps(result[-1], ("createdDateTime", "lastUpdateDateTime"))
    return result


def _fetch_optional(
    name: str,
    permission: str,
    fetch: Callable[[], list[dict[str, Any]]],
) -> list[dict[str, Any]] | None:
    """Return a complete collection, or None when the tenant can't provide it.

    Missing provisioning or permissions skip the collection without cleanup, like
    optional Entra datasets. Any other failure propagates.
    """
    try:
        return fetch()
    except ClientAuthenticationError as e:
        if RESOURCE_NOT_PROVISIONED not in str(e):
            raise
        logger.info(
            "Defender for Endpoint is not provisioned in this tenant; skipping "
            "Defender %s.",
            name,
        )
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        if status in (401, 403):
            logger.warning(
                "Defender %s request was denied (%d). Grant the %s application "
                "permission to sync them. Skipping; previously synced Defender "
                "%s are preserved.",
                name,
                status,
                permission,
                name,
            )
        elif status == 404 and name == "machines":
            # Microsoft documents 404 when the tenant has no recent machines.
            logger.warning(
                "Defender returned no recent machines (404). Skipping; previously "
                "synced Defender machines are preserved.",
            )
        else:
            raise
    return None


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    credential: TokenCredential,
    tenant_id: str,
    update_tag: int,
) -> None:
    # Finish both API reads and transforms before any writes or cleanup, so a
    # failed read leaves the previous snapshot intact. A skipped collection is
    # neither loaded nor cleaned up.
    raw_machines = _fetch_optional(
        "machines",
        "WindowsDefenderATP Machine.Read.All",
        lambda: get_machines(session, credential),
    )
    raw_alerts = _fetch_optional(
        "alerts",
        "Microsoft Graph SecurityAlert.Read.All",
        lambda: get_alerts(session, credential),
    )
    collections: list[tuple[CartographyNodeSchema, list[dict[str, Any]]]] = []
    if raw_machines is not None:
        collections.append(
            (DefenderMachineSchema(), transform_machines(raw_machines, tenant_id))
        )
    if raw_alerts is not None:
        collections.append(
            (DefenderAlertSchema(), transform_alerts(raw_alerts, tenant_id))
        )
    for schema, data in collections:
        load(neo4j_session, schema, data, lastupdated=update_tag, TENANT_ID=tenant_id)
    parameters = {"TENANT_ID": tenant_id, "UPDATE_TAG": update_tag}
    for schema, _ in reversed(collections):
        GraphJob.from_node_schema(schema, parameters).run(neo4j_session)


@timeit
def start_defender_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
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
