import datetime
import hashlib
import ipaddress
import json
import logging
from collections import defaultdict
from typing import Any
from urllib.parse import urlsplit
from urllib.parse import urlunsplit

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.client.core.tx import run_write_query
from cartography.config import Config
from cartography.graph.job import GraphJob
from cartography.intel.common.object_store import filter_report_refs
from cartography.intel.common.object_store import read_text_report
from cartography.intel.common.object_store import ReportReader
from cartography.intel.common.report_reader_builder import (
    build_report_reader_for_source,
)
from cartography.intel.common.report_source import parse_report_source
from cartography.models.bbot.events import BBOT_SCHEMAS
from cartography.models.bbot.events import BbotCleanupSchema
from cartography.models.bbot.events import BbotMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)

_LIST_FIELDS = (
    "bbot_ids",
    "occurrence_uuids",
    "parent_uuids",
    "tags",
    "modules",
    "resolved_hosts",
    "discovery_contexts",
)
_FINDING_TARGET_LABELS = {
    "BbotDNSName",
    "BbotIPAddress",
    "BbotOpenTCPPort",
    "BbotStorageBucket",
    "BbotURL",
}


def _event_data(event: dict[str, Any]) -> str | dict[str, Any]:
    data = event.get("data_json", event.get("data"))
    if not isinstance(data, (str, dict)):
        raise ValueError(
            f"BBOT {event.get('type', 'unknown')} event data must be a string or object",
        )
    return data


def _fingerprint(event_type: str, parts: list[str]) -> str:
    payload = json.dumps(parts, separators=(",", ":"), ensure_ascii=True)
    return f"{event_type}:{hashlib.sha256(payload.encode()).hexdigest()}"


def _canonical_url(value: str) -> str:
    value = value.strip()
    parsed = urlsplit(value)
    if not parsed.scheme or not parsed.hostname:
        return value
    host = parsed.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    port = parsed.port
    if (parsed.scheme.lower(), port) in {("http", 80), ("https", 443)}:
        port = None
    netloc = f"{host}:{port}" if port is not None else host
    return urlunsplit(
        (parsed.scheme.lower(), netloc, parsed.path or "/", parsed.query, ""),
    )


def _extract_url(data: str | dict[str, Any]) -> str | None:
    value = data.get("url") if isinstance(data, dict) else data
    return _canonical_url(value) if isinstance(value, str) and value else None


def _normalize_host(value: str) -> str:
    try:
        return ipaddress.ip_address(value).compressed
    except ValueError:
        return value.rstrip(".").lower()


def _normalize_text(value: Any) -> str:
    return " ".join(str(value).split()).casefold()


def _finding_target(event: dict[str, Any], data: dict[str, Any]) -> str:
    url = data.get("full_url") or data.get("url")
    if isinstance(url, str) and url:
        return _canonical_url(url)

    host = data.get("host") or event.get("host")
    if isinstance(host, str) and host:
        normalized_host = _normalize_host(host)
        port = data.get("port") or event.get("port")
        if isinstance(port, int):
            if ":" in normalized_host:
                normalized_host = f"[{normalized_host}]"
            return f"{normalized_host}:{port}"
        return normalized_host

    parent_id = event.get("parent")
    return str(parent_id) if parent_id else ""


def _bucket_provider(event: dict[str, Any], data: dict[str, Any]) -> str:
    explicit_provider = data.get("provider")
    if isinstance(explicit_provider, str) and explicit_provider.strip():
        provider = explicit_provider.strip().lower()
        return {
            "amazon": "aws",
            "google": "gcp",
            "microsoft": "azure",
        }.get(provider, provider)

    value = f"{event.get('module', '')} {data.get('url', '')}".lower()
    providers = {
        "amazon": "aws",
        "amazonaws.com": "aws",
        "google": "gcp",
        "googleapis.com": "gcp",
        "firebase": "gcp",
        "microsoft": "azure",
        "blob.core.windows.net": "azure",
        "digitalocean": "digitalocean",
        "digitaloceanspaces.com": "digitalocean",
        "hetzner": "hetzner",
    }
    for marker, provider in providers.items():
        if marker in value:
            return provider
    url = data.get("url")
    if isinstance(url, str):
        hostname = urlsplit(url).hostname
        if hostname:
            return hostname.lower()
    return str(event.get("module") or "unknown").lower()


