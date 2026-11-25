"""Group Sweet runtime vulnerability detections into finding sets that workloads share."""

import hashlib
import json
import re
from array import array
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

from dateutil.parser import isoparse

_ID_LENGTH = 32
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_BARE_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:_ID_LENGTH]


def normalize_status(status: str | None) -> str | None:
    """Turn Sweet's title-case status, such as `In Progress`, into `in_progress`."""
    if not status:
        return None
    return "_".join(status.strip().lower().split()) or None


def vulnerability_ids(raw_id: str | None) -> tuple[str | None, str | None]:
    """Return the vulnerability ID, with CVE IDs uppercased, and the CVE ID if it is one."""
    if raw_id and raw_id.upper().startswith("CVE-"):
        return raw_id.upper(), raw_id.upper()
    return raw_id, None


def sweet_vulnerability_id(tenant_id: str, vulnerability_id: str) -> str:
    return f"{tenant_id}:{vulnerability_id}"


def image_digest_for_match(digest: str | None) -> str | None:
    """Return the digest in the `sha256:<hex>` form that `Image._ont_digest` uses."""
    if not digest:
        return None
    normalized = digest.strip().lower()
    if normalized.startswith("sha256:"):
        return normalized
    if _BARE_SHA256.match(normalized):
        return f"sha256:{normalized}"
    return None


def transform_content(vulnerability: dict[str, Any], tenant_id: str) -> dict[str, Any]:
    """Return the parts of a Sweet detection that do not depend on its workload.

    Workloads running the same image report the same package, score, status and
    labels. Detection times, EPSS and the workload's cloud account vary per workload,
    so they stay out of the content.
    """
    vulnerability_id, cve_id = vulnerability_ids(vulnerability.get("cve"))
    package = vulnerability.get("package") or {}
    image = vulnerability.get("image") or {}
    code_owner = vulnerability.get("codeOwner") or {}
    content = {
        "vulnerability_id": vulnerability_id,
        "cve_id": cve_id,
        "status": normalize_status(vulnerability.get("status")),
        "sweet_score": vulnerability.get("sweetScore"),
        "sweet_severity": vulnerability.get("sweetSeverity"),
        "risk_indicators": sorted(vulnerability.get("riskIndicators") or []),
        "attack_labels": sorted(vulnerability.get("attackLabels") or []),
        "has_fix": vulnerability.get("hasFix"),
        "fixed_in_versions": vulnerability.get("fixedInVersions") or [],
        "package_name": package.get("name"),
        "package_version": package.get("version"),
        "package_manager": package.get("manager"),
        "image_name": image.get("name"),
        "image_tag": image.get("tag"),
        "image_digest": image.get("digest"),
        "image_registry": image.get("registry"),
        "code_owner_name": code_owner.get("name"),
        "code_owner_email": code_owner.get("email"),
    }
    # The tenant is part of the ID so that one tenant's cleanup never removes a node
    # that another tenant still reports.
    content["id"] = _hash(json.dumps([tenant_id, content], sort_keys=True))
    content["affected_image_digest"] = image_digest_for_match(image.get("digest"))
    content["sweet_vulnerability_id"] = (
        sweet_vulnerability_id(tenant_id, vulnerability_id)
        if vulnerability_id
        else None
    )
    return content


