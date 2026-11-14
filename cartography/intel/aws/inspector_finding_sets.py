"""Group Inspector package vulnerability findings on EC2 instances into shared finding sets."""

import hashlib
import json
from array import array
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from typing import Any
from typing import Dict
from typing import List
from typing import Set
from typing import Tuple

# Inspector records an instance's findings over the minutes its scan takes, so findings
# first observed within this window of the instance's earliest one share its timestamp.
LATE_FINDING_THRESHOLD_SECONDS = 3600
_ID_LENGTH = 32


def is_ec2_package_finding(finding: Dict[str, Any]) -> bool:
    return (
        finding["type"] == "PACKAGE_VULNERABILITY"
        and finding["resources"][0]["type"] == "AWS_EC2_INSTANCE"
    )


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:_ID_LENGTH]


def transform_finding_content(
    finding: Dict[str, Any],
    package_ids: List[str],
) -> Dict[str, Any]:
    """Return the parts of an EC2 package finding that do not depend on its instance."""
    details = finding["packageVulnerabilityDetails"]
    adjusted = (finding.get("inspectorScoreDetails") or {}).get("adjustedCvss") or {}
    content = {
        "title": finding.get("title"),
        "type": finding["type"],
        "status": finding["status"],
        "severity": finding["severity"],
        "cvssscore": adjusted.get("score"),
        "cvssvector": adjusted.get("scoringVector"),
        "vulnerabilityid": details["vulnerabilityId"],
        "cve_id": details["vulnerabilityId"],
        "vendorseverity": details.get("vendorSeverity"),
        "vulnerablepackageids": package_ids,
        "fixavailable": finding.get("fixAvailable"),
        "exploitavailable": finding.get("exploitAvailable"),
        "lastknownexploitat": (finding.get("exploitabilityDetails") or {}).get(
            "lastKnownExploitAt",
        ),
        "epss_score_inspector": (finding.get("epss") or {}).get("score"),
    }
    # Package details (fix version, remediation, file path) are part of the finding too,
    # so two findings that differ only there must not share a content.
    packages = sorted(
        json.dumps(p, sort_keys=True, default=str)
        for p in details["vulnerablePackages"]
    )
    content["id"] = _hash(json.dumps([content, packages], sort_keys=True, default=str))
    return content


def finding_id(finding: Dict[str, Any]) -> str:
    return finding["findingArn"].rsplit("/", 1)[1]


def _epoch_seconds(value: datetime) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return int(value.timestamp())


def _from_epoch_seconds(value: int) -> datetime:
    return datetime.fromtimestamp(value, tz=timezone.utc)


@dataclass
class _InstanceFindings:
    awsaccount: str
    imageid: str | None
    # Parallel columns keep a large fleet's findings compact while a region syncs.
    content_indexes: array = field(default_factory=lambda: array("I"))
    finding_ids: bytearray = field(default_factory=bytearray)
    first_observed: array = field(default_factory=lambda: array("q"))
    last_observed: int = 0


@dataclass
class InstanceFindingSets:
    """Collects one region's EC2 package findings until every batch has loaded.

    An instance's set is known only after all of its findings arrive, and Inspector
    returns them spread across finding ID shards and load batches.
    """

    _content_ids: List[str] = field(default_factory=list)
    _content_indexes: Dict[str, int] = field(default_factory=dict)
    _instances: Dict[str, _InstanceFindings] = field(default_factory=dict)
    loaded_content_ids: Set[str] = field(default_factory=set)

    def add(self, finding: Dict[str, Any], content_id: str) -> None:
        resource = finding["resources"][0]
        instance = self._instances.get(resource["id"])
        if instance is None:
            details = (resource.get("details") or {}).get("awsEc2Instance") or {}
            instance = _InstanceFindings(
                awsaccount=finding["awsAccountId"],
                imageid=details.get("imageId"),
            )
            self._instances[resource["id"]] = instance
        index = self._content_indexes.get(content_id)
        if index is None:
            index = len(self._content_ids)
            self._content_ids.append(content_id)
            self._content_indexes[content_id] = index
        instance.content_indexes.append(index)
        instance.finding_ids.extend(bytes.fromhex(finding_id(finding)))
        instance.first_observed.append(_epoch_seconds(finding["firstObservedAt"]))
        instance.last_observed = max(
            instance.last_observed,
            _epoch_seconds(finding["updatedAt"]),
        )

    def build(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Return the region's finding sets and instance findings, and start over."""
        sets: Dict[str, List[str]] = {}
        instances: List[Dict[str, Any]] = []
        for instance_id, instance in self._instances.items():
            findings: Dict[str, Tuple[str, int]] = {}
            for position, index in enumerate(instance.content_indexes):
                content_id = self._content_ids[index]
                first_observed = instance.first_observed[position]
                known = findings.get(content_id)
                if known is None or first_observed < known[1]:
                    raw_id = instance.finding_ids[position * 16 : (position + 1) * 16]
                    findings[content_id] = (raw_id.hex(), first_observed)
            content_ids = sorted(findings)
            set_id = _hash("\n".join(content_ids))
            sets[set_id] = content_ids
            first_observed = min(observed for _, observed in findings.values())
            late = [
                (content_id, findings[content_id][1])
                for content_id in content_ids
                if findings[content_id][1] - first_observed
                > LATE_FINDING_THRESHOLD_SECONDS
            ]
            instances.append(
                {
                    "id": instance_id,
                    "instanceid": instance_id,
                    "awsaccount": instance.awsaccount,
                    "imageid": instance.imageid,
                    "finding_set_id": set_id,
                    "finding_ids": [findings[c][0] for c in content_ids],
                    "first_observed_at": _from_epoch_seconds(first_observed),
                    "late_content_ids": [content_id for content_id, _ in late],
                    "late_first_observed_at": [
                        _from_epoch_seconds(observed) for _, observed in late
                    ],
                    "last_observed_at": _from_epoch_seconds(instance.last_observed),
                },
            )
        self._content_ids.clear()
        self._content_indexes.clear()
        self._instances.clear()
        return (
            [{"id": set_id, "content_ids": ids} for set_id, ids in sets.items()],
            instances,
        )