def _stable_identity(
    event: dict[str, Any],
    data: str | dict[str, Any],
) -> str:
    event_type = event["type"]
    bbot_id = event["id"]
    if not isinstance(bbot_id, str) or not bbot_id:
        raise ValueError(f"BBOT {event_type} event is missing id")

    if event_type == "SOCIAL":
        if not isinstance(data, dict):
            raise ValueError("BBOT SOCIAL event data must be an object")
        platform = _normalize_text(data.get("platform") or "unknown")
        profile = _extract_url(data) or _normalize_text(data.get("profile_name") or "")
        if not profile:
            raise ValueError("BBOT SOCIAL event is missing profile URL and name")
        return _fingerprint(event_type, [platform, profile])

    if event_type == "STORAGE_BUCKET":
        if not isinstance(data, dict) or not data.get("name"):
            raise ValueError("BBOT STORAGE_BUCKET event is missing name")
        provider = _bucket_provider(event, data)
        return f"{event_type}:{provider}:{str(data['name']).strip().lower()}"

    if event_type == "FINDING":
        if not isinstance(data, dict):
            raise ValueError("BBOT FINDING event data must be an object")
        name = data.get("name") or data.get("description")
        if not name:
            raise ValueError("BBOT FINDING event is missing name and description")
        target = _finding_target(event, data)
        if not target:
            raise ValueError("BBOT FINDING event is missing an affected target")
        return _fingerprint(
            event_type,
            [
                _normalize_text(event.get("module") or "unknown"),
                target,
                _normalize_text(name),
            ],
        )

    return bbot_id


def _event_properties(
    event: dict[str, Any],
    data: str | dict[str, Any],
    stable_id: str,
    source_uri: str,
) -> dict[str, Any]:
    event_type = event["type"]
    object_data = data if isinstance(data, dict) else {}
    host_value = event.get("host") or object_data.get("host")
    port_value = (
        event.get("port") if event.get("port") is not None else object_data.get("port")
    )
    host = _normalize_host(host_value) if isinstance(host_value, str) else None
    url = (
        _extract_url(data)
        if event_type in {"FINDING", "SOCIAL", "STORAGE_BUCKET", "URL"}
        else None
    )
    module = event.get("module")
    event_uuid = event.get("uuid")
    parent_uuid = event.get("parent_uuid")
    context = event.get("discovery_context")
    raw_data = (
        json.dumps(data, sort_keys=True, separators=(",", ":"))
        if isinstance(data, dict)
        else data
    )

    result: dict[str, Any] = {
        "id": stable_id,
        "bbot_ids": [event["id"]],
        "event_type": event_type,
        "data": raw_data,
        "host": host,
        "port": port_value,
        "url": url,
        "scan_id": event.get("scan") or (stable_id if event_type == "SCAN" else None),
        "occurrence_uuids": [event_uuid] if isinstance(event_uuid, str) else [],
        "occurrence_count": 1,
        "parent_uuids": [parent_uuid] if isinstance(parent_uuid, str) else [],
        "tags": sorted(str(tag) for tag in event.get("tags", []) if tag is not None),
        "modules": [str(module)] if module else [],
        "resolved_hosts": sorted(
            str(value) for value in event.get("resolved_hosts", []) if value is not None
        ),
        "discovery_contexts": [str(context)] if context else [],
        "scope_distance": event.get("scope_distance"),
        "web_spider_distance": event.get("web_spider_distance"),
        "observed_at": event.get("timestamp"),
        "source_uri": source_uri,
    }

    if event_type == "SCAN":
        target = object_data.get("target")
        result.update(
            {
                "name": object_data.get("name"),
                "status": object_data.get("status"),
                "started_at": object_data.get("started_at"),
                "finished_at": object_data.get("finished_at"),
                "duration_seconds": object_data.get("duration_seconds"),
                "targets": target.get("seeds", []) if isinstance(target, dict) else [],
            },
        )
    elif event_type == "DNS_NAME":
        result["name"] = _normalize_host(str(data))
    elif event_type == "IP_ADDRESS":
        address = ipaddress.ip_address(str(data))
        result.update(
            {"ip_address": address.compressed, "is_global": address.is_global}
        )
    elif event_type == "IP_RANGE":
        result["network"] = str(ipaddress.ip_network(str(data), strict=False))
    elif event_type == "OPEN_TCP_PORT":
        if not host or not isinstance(port_value, int):
            raise ValueError("BBOT OPEN_TCP_PORT event is missing host or port")
        result["endpoint"] = str(data)
    elif event_type == "URL":
        result["name"] = url
    elif event_type == "ASN":
        result.update(
            {
                "asn": (
                    str(object_data.get("asn"))
                    if object_data.get("asn") is not None
                    else None
                ),
                "name": object_data.get("name"),
                "country": object_data.get("country"),
                "description": object_data.get("description"),
                "subnet": object_data.get("subnet"),
            },
        )
    elif event_type == "TECHNOLOGY":
        technology = object_data.get("technology")
        result.update(
            {
                "technology": str(technology).lower() if technology else None,
                "name": str(technology).lower() if technology else None,
                "url": _extract_url(object_data),
            },
        )
    elif event_type == "EMAIL_ADDRESS":
        result["email"] = str(data)
    elif event_type == "ORG_STUB":
        result["organization"] = str(data).lower()
    elif event_type == "SOCIAL":
        result.update(
            {
                "platform": object_data.get("platform"),
                "profile_name": object_data.get("profile_name"),
            },
        )
    elif event_type == "STORAGE_BUCKET":
        result.update(
            {
                "bucket_provider": _bucket_provider(event, object_data),
                "bucket_name": str(object_data["name"]).strip().lower(),
                "name": str(object_data["name"]).strip().lower(),
            },
        )
    elif event_type == "FINDING":
        result.update(
            {
                "finding_name": object_data.get("name")
                or object_data.get("description"),
                "name": object_data.get("name") or object_data.get("description"),
                "severity": object_data.get("severity"),
                "confidence": object_data.get("confidence"),
                "description": object_data.get("description"),
                "cves": [str(cve) for cve in object_data.get("cves", [])],
            },
        )
    return result