def _epoch_ms(value: str | None) -> int:
    if not value:
        return 0
    timestamp = isoparse(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return (timestamp - _EPOCH) // timedelta(milliseconds=1)


@dataclass
class _WorkloadDetections:
    workload: str
    cloud_account: str | None
    # Parallel columns keep a large tenant's detections compact until every page has loaded.
    content_indexes: array = field(default_factory=lambda: array("I"))
    finding_ids: list[str] = field(default_factory=list)
    first_detected_ms: array = field(default_factory=lambda: array("q"))
    last_detected_ms: array = field(default_factory=lambda: array("q"))
    last_loaded_ms: array = field(default_factory=lambda: array("q"))
    last_executed_ms: array = field(default_factory=lambda: array("q"))


@dataclass
class WorkloadFindingSets:
    """Collects a tenant's detections until every page has loaded.

    A workload's set is known only after all of its detections arrive, and Sweet
    returns them spread across pages ordered by score.
    """

    tenant_id: str
    _content_ids: list[str] = field(default_factory=list)
    _content_indexes: dict[str, int] = field(default_factory=dict)
    _workloads: dict[str, _WorkloadDetections] = field(default_factory=dict)

    def add(self, vulnerability: dict[str, Any], content_id: str) -> None:
        workload = vulnerability.get("workload") or ""
        cloud_account = vulnerability.get("cloudAccount") or ""
        workload_id = f"{self.tenant_id}:{cloud_account}:{workload}"
        detections = self._workloads.get(workload_id)
        if detections is None:
            detections = _WorkloadDetections(
                workload=workload,
                cloud_account=cloud_account or None,
            )
            self._workloads[workload_id] = detections
        index = self._content_indexes.get(content_id)
        if index is None:
            index = len(self._content_ids)
            self._content_ids.append(content_id)
            self._content_indexes[content_id] = index
        detections.content_indexes.append(index)
        detections.finding_ids.append(vulnerability["id"])
        detections.first_detected_ms.append(
            _epoch_ms(vulnerability.get("firstDetected"))
        )
        detections.last_detected_ms.append(_epoch_ms(vulnerability.get("lastDetected")))
        detections.last_loaded_ms.append(_epoch_ms(vulnerability.get("lastLoaded")))
        detections.last_executed_ms.append(_epoch_ms(vulnerability.get("lastExecuted")))

    def build(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Return the tenant's finding sets, their content slots and workload findings.

        A set lists its contents in a fixed order, repeating a content once per
        detection that reports it, and every workload on the set lists its detections
        in that order. Position k of a workload's columns is the detection in slot k of
        its set.
        """
        sets: dict[str, list[str]] = {}
        workloads: list[dict[str, Any]] = []
        for workload_id, detections in self._workloads.items():
            # Scores change while Sweet pages, so a detection can arrive twice; keep its
            # latest version.
            positions: dict[str, int] = {}
            for position, finding_id in enumerate(detections.finding_ids):
                known = positions.get(finding_id)
                if (
                    known is None
                    or detections.last_detected_ms[position]
                    >= detections.last_detected_ms[known]
                ):
                    positions[finding_id] = position
            occurrences = sorted(
                (
                    self._content_ids[detections.content_indexes[position]],
                    finding_id,
                    position,
                )
                for finding_id, position in positions.items()
            )
            content_ids = [content_id for content_id, _, _ in occurrences]
            set_id = _hash("\n".join(content_ids))
            sets[set_id] = content_ids
            workloads.append(
                {
                    "id": workload_id,
                    "workload": detections.workload,
                    "cloud_account": detections.cloud_account,
                    "finding_set_id": set_id,
                    "finding_ids": [finding_id for _, finding_id, _ in occurrences],
                    "first_detected_ms": [
                        detections.first_detected_ms[p] for _, _, p in occurrences
                    ],
                    "last_detected_ms": [
                        detections.last_detected_ms[p] for _, _, p in occurrences
                    ],
                    "last_loaded_ms": [
                        detections.last_loaded_ms[p] for _, _, p in occurrences
                    ],
                    "last_executed_ms": [
                        detections.last_executed_ms[p] for _, _, p in occurrences
                    ],
                },
            )
        slots: list[dict[str, Any]] = []
        for set_id, content_ids in sets.items():
            content_slots: dict[str, list[int]] = {}
            for slot, content_id in enumerate(content_ids):
                content_slots.setdefault(content_id, []).append(slot)
            slots.extend(
                {"setid": set_id, "contentid": content_id, "slots": slot_list}
                for content_id, slot_list in content_slots.items()
            )
        return (
            [{"id": set_id, "content_ids": ids} for set_id, ids in sets.items()],
            slots,
            workloads,
        )
