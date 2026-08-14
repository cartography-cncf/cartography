import hashlib
import json
import re
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.orca import api
from cartography.models.orca import OrcaVulnerabilitySchema
from cartography.util import timeit

PAGE_SIZE = 1000
_CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)


def build_query() -> dict[str, Any]:
    return {
        "query": {
            "models": ["VulnerabilityV2"],
            "type": "object_set",
            "with": {
                "operator": "and",
                "type": "operation",
                "values": [
                    {
                        "keys": ["Inventory"],
                        "models": ["Inventory"],
                        "type": "object",
                        "operator": "has",
                    },
                ],
            },
        },
        "additional_models[]": ["InstalledPackage", "Inventory"],
        "flat_json": True,
        "full_graph_fetch": {"enabled": True},
        "max_tier": 2,
    }


def _normalize_cve_ids(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    result = {
        str(candidate).strip().upper()
        for candidate in values
        if candidate is not None and _CVE_RE.fullmatch(str(candidate).strip())
    }
    if not result:
        raise ValueError("Orca VulnerabilityV2 row omitted a canonical CveId")
    return sorted(result)


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "yes", "1"}:
        return True
    if normalized in {"false", "no", "0"}:
        return False
    raise ValueError(f"Unexpected Orca boolean value {value!r}")