def _merge_occurrence(existing: dict[str, Any], incoming: dict[str, Any]) -> None:
    for field in _LIST_FIELDS:
        existing[field] = sorted(
            set(existing.get(field, [])) | set(incoming.get(field, []))
        )
    existing["occurrence_count"] += incoming["occurrence_count"]
    for field in ("scope_distance", "web_spider_distance"):
        values = [
            value
            for value in (existing.get(field), incoming.get(field))
            if value is not None
        ]
        existing[field] = min(values) if values else None
    incoming_is_latest = _observation_order(
        incoming.get("observed_at"),
    ) >= _observation_order(existing.get("observed_at"))
    if incoming_is_latest:
        excluded = {
            *_LIST_FIELDS,
            "occurrence_count",
            "scope_distance",
            "web_spider_distance",
        }
        for key, value in incoming.items():
            if key not in excluded and value is not None:
                existing[key] = value


def _nearest_parent_ref(
    event: dict[str, Any],
    uuid_refs: dict[str, tuple[str, str]],
    bbot_id_refs: dict[str, tuple[str, str]],
) -> tuple[str, str] | None:
    candidates = [event.get("parent_uuid")]
    parent_chain = event.get("parent_chain", [])
    if isinstance(parent_chain, list):
        if parent_chain and parent_chain[-1] == event.get("uuid"):
            parent_chain = parent_chain[:-1]
        candidates.extend(reversed(parent_chain))
    for candidate in candidates:
        if isinstance(candidate, str) and candidate in uuid_refs:
            return uuid_refs[candidate]
    parent_id = event.get("parent")
    return bbot_id_refs.get(parent_id) if isinstance(parent_id, str) else None


def _add_relationship(
    relationships: dict[tuple[str, str, str], set[tuple[str, str]]],
    source: tuple[str, str] | None,
    rel_label: str,
    target: tuple[str, str] | None,
) -> None:
    if not source or not target or source == target:
        return
    relationships[(source[0], target[0], rel_label)].add((source[1], target[1]))


