"""
The Debian security tracker's state of each CVE in each source package and release.

The tracker publishes everything it tracks as one JSON document, keyed by source
package, then vulnerability, then release (about 80 MB and 75,000 vulnerability
records). It is read as a stream, one vulnerability record at a time, and only the
records of CVEs already in the graph are kept, so memory does not grow with the
document. Loading it whole with json.load takes over 400 MB.
"""

import codecs
import json
import logging
import re
from collections.abc import Iterable
from collections.abc import Iterator
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from email.utils import parsedate_to_datetime
from typing import Any

import neo4j
from requests import Session

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.common.debian_releases import release_version
from cartography.intel.cve_metadata import get_cve_ids_from_graph
from cartography.models.debian.entry import DebianSecurityTrackerEntrySchema
from cartography.models.debian.feed import DebianSecurityTrackerFeedSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

# Module-level so that a deployment can point it at a mirror or caching proxy.
DEBIAN_SECURITY_TRACKER_URL = "https://security-tracker.debian.org/tracker/data/json"
FEED_ID = "debian-security-tracker"
CONNECT_AND_READ_TIMEOUT = (30, 120)
_CHUNK_SIZE = 1024 * 1024
# A vulnerability record is a few kilobytes, so a value that still does not decode
# with this much text buffered is malformed rather than incomplete.
_MAX_PENDING_CHARS = 16 * 1024 * 1024
_NON_WHITESPACE = re.compile(r"[^ \t\n\r]")
_DECODER = json.JSONDecoder()


@dataclass(frozen=True)
class TrackerSnapshot:
    last_modified: datetime | None
    fetched_at: datetime
    # (source package, CVE ID, raw record), for CVEs in the graph only.
    records: list[tuple[str, str, dict[str, Any]]] = field(default_factory=list)


class _JSONStream:
    """
    Walks nested JSON objects from a sequence of text chunks. Objects are entered
    member by member, and only the values the caller reads are decoded whole.
    """

    def __init__(self, chunks: Iterable[str]) -> None:
        self._chunks = iter(chunks)
        self._buffer = ""
        self._pos = 0

    def _read_more(self) -> bool:
        for chunk in self._chunks:
            if chunk:
                self._buffer = self._buffer[self._pos :] + chunk
                self._pos = 0
                return True
        return False

    def _peek(self) -> str | None:
        while True:
            match = _NON_WHITESPACE.search(self._buffer, self._pos)
            if match is not None:
                self._pos = match.start()
                return match.group()
            self._pos = len(self._buffer)
            if not self._read_more():
                return None

    def _expect(self, char: str) -> None:
        found = self._peek()
        if found != char:
            raise ValueError(
                f"Malformed Debian security tracker data: expected {char!r}, "
                f"found {found!r}.",
            )
        self._pos += 1

    def _accept(self, char: str) -> bool:
        if self._peek() == char:
            self._pos += 1
            return True
        return False

    def value(self) -> Any:
        if self._peek() is None:
            raise ValueError("The Debian security tracker data ended early.")
        while True:
            try:
                value, end = _DECODER.raw_decode(self._buffer, self._pos)
            except json.JSONDecodeError:
                if len(self._buffer) - self._pos > _MAX_PENDING_CHARS:
                    raise
                if not self._read_more():
                    raise
                continue
            # A number or literal that ends the buffer may continue in the next chunk.
            if end == len(self._buffer) and self._read_more():
                continue
            self._pos = end
            return value

    def members(self) -> Iterator[str]:
        """
        Yields the keys of the object at the cursor. The caller reads each key's
        value, or walks into it, before asking for the next key.
        """
        self._expect("{")
        if self._accept("}"):
            return
        while True:
            key = self.value()
            if not isinstance(key, str):
                raise ValueError(
                    "Malformed Debian security tracker data: an object key is not a "
                    "string.",
                )
            self._expect(":")
            yield key
            if self._accept(","):
                continue
            self._expect("}")
            return

    def end(self) -> None:
        found = self._peek()
        if found is not None:
            raise ValueError(
                f"Malformed Debian security tracker data: unexpected {found!r} after "
                "the document.",
            )


