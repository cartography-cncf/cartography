import io
import json
import tarfile
from typing import Any

VULNRICHMENT_COMMIT = "0123456789abcdef0123456789abcdef01234567"

_CVE_PROGRAM_ADP = {
    "title": "CVE Program Container",
    "providerMetadata": {
        "shortName": "CVE",
        "dateUpdated": "2024-08-01T16:27:56.695Z",
    },
    "references": [{"url": "https://example.com/advisory"}],
}


def _ssvc(cve_id: str, exploitation: str, automatable: str, impact: str, ts: str):
    return {
        "other": {
            "type": "ssvc",
            "content": {
                "id": cve_id,
                "role": "CISA Coordinator",
                "options": [
                    {"Exploitation": exploitation},
                    {"Automatable": automatable},
                    {"Technical Impact": impact},
                ],
                "version": "2.0.3",
                "timestamp": ts,
            },
        },
    }


def _record(
    cve_id: str,
    date_updated: str,
    cna: dict[str, Any],
    adp: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    containers: dict[str, Any] = {"cna": cna}
    if adp is not None:
        containers["adp"] = adp
    return {
        "dataType": "CVE_RECORD",
        "dataVersion": "5.1",
        "cveMetadata": {
            "cveId": cve_id,
            "state": "PUBLISHED",
            "dateUpdated": date_updated,
        },
        "containers": containers,
    }


# CISA's ADP container carries the SSVC decision, next to the CVE Program container.
def _cisa_adp_record(date_updated: str, ssvc_timestamp: str) -> dict[str, Any]:
    return _record(
        "CVE-2023-41782",
        date_updated,
        cna={"providerMetadata": {"shortName": "zte"}},
        adp=[
            _CVE_PROGRAM_ADP,
            {
                "title": "CISA ADP Vulnrichment",
                "providerMetadata": {
                    "shortName": "CISA-ADP",
                    "dateUpdated": "2024-08-01T19:31:28.822Z",
                },
                "metrics": [
                    _ssvc(
                        "CVE-2023-41782",
                        "active",
                        "yes",
                        "total",
                        ssvc_timestamp,
                    ),
                ],
            },
        ],
    )


CISA_ADP_RECORD = _cisa_adp_record(
    "2024-10-29T14:07:56.381Z",
    "2024-08-01T19:28:25.242481Z",
)

# Some records give their timestamps without a UTC offset.
CISA_ADP_RECORD_WITHOUT_OFFSETS = _cisa_adp_record(
    "2024-10-29T14:07:56.381",
    "2024-08-01T19:28:25.242481",
)

# A record with only the CNA container: Vulnrichment has it, but no SSVC decision.
CNA_ONLY_RECORD = _record(
    "CVE-2024-22075",
    "2024-05-28T18:59:27.726Z",
    cna={"providerMetadata": {"shortName": "mitre"}},
)

# CISA's ADP container adds a CVSS score but no SSVC decision.
ADP_WITHOUT_SSVC_RECORD = _record(
    "CVE-2024-0002",
    "2024-03-01T00:00:00.000Z",
    cna={"providerMetadata": {"shortName": "mitre"}},
    adp=[
        {
            "providerMetadata": {"shortName": "CISA-ADP"},
            "metrics": [{"cvssV3_1": {"baseScore": 7.5, "version": "3.1"}}],
        },
    ],
)

# Only the CNA publishes an SSVC decision, which is not read.
CNA_SSVC_RECORD = _record(
    "CVE-2024-0003",
    "2024-04-01T00:00:00.000Z",
    cna={
        "providerMetadata": {"shortName": "example-cna"},
        "metrics": [
            _ssvc("CVE-2024-0003", "poc", "no", "partial", "2024-03-30T00:00:00Z"),
        ],
    },
)

# Both containers publish a decision; CISA's is read.
CNA_AND_ADP_SSVC_RECORD = _record(
    "CVE-2024-0004",
    "2024-04-02T00:00:00.000Z",
    cna={
        "providerMetadata": {"shortName": "example-cna"},
        "metrics": [
            _ssvc("CVE-2024-0004", "none", "no", "partial", "2024-03-30T00:00:00Z"),
        ],
    },
    adp=[
        {
            "providerMetadata": {"shortName": "CISA-ADP"},
            "metrics": [
                _ssvc("CVE-2024-0004", "poc", "yes", "total", "2024-04-01T00:00:00Z"),
            ],
        },
    ],
)

# Archive paths follow the repository layout: <year>/<thousands>xxx/<cve>.json
ARCHIVE_RECORDS = {
    "2023/41xxx/CVE-2023-41782.json": CISA_ADP_RECORD,
    "2024/22xxx/CVE-2024-22075.json": CNA_ONLY_RECORD,
    "2024/0xxx/CVE-2024-0002.json": ADP_WITHOUT_SSVC_RECORD,
}


def build_vulnrichment_archive(
    records: dict[str, dict[str, Any]],
    commit: str | None = VULNRICHMENT_COMMIT,
    extra_files: dict[str, bytes] | None = None,
) -> bytes:
    """Build a gzipped tarball shaped like GitHub's archive of the repository."""
    buffer = io.BytesIO()
    pax_headers = {"comment": commit} if commit else {}
    with tarfile.open(
        fileobj=buffer,
        mode="w:gz",
        format=tarfile.PAX_FORMAT,
        pax_headers=pax_headers,
    ) as archive:
        root = tarfile.TarInfo("vulnrichment-develop")
        root.type = tarfile.DIRTYPE
        archive.addfile(root)
        files = {"README.md": b"# Vulnrichment\n", **(extra_files or {})}
        files.update(
            {path: json.dumps(record).encode() for path, record in records.items()},
        )
        for path, content in files.items():
            info = tarfile.TarInfo(f"vulnrichment-develop/{path}")
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    return buffer.getvalue()