def transform(
    events: list[dict[str, Any]],
    source_uri: str,
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[tuple[str, str, str], list[dict[str, str]]],
]:
    prepared: list[tuple[dict[str, Any], str | dict[str, Any], tuple[str, str]]] = []
    uuid_refs: dict[str, tuple[str, str]] = {}
    bbot_id_refs: dict[str, tuple[str, str]] = {}
    unknown_types: set[str] = set()

    for event in events:
        event_type = event.get("type")
        if event_type not in BBOT_SCHEMAS:
            unknown_types.add(str(event_type))
            continue
        data = _event_data(event)
        ref = (BBOT_SCHEMAS[event_type].label, _stable_identity(event, data))
        prepared.append((event, data, ref))
        if isinstance(event.get("uuid"), str):
            uuid_refs[event["uuid"]] = ref
        bbot_id_refs[event["id"]] = ref

    if unknown_types:
        logger.warning(
            "Skipping unsupported BBOT event types: %s",
            ", ".join(sorted(unknown_types)),
        )

    nodes: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    host_refs: dict[str, tuple[str, str]] = {}
    port_refs: dict[tuple[str, int], tuple[str, str]] = {}
    url_refs: dict[str, tuple[str, str]] = {}
    scan_ref: tuple[str, str] | None = None

    for event, data, ref in prepared:
        properties = _event_properties(event, data, ref[1], source_uri)
        existing = nodes[ref[0]].get(ref[1])
        if existing:
            _merge_occurrence(existing, properties)
        else:
            nodes[ref[0]][ref[1]] = properties

        if event["type"] == "SCAN":
            scan_ref = ref
        if event["type"] in {"DNS_NAME", "IP_ADDRESS"}:
            value = properties.get("name") or properties.get("ip_address")
            if isinstance(value, str):
                host_refs[value] = ref
        if (
            event["type"] == "OPEN_TCP_PORT"
            and properties.get("host")
            and properties.get("port")
        ):
            port_refs[(properties["host"], properties["port"])] = ref
        if event["type"] == "URL" and properties.get("url"):
            url_refs[properties["url"]] = ref

    relationships: dict[tuple[str, str, str], set[tuple[str, str]]] = defaultdict(set)
    for event, data, ref in prepared:
        event_type = event["type"]
        parent_ref = _nearest_parent_ref(event, uuid_refs, bbot_id_refs)
        _add_relationship(relationships, ref, "DISCOVERED_FROM", parent_ref)
        if event_type != "SCAN":
            _add_relationship(relationships, ref, "OBSERVED_IN", scan_ref)

        properties = nodes[ref[0]][ref[1]]
        host_value = properties.get("host")
        host_ref = host_refs.get(host_value) if isinstance(host_value, str) else None
        port_ref = None
        port_value = properties.get("port")
        if isinstance(host_value, str) and isinstance(port_value, int):
            port_ref = port_refs.get((host_value, port_value))

        if event_type == "DNS_NAME":
            for resolved_host in event.get("resolved_hosts", []):
                if isinstance(resolved_host, str):
                    _add_relationship(
                        relationships,
                        ref,
                        "RESOLVES_TO",
                        host_refs.get(_normalize_host(resolved_host)),
                    )
        elif event_type == "OPEN_TCP_PORT":
            _add_relationship(relationships, host_ref, "HAS_OPEN_PORT", ref)
        elif event_type == "URL":
            _add_relationship(relationships, ref, "HOSTED_BY", port_ref or host_ref)
        elif event_type == "TECHNOLOGY":
            technology_url = properties.get("url")
            target = (
                url_refs.get(technology_url)
                if isinstance(technology_url, str)
                else None
            )
            target = target or port_ref or host_ref
            _add_relationship(relationships, ref, "DETECTED_ON", target)
        elif event_type == "FINDING":
            finding_url = properties.get("url")
            target = (
                parent_ref
                if parent_ref and parent_ref[0] in _FINDING_TARGET_LABELS
                else None
            )
            target = target or (
                url_refs.get(finding_url) if isinstance(finding_url, str) else None
            )
            target = target or host_ref
            _add_relationship(relationships, ref, "AFFECTS", target)
        elif event_type == "ASN" and parent_ref and parent_ref[0] == "BbotIPAddress":
            _add_relationship(relationships, parent_ref, "ANNOUNCED_BY", ref)

    return (
        {label: list(records.values()) for label, records in nodes.items()},
        {
            key: [
                {"source_id": source_id, "target_id": target_id}
                for source_id, target_id in sorted(records)
            ]
            for key, records in relationships.items()
        },
    )


def _parse_finished_at(value: Any) -> datetime.datetime:
    if isinstance(value, (int, float)):
        return datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc)
    if isinstance(value, str):
        parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=parsed.tzinfo or datetime.timezone.utc)
    raise ValueError("BBOT completed scan is missing a valid finished_at")