def _value(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key not in data:
            continue
        value = data[key]
        if isinstance(value, dict) and "value" in value:
            return value.get("value")
        return value
    return None


def _related_object(row: dict[str, Any], field: str) -> dict[str, Any]:
    value = row.get(field)
    if isinstance(value, dict) and "value" in value:
        value = value.get("value")
    if isinstance(value, list):
        if len(value) != 1 or not isinstance(value[0], dict):
            raise TypeError(f"Orca VulnerabilityV2.{field} must contain one object")
        value = value[0]
    if not isinstance(value, dict):
        raise TypeError(f"Orca VulnerabilityV2.{field} must be an object")
    return value


def _related_packages(row: dict[str, Any]) -> list[dict[str, Any]]:
    value = row.get("InstalledPackage")
    if isinstance(value, dict) and "value" in value:
        value = value.get("value")
    if value is None:
        return [{}]
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        return value or [{}]
    raise TypeError(
        "Orca VulnerabilityV2.InstalledPackage must be an object or object list",
    )


def _references(vulnerability: dict[str, Any]) -> list[str]:
    references = vulnerability.get("References") or []
    if isinstance(references, str):
        references = [references]
    if not isinstance(references, list):
        raise ValueError("Orca VulnerabilityV2.References must be a list or string")
    source_link = vulnerability.get("SourceLink")
    if source_link:
        references = [*references, source_link]
    return sorted(
        {str(reference).strip() for reference in references if str(reference).strip()},
    )


def _package_key(package: dict[str, Any]) -> str:
    package_id = _value(package, "id")
    if package_id:
        return str(package_id).strip()
    for key in ("PURL", "CPE"):
        value = _value(package, key)
        if value:
            return str(value).strip()
    name = _value(package, "Name")
    version = _value(package, "Version")
    if name or version:
        normalized_name = str(name or "").strip().casefold()
        normalized_version = str(version or "").strip()
        return f"{normalized_name}@{normalized_version}"
    return "asset-wide"


def _vulnerability_id(
    organization_id: str,
    asset_unique_id: str,
    cve_id: str,
    package_key: str,
) -> str:
    identity = json.dumps(
        [organization_id, asset_unique_id, cve_id, package_key],
        separators=(",", ":"),
    )
    digest = hashlib.sha256(identity.encode()).hexdigest()
    return f"orca:{organization_id}:vulnerability:{digest}"


def transform(
    raw_vulnerabilities: list[dict[str, Any]],
    organization_id: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for vulnerability in raw_vulnerabilities:
        inventory = _related_object(vulnerability, "Inventory")
        asset_unique_id = _value(inventory, "AssetUniqueId", "asset_unique_id")
        if not isinstance(asset_unique_id, str) or not asset_unique_id.strip():
            raise ValueError(
                "Orca VulnerabilityV2 Inventory.AssetUniqueId must be nonempty",
            )
        asset_unique_id = asset_unique_id.strip()
        inventory_id = _value(inventory, "id", "base_id_uuid")
        if inventory_id is not None:
            if not isinstance(inventory_id, str) or not inventory_id.strip():
                raise ValueError(
                    "Orca VulnerabilityV2 Inventory identifier must be nonempty",
                )
            inventory_id = inventory_id.strip()

        orca_id = vulnerability.get("id") or vulnerability.get("base_id_uuid")
        if orca_id is not None:
            if not isinstance(orca_id, str) or not orca_id.strip():
                raise ValueError("Orca VulnerabilityV2 identifier must be nonempty")
            orca_id = orca_id.strip()

        for package in _related_packages(vulnerability):
            package_key = _package_key(package)
            for cve_id in _normalize_cve_ids(vulnerability.get("CveId")):
                transformed.append(
                    {
                        "id": _vulnerability_id(
                            organization_id,
                            asset_unique_id,
                            cve_id,
                            package_key,
                        ),
                        "orca_id": orca_id,
                        "cve_id": cve_id,
                        "description": vulnerability.get("Description"),
                        "references": _references(vulnerability),
                        "cvss_source": vulnerability.get("CvssSource"),
                        "base_score": vulnerability.get("CvssScore"),
                        "base_severity": vulnerability.get("CvssSeverity"),
                        "vector_string": vulnerability.get("CvssVector"),
                        "epss_percentile": vulnerability.get("EpssPercentile"),
                        "epss_probability": vulnerability.get("EpssProbability"),
                        "has_exploit": _optional_bool(
                            vulnerability.get("HasExploit"),
                        ),
                        "cisa_kev": _optional_bool(vulnerability.get("CisaKev")),
                        "patch_available": _optional_bool(
                            vulnerability.get("PatchAvailable"),
                        ),
                        "trending": _optional_bool(vulnerability.get("Trending")),
                        "upstream_disposition": vulnerability.get(
                            "UpstreamDisposition",
                        ),
                        "first_seen": vulnerability.get("FirstSeen"),
                        "package_id": _value(package, "id"),
                        "package_base_id_uuid": _value(package, "base_id_uuid"),
                        "package_name": _value(package, "Name"),
                        "package_version": _value(package, "Version"),
                        "purl": _value(package, "PURL"),
                        "cpe": _value(package, "CPE"),
                        "source_package": _value(package, "SourcePackage"),
                        "inventory_id": inventory_id,
                        "asset_unique_id": asset_unique_id,
                    },
                )
    return transformed


def load_vulnerabilities(
    neo4j_session: neo4j.Session,
    vulnerabilities: list[dict[str, Any]],
    organization_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        OrcaVulnerabilitySchema(),
        vulnerabilities,
        lastupdated=update_tag,
        ORCA_ORGANIZATION_ID=organization_id,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    api_endpoint: str,
    organization_id: str,
    update_tag: int,
) -> None:
    seen_ids: set[str] = set()
    for page in api.iter_serving_layer_pages(
        session,
        api_endpoint,
        build_query(),
        page_size=PAGE_SIZE,
        result_name="vulnerabilities",
    ):
        vulnerabilities = transform(page, organization_id)
        page_ids = {vulnerability["id"] for vulnerability in vulnerabilities}
        if len(page_ids) != len(vulnerabilities) or page_ids & seen_ids:
            raise RuntimeError(
                "Orca vulnerabilities response contained duplicate identities",
            )
        seen_ids.update(page_ids)
        load_vulnerabilities(
            neo4j_session,
            vulnerabilities,
            organization_id,
            update_tag,
        )


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(OrcaVulnerabilitySchema(), common_job_parameters).run(
        neo4j_session,
    )
