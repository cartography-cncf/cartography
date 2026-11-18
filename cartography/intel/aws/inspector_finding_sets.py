"""Group Inspector package vulnerability findings on EC2 instances into shared finding sets."""

import hashlib
import json
from array import array
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

from cartography.intel.trivy.util import canonical_cve_id

_ID_LENGTH = 32
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


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
        "cve_id": canonical_cve_id(details["vulnerabilityId"]),
        "vendorseverity": details.get("vendorSeverity"),
        "vulnerablepackageids": sorted(package_ids),
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


def split_finding_arn(finding: Dict[str, Any]) -> Tuple[str, str]:
    """Split a finding ARN into its prefix, which carries the partition, and its ID."""
    prefix, finding_id = finding["findingArn"].rsplit("/", 1)
    return f"{prefix}/", finding_id


# Times are held to the microsecond, so the latest of two deliveries of a finding
# is found even within one millisecond, and written in milliseconds.
def _epoch_us(value: datetime) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return (value - _EPOCH) // timedelta(microseconds=1)


def _ms(microseconds: int) -> int:
    return round(microseconds / 1000)


@dataclass
class _InstanceFindings:
    awsaccount: str
    imageid: str | None
    finding_arn_prefix: str
    # Parallel columns keep a large fleet's findings compact while a region syncs.
    content_indexes: array = field(default_factory=lambda: array("I"))
    finding_ids: bytearray = field(default_factory=bytearray)
    first_observed_us: array = field(default_factory=lambda: array("q"))
    last_observed_us: array = field(default_factory=lambda: array("q"))
    updated_us: array = field(default_factory=lambda: array("q"))


@dataclass
class InstanceFindingSets:
    """Collects one region's EC2 package findings until every batch has loaded.

    An instance's set is known only after all of its findings arrive, and Inspector
    returns them spread across finding ID shards and load batches.
    """

    _content_ids: List[str] = field(default_factory=list)
    _content_indexes: Dict[str, int] = field(default_factory=dict)
    _instances: Dict[str, _InstanceFindings] = field(default_factory=dict)

    def add(self, finding: Dict[str, Any], content_id: str) -> None:
        resource = finding["resources"][0]
        arn_prefix, raw_finding_id = split_finding_arn(finding)
        instance = self._instances.get(resource["id"])
        if instance is None:
            details = (resource.get("details") or {}).get("awsEc2Instance") or {}
            instance = _InstanceFindings(
                awsaccount=finding["awsAccountId"],
                imageid=details.get("imageId"),
                finding_arn_prefix=arn_prefix,
            )
            self._instances[resource["id"]] = instance
        index = self._content_indexes.get(content_id)
        if index is None:
            index = len(self._content_ids)
            self._content_ids.append(content_id)
            self._content_indexes[content_id] = index
        instance.content_indexes.append(index)
        instance.finding_ids.extend(bytes.fromhex(raw_finding_id))
        instance.first_observed_us.append(_epoch_us(finding["firstObservedAt"]))
        instance.last_observed_us.append(_epoch_us(finding["lastObservedAt"]))
        instance.updated_us.append(_epoch_us(finding["updatedAt"]))

    def discard_account(self, awsaccount: str) -> None:
        """Drop an account's instances after an incomplete read.

        A partial set would replace the instance's complete set from the last sync.
        """
        dropped = [i for i, f in self._instances.items() if f.awsaccount == awsaccount]
        for instance_id in dropped:
            del self._instances[instance_id]

    def build(
        self,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Return the region's finding sets, their content slots and instance findings, and start over.

        A set lists its contents in a fixed order, repeating a content once per finding
        that reports it, and every instance on the set lists its findings in that order.
        Position k of an instance's columns is the finding in slot k of its set.
        """
        sets: Dict[str, List[str]] = {}
        instances: List[Dict[str, Any]] = []
        for instance_id, instance in self._instances.items():
            # Inspector can return a finding twice while it pages; keep its latest version.
            positions: Dict[bytes, int] = {}
            for position in range(len(instance.content_indexes)):
                raw_id = bytes(
                    instance.finding_ids[position * 16 : (position + 1) * 16]
                )
                known = positions.get(raw_id)
                if (
                    known is None
                    or instance.updated_us[position] > instance.updated_us[known]
                ):
                    positions[raw_id] = position
            occurrences = sorted(
                (
                    self._content_ids[instance.content_indexes[position]],
                    raw_id,
                    position,
                )
                for raw_id, position in positions.items()
            )
            content_ids = [content_id for content_id, _, _ in occurrences]
            set_id = _hash("\n".join(content_ids))
            sets[set_id] = content_ids
            instances.append(
                {
                    "id": instance_id,
                    "instanceid": instance_id,
                    "awsaccount": instance.awsaccount,
                    "imageid": instance.imageid,
                    "finding_set_id": set_id,
                    "finding_arn_prefix": instance.finding_arn_prefix,
                    "finding_ids": [raw_id.hex() for _, raw_id, _ in occurrences],
                    "first_observed_at_ms": [
                        _ms(instance.first_observed_us[p]) for _, _, p in occurrences
                    ],
                    "last_observed_at_ms": [
                        _ms(instance.last_observed_us[p]) for _, _, p in occurrences
                    ],
                    "updated_at_ms": [
                        _ms(instance.updated_us[p]) for _, _, p in occurrences
                    ],
                },
            )
        self._content_ids.clear()
        self._content_indexes.clear()
        self._instances.clear()
        slots: List[Dict[str, Any]] = []
        for set_id, content_ids in sets.items():
            content_slots: Dict[str, List[int]] = {}
            for slot, content_id in enumerate(content_ids):
                content_slots.setdefault(content_id, []).append(slot)
            slots.extend(
                {"setid": set_id, "contentid": content_id, "slots": content_slot_list}
                for content_id, content_slot_list in content_slots.items()
            )
        return (
            [{"id": set_id, "content_ids": ids} for set_id, ids in sets.items()],
            slots,
            instances,
        )