def _observation_order(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            try:
                return datetime.datetime.fromisoformat(
                    value.replace("Z", "+00:00"),
                ).timestamp()
            except ValueError:
                return float("-inf")
    return float("-inf")


def parse_completed_scan_runs(
    text: str,
    source_uri: str,
) -> list[tuple[datetime.datetime, list[dict[str, Any]], str]]:
    runs: list[tuple[datetime.datetime, list[dict[str, Any]], str]] = []
    current: list[dict[str, Any]] | None = None
    current_scan_id: str | None = None

    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid BBOT JSON at {source_uri}:{line_number}"
            ) from exc
        if not isinstance(event, dict):
            raise ValueError(
                f"BBOT event at {source_uri}:{line_number} is not an object"
            )
        event_type = event.get("type")
        data = _event_data(event)
        status = (
            data.get("status")
            if event_type == "SCAN" and isinstance(data, dict)
            else None
        )

        if event_type == "SCAN" and status == "RUNNING":
            current = [event]
            current_scan_id = event.get("id")
            continue
        if current is None:
            continue
        current.append(event)
        if event_type == "SCAN" and status == "FINISHED" and isinstance(data, dict):
            if current_scan_id and event.get("id") != current_scan_id:
                raise ValueError(
                    f"BBOT scan ID changed before completion in {source_uri}"
                )
            runs.append(
                (_parse_finished_at(data.get("finished_at")), current, source_uri)
            )
            current = None
            current_scan_id = None
    return runs


@timeit
def sync(
    neo4j_session: neo4j.Session,
    events: list[dict[str, Any]],
    source_uri: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    nodes, relationships = transform(events, source_uri)

    for schema in BBOT_SCHEMAS.values():
        load(
            neo4j_session,
            schema,
            nodes.get(schema.label, []),
            lastupdated=update_tag,
        )

    for (source_label, target_label, rel_label), records in sorted(
        relationships.items()
    ):
        load_matchlinks(
            neo4j_session,
            BbotMatchLink(
                source_label,
                target_label,
                rel_label,
            ),
            records,
            lastupdated=update_tag,
            _sub_resource_label="BbotSource",
            _sub_resource_id=source_uri,
        )

    # MatchLinks span concrete label pairs, so one module-scoped cleanup handles
    # combinations that disappeared entirely from the new report.
    run_write_query(
        neo4j_session,
        """
        MATCH ()-[r]->()
        WHERE r._module_name = 'cartography:bbot'
          AND r.lastupdated <> $UPDATE_TAG
        DELETE r
        """,
        UPDATE_TAG=update_tag,
    )
    for schema in BBOT_SCHEMAS.values():
        GraphJob.from_node_schema(
            BbotCleanupSchema(schema.label),
            common_job_parameters,
        ).run(neo4j_session)


@timeit
def sync_bbot_from_report_reader(
    neo4j_session: neo4j.Session,
    reader: ReportReader,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    refs = filter_report_refs(
        reader.list_reports(),
        predicate=lambda ref: ref.name.endswith((".json", ".jsonl")),
    )
    if not refs:
        raise ValueError(f"No BBOT JSON reports found in {reader.source_uri}")

    runs: list[tuple[datetime.datetime, list[dict[str, Any]], str]] = []
    for ref in sorted(refs, key=lambda item: item.name):
        runs.extend(parse_completed_scan_runs(read_text_report(reader, ref), ref.uri))
    if not runs:
        raise ValueError(f"No completed BBOT scans found in {reader.source_uri}")

    finished_at, events, source_uri = max(runs, key=lambda run: run[0])
    logger.info("Ingesting BBOT scan completed at %s from %s", finished_at, source_uri)
    sync(neo4j_session, events, source_uri, update_tag, common_job_parameters)


@timeit
def start_bbot_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.bbot_source:
        logger.info("BBOT configuration not provided. Skipping BBOT ingestion.")
        return

    source = parse_report_source(config.bbot_source)
    common_job_parameters = {"UPDATE_TAG": config.update_tag}
    with build_report_reader_for_source(source, config=config) as reader:
        sync_bbot_from_report_reader(
            neo4j_session,
            reader,
            config.update_tag,
            common_job_parameters,
        )
