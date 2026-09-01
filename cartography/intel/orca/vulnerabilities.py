import hashlib
import json
import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.orca import api
from cartography.intel.orca.response import canonical_cve_ids
from cartography.intel.orca.response import inventory_target_context
from cartography.intel.orca.response import optional_nonempty_string
from cartography.intel.orca.response import optional_number
from cartography.intel.orca.response import optional_string
from cartography.intel.orca.response import parse_datetime
from cartography.intel.orca.response import require_nonempty_string
from cartography.intel.orca.response import require_object
from cartography.models.orca import OrcaVulnerabilityFindingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

PAGE_SIZE = 1000
VULNERABILITY_MODEL = "VulnerabilityV2"


def build_query() -> dict[str, Any]:
    return {
        "query": {
            "models": [VULNERABILITY_MODEL],
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


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if normalized in {"true", "yes", "1"}:
        return True
    if normalized in {"false", "no", "0"}:
        return False
    raise ValueError("Unexpected Orca boolean value")


def _related_packages(row: dict[str, Any]) -> list[dict[str, Any]]:
    value = row.get("InstalledPackage")
    if value is None:
        return [{}]
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        return value or [{}]
    raise ValueError(
        "Orca vulnerability.InstalledPackage must be an object or object list",
    )


def _package_properties(package: dict[str, Any]) -> dict[str, str | None]:
    return {
        field: optional_nonempty_string(
            package.get(orca_field),
            f"Orca vulnerability.InstalledPackage.{orca_field}",
        )
        for field, orca_field in (
            ("package_id", "id"),
            ("package_base_id_uuid", "base_id_uuid"),
            ("package_name", "Name"),
            ("package_version", "Version"),
            ("purl", "PURL"),
            ("cpe", "CPE"),
            ("source_package", "SourcePackage"),
        )
    }


def _package_key(package: dict[str, str | None]) -> tuple[str, ...]:
    for field in ("package_id", "purl", "cpe"):
        value = package[field]
        if value is not None:
            return (field.removeprefix("package_"), value)
    name = package["package_name"]
    version = package["package_version"]
    if name or version:
        normalized_name = (name or "").casefold()
        normalized_version = version or ""
        return ("name-version", normalized_name, normalized_version)
    return ("asset-wide",)


def _vulnerability_id(
    organization_id: str,
    target_orca_asset_unique_id: str,
    cve_id: str,
    package_key: tuple[str, ...],
) -> str:
    identity = json.dumps(
        [organization_id, target_orca_asset_unique_id, cve_id, package_key],
        separators=(",", ":"),
    )
    digest = hashlib.sha256(identity.encode()).hexdigest()
    return f"orca:{organization_id}:vulnerability:{digest}"


def transform(
    raw_vulnerabilities: list[dict[str, Any]],
    organization_id: str,
) -> list[dict[str, Any]]:
    transformed: dict[str, dict[str, Any]] = {}
    duplicate_count = 0
    for vulnerability in raw_vulnerabilities:
        inventory = require_object(
            vulnerability.get("Inventory"),
            "Orca vulnerability.Inventory",
        )
        target_context = inventory_target_context(
            inventory,
            "Orca vulnerability.Inventory",
        )
        target_orca_asset_unique_id = require_nonempty_string(
            target_context["target_orca_asset_unique_id"],
            "Orca vulnerability Inventory.AssetUniqueId",
        )

        raw_orca_id = vulnerability.get("id")
        if raw_orca_id is None:
            raw_orca_id = vulnerability.get("base_id_uuid")
        orca_id = optional_nonempty_string(
            raw_orca_id,
            "Orca vulnerability identifier",
        )

        cve_ids = canonical_cve_ids(vulnerability.get("CveId"))
        if not cve_ids:
            raise ValueError("Orca vulnerability row omitted a canonical CveId")
        source_link = optional_nonempty_string(
            vulnerability.get("SourceLink"),
            "Orca vulnerability.SourceLink",
        )
        common_fields = {
            "orca_id": orca_id,
            "description": optional_string(
                vulnerability.get("Description"),
                "Orca vulnerability.Description",
            ),
            "references": [source_link] if source_link else [],
            "cvss_source": optional_string(
                vulnerability.get("CvssSource"),
                "Orca vulnerability.CvssSource",
            ),
            "base_score": optional_number(
                vulnerability.get("CvssScore"),
                "Orca vulnerability.CvssScore",
            ),
            "base_severity": optional_string(
                vulnerability.get("CvssSeverity"),
                "Orca vulnerability.CvssSeverity",
            ),
            "vector_string": optional_string(
                vulnerability.get("CvssVector"),
                "Orca vulnerability.CvssVector",
            ),
            "epss_percentile": optional_number(
                vulnerability.get("EpssPercentile"),
                "Orca vulnerability.EpssPercentile",
            ),
            "epss_probability": optional_number(
                vulnerability.get("EpssProbability"),
                "Orca vulnerability.EpssProbability",
            ),
            "has_exploit": _optional_bool(vulnerability.get("HasExploit")),
            "cisa_kev": _optional_bool(vulnerability.get("CisaKev")),
            "patch_available": _optional_bool(
                vulnerability.get("PatchAvailable"),
            ),
            "trending": _optional_bool(vulnerability.get("Trending")),
            "upstream_disposition": optional_string(
                vulnerability.get("UpstreamDisposition"),
                "Orca vulnerability.UpstreamDisposition",
            ),
            "first_seen": parse_datetime(
                vulnerability.get("FirstSeen"),
                "Orca vulnerability.FirstSeen",
            ),
            **target_context,
        }

        for package in _related_packages(vulnerability):
            package_properties = _package_properties(package)
            package_key = _package_key(package_properties)
            for cve_id in cve_ids:
                finding_id = _vulnerability_id(
                    organization_id,
                    target_orca_asset_unique_id,
                    cve_id,
                    package_key,
                )
                finding = {
                    "id": finding_id,
                    "cve_id": cve_id,
                    **common_fields,
                    **package_properties,
                }
                if finding_id in transformed:
                    duplicate_count += 1
                    continue
                transformed[finding_id] = finding
    if duplicate_count:
        logger.warning(
            "Skipped %d duplicate Orca vulnerability findings within a page.",
            duplicate_count,
        )
    return list(transformed.values())


def load_vulnerabilities(
    neo4j_session: neo4j.Session,
    vulnerabilities: list[dict[str, Any]],
    organization_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        OrcaVulnerabilityFindingSchema(),
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
        new_vulnerabilities = [
            vulnerability
            for vulnerability in vulnerabilities
            if vulnerability["id"] not in seen_ids
        ]
        duplicate_count = len(vulnerabilities) - len(new_vulnerabilities)
        if duplicate_count:
            logger.warning(
                "Skipped %d duplicate Orca vulnerability findings across pages.",
                duplicate_count,
            )
        seen_ids.update(vulnerability["id"] for vulnerability in new_vulnerabilities)
        if new_vulnerabilities:
            load_vulnerabilities(
                neo4j_session,
                new_vulnerabilities,
                organization_id,
                update_tag,
            )


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        OrcaVulnerabilityFindingSchema(),
        common_job_parameters,
    ).run(neo4j_session)