def _decode(chunks: Iterable[bytes]) -> Iterator[str]:
    decoder = codecs.getincrementaldecoder("utf-8")()
    for chunk in chunks:
        yield decoder.decode(chunk)
    yield decoder.decode(b"", final=True)


def read_tracker_records(
    chunks: Iterable[bytes],
    cve_ids: set[str],
) -> list[tuple[str, str, dict[str, Any]]]:
    stream = _JSONStream(_decode(chunks))
    records: list[tuple[str, str, dict[str, Any]]] = []
    scanned = 0
    for source_package in stream.members():
        for vuln_id in stream.members():
            record = stream.value()
            scanned += 1
            if vuln_id in cve_ids:
                records.append((source_package, vuln_id, record))
    stream.end()
    # Loading nothing would remove every entry of the previous sync.
    if not scanned:
        raise ValueError(
            "The Debian security tracker data has no vulnerability records.",
        )
    logger.info(
        "Read %d of %d Debian security tracker records, for CVEs in the graph.",
        len(records),
        scanned,
    )
    return records


def _parse_http_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        logger.warning(
            "Ignoring an unparseable Last-Modified header from the Debian security "
            "tracker: %r",
            value,
        )
        return None


@timeit
def get(http_session: Session, cve_ids: set[str]) -> TrackerSnapshot:
    logger.info(
        "Streaming the Debian security tracker from %s",
        DEBIAN_SECURITY_TRACKER_URL,
    )
    fetched_at = datetime.now(timezone.utc)
    with http_session.get(
        DEBIAN_SECURITY_TRACKER_URL,
        stream=True,
        timeout=CONNECT_AND_READ_TIMEOUT,
    ) as response:
        response.raise_for_status()
        records = read_tracker_records(
            response.iter_content(chunk_size=_CHUNK_SIZE),
            cve_ids,
        )
        last_modified = _parse_http_date(response.headers.get("Last-Modified"))
    return TrackerSnapshot(
        last_modified=last_modified,
        fetched_at=fetched_at,
        records=records,
    )


def transform(
    records: list[tuple[str, str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for source_package, cve_id, record in records:
        for release, state in record["releases"].items():
            fixed_version = state.get("fixed_version")
            entries.append(
                {
                    "id": f"{release}|{source_package}|{cve_id}",
                    "cve_id": cve_id,
                    "source_package": source_package,
                    "release": release,
                    "release_version": release_version(release),
                    "status": state["status"],
                    "urgency": state["urgency"],
                    "fixed_version": fixed_version,
                    # The tracker records a release that never shipped the
                    # vulnerable code as fixed in version 0.
                    "not_affected": fixed_version == "0",
                    "nodsa": state.get("nodsa"),
                    "nodsa_reason": state.get("nodsa_reason"),
                    "next_point_update": state.get("next_point_update") is True,
                    "debianbug": record.get("debianbug"),
                },
            )
    return entries


@timeit
def load_feed(
    neo4j_session: neo4j.Session,
    snapshot: TrackerSnapshot,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DebianSecurityTrackerFeedSchema(),
        [
            {
                "id": FEED_ID,
                "url": DEBIAN_SECURITY_TRACKER_URL,
                "last_modified": snapshot.last_modified,
                "fetched_at": snapshot.fetched_at,
            },
        ],
        lastupdated=update_tag,
    )


@timeit
def load_entries(
    neo4j_session: neo4j.Session,
    entries: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DebianSecurityTrackerEntrySchema(),
        entries,
        lastupdated=update_tag,
        FEED_ID=FEED_ID,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        DebianSecurityTrackerEntrySchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    http_session: Session,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    cve_ids = set(get_cve_ids_from_graph(neo4j_session))
    if cve_ids:
        snapshot = get(http_session, cve_ids)
        entries = transform(snapshot.records)
        load_feed(neo4j_session, snapshot, update_tag)
        load_entries(neo4j_session, entries, update_tag)
    else:
        logger.info(
            "No CVEs in the graph, so the Debian security tracker is not downloaded.",
        )
    cleanup(neo4j_session, common_job_parameters)
    merge_module_sync_metadata(
        neo4j_session,
        group_type="DebianSecurityTrackerFeed",
        group_id=FEED_ID,
        synced_type="DebianSecurityTrackerEntry",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
