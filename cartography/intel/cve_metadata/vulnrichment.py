"""
CISA Vulnrichment: SSVC decisions that CISA adds to CVE records as an ADP container.

Vulnrichment is published only as a git repository of CVE JSON 5 records, one file
per CVE (about 200,000 files, 1.2 GB uncompressed). Rather than one request per CVE,
the sync streams the repository's gzipped tarball once (about 100 MB), reads it as a
non-seekable tar stream, and parses only the files of CVEs already in the graph.
Nothing is written to disk. GitHub's tarballs carry the commit in a pax global
header, which is recorded on the feed node as vulnrichment_commit.
"""

import gzip
import json
import logging
import posixpath
import tarfile
import zlib
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import cast
from typing import IO

from requests import Session
from requests.exceptions import RequestException
from urllib3.exceptions import HTTPError as Urllib3HTTPError

from cartography.intel.cve_metadata.util import parse_utc_datetime
from cartography.util import timeit

logger = logging.getLogger(__name__)

VULNRICHMENT_ARCHIVE_URL = (
    "https://codeload.github.com/cisagov/vulnrichment/tar.gz/refs/heads/develop"
)
CONNECT_AND_READ_TIMEOUT = (30, 120)
CISA_ADP_SHORT_NAME = "CISA-ADP"
_DRAIN_CHUNK_SIZE = 1024 * 1024

# Errors that mean the archive could not be downloaded or read in full. urllib3's
# errors surface directly because the body is read from the raw response stream.
FETCH_ERRORS = (
    RequestException,
    Urllib3HTTPError,
    tarfile.TarError,
    EOFError,
    gzip.BadGzipFile,
    zlib.error,
)

_SSVC_OPTION_KEYS = {
    "Exploitation": "ssvc_exploitation",
    "Automatable": "ssvc_automatable",
    "Technical Impact": "ssvc_technical_impact",
}
_EMPTY_RECORD: dict[str, Any] = {
    "ssvc_exploitation": None,
    "ssvc_automatable": None,
    "ssvc_technical_impact": None,
    "ssvc_version": None,
    "ssvc_timestamp": None,
    "vulnrichment_updated_at": None,
}


@dataclass(frozen=True)
class VulnrichmentSnapshot:
    commit: str | None
    records: dict[str, dict[str, Any]] = field(default_factory=dict)


def _find_ssvc(container: dict[str, Any]) -> dict[str, Any] | None:
    for metric in container.get("metrics", []):
        other = metric.get("other") or {}
        if other.get("type") == "ssvc":
            return other.get("content") or {}
    return None


def transform_vulnrichment_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Only CISA's ADP container is read. A few records also carry an SSVC decision in
    the CNA container; when this was written, all of them also had a CISA decision.
    """
    transformed = dict(_EMPTY_RECORD)
    transformed["vulnrichment_updated_at"] = parse_utc_datetime(
        record.get("cveMetadata", {}).get("dateUpdated"),
    )
    for adp in record.get("containers", {}).get("adp", []):
        if adp.get("providerMetadata", {}).get("shortName") != CISA_ADP_SHORT_NAME:
            continue
        ssvc = _find_ssvc(adp)
        if ssvc is None:
            continue
        for option in ssvc.get("options", []):
            for key, value in option.items():
                if key in _SSVC_OPTION_KEYS:
                    transformed[_SSVC_OPTION_KEYS[key]] = value
        transformed["ssvc_version"] = ssvc.get("version")
        transformed["ssvc_timestamp"] = parse_utc_datetime(ssvc.get("timestamp"))
        break
    return transformed


def _cve_id_from_member(member: tarfile.TarInfo) -> str | None:
    if not member.isfile():
        return None
    name = posixpath.basename(member.name)
    if not (name.startswith("CVE-") and name.endswith(".json")):
        return None
    return name.removesuffix(".json")


def read_vulnrichment_archive(
    fileobj: IO[bytes],
    cve_ids: set[str],
) -> VulnrichmentSnapshot:
    records: dict[str, dict[str, Any]] = {}
    scanned = 0
    malformed = 0
    # gzip.GzipFile rather than tarfile's "r|gz": it checks the stream's length and
    # CRC, so a truncated download raises instead of reading as a shorter archive.
    with gzip.GzipFile(fileobj=fileobj, mode="rb") as decompressed:
        with tarfile.open(
            fileobj=cast(IO[bytes], decompressed),
            mode="r|",
        ) as archive:
            while (member := archive.next()) is not None:
                # Stream mode remembers every member it has read. Forgetting them
                # keeps memory flat; the full list would take about 150 MB.
                archive.members = []  # type: ignore[attr-defined]
                cve_id = _cve_id_from_member(member)
                if cve_id is None:
                    continue
                scanned += 1
                if cve_id not in cve_ids:
                    continue
                extracted = archive.extractfile(member)
                if extracted is None:
                    continue
                try:
                    records[cve_id] = transform_vulnrichment_record(
                        json.load(extracted),
                    )
                except (ValueError, TypeError, AttributeError):
                    malformed += 1
                    logger.debug(
                        "Skipping malformed Vulnrichment record %s",
                        member.name,
                    )
            commit = (archive.pax_headers or {}).get("comment")
        # tarfile stops at the end-of-archive marker; the gzip checks run at EOF.
        while decompressed.read(_DRAIN_CHUNK_SIZE):
            pass
    if not scanned:
        # A complete archive without CVE records (a repository layout change, for
        # example) must fail like a bad download rather than unset every SSVC field.
        raise tarfile.ReadError("The Vulnrichment archive has no CVE records.")
    if malformed:
        logger.warning("Skipped %d malformed Vulnrichment records.", malformed)
    logger.info(
        "Read %d of %d Vulnrichment records, for CVEs in the graph, at commit %s.",
        len(records),
        scanned,
        commit,
    )
    return VulnrichmentSnapshot(commit=commit, records=records)


@timeit
def get_vulnrichment_records(
    http_session: Session,
    cve_ids: set[str],
) -> VulnrichmentSnapshot:
    logger.info("Streaming the Vulnrichment archive from %s", VULNRICHMENT_ARCHIVE_URL)
    with http_session.get(
        VULNRICHMENT_ARCHIVE_URL,
        stream=True,
        timeout=CONNECT_AND_READ_TIMEOUT,
    ) as response:
        response.raise_for_status()
        # Undo any transport encoding a proxy adds; the body itself is the .tar.gz.
        response.raw.decode_content = True
        return read_vulnrichment_archive(cast(IO[bytes], response.raw), cve_ids)


def merge_vulnrichment_into_cves(
    cves: list[dict[str, Any]],
    snapshot: VulnrichmentSnapshot | None,
) -> None:
    records = snapshot.records if snapshot else {}
    for cve in cves:
        cve.update(records.get(cve["id"], _EMPTY_RECORD))
