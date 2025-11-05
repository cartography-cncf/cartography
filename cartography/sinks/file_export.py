import atexit
import gzip
import io
import json
import os
import threading
from dataclasses import asdict
from typing import Any, Dict, Iterable, List, Optional

# Minimal, opt-in export sink for append-only NDJSON.gz streams.


class _ThreadSafeGzipWriter:
    def __init__(self, path: str) -> None:
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        # Open gzip file in text mode
        self._fh: gzip.GzipFile = gzip.open(path, mode="wt", encoding="utf-8")  # type: ignore
        self._lock = threading.Lock()
        self._closed = False

    def write_line(self, line: str) -> None:
        with self._lock:
            if self._closed:
                return
            self._fh.write(line)
            if not line.endswith("\n"):
                self._fh.write("\n")

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            try:
                self._fh.close()
            finally:
                self._closed = True


class FileExportSink:
    """Append-only exporter for graph events.

    Records are serialized as NDJSON and compressed with gzip. Thread-safe.
    """

    def __init__(self, path: str, format: str = "ndjson") -> None:
        self._format = format.lower()
        if self._format != "ndjson":
            raise ValueError(f"Unsupported export format: {format}")
        self._writer = _ThreadSafeGzipWriter(path)

    def close(self) -> None:
        self._writer.close()

    def write_record(self, record: Dict[str, Any]) -> None:
        # Keep JSON output stable and minimal
        self._writer.write_line(json.dumps(record, separators=(",", ":"), sort_keys=False))

    # Convenience helpers
    def write_vertex(
        self,
        *,
        uid: Any,
        labels: List[str],
        props: Dict[str, Any],
        update_tag: Any,
        sub_resource_label: Optional[str] = None,
        sub_resource_id: Optional[Any] = None,
    ) -> None:
        rec: Dict[str, Any] = {
            "record_type": "vertex",
            "uid": uid,
            "labels": labels,
            "props": props,
            "update_tag": update_tag,
        }
        # Provide cleanup-scoping hints when available
        if sub_resource_label is not None:
            rec["_sub_resource_label"] = sub_resource_label
        if sub_resource_id is not None:
            rec["_sub_resource_id"] = sub_resource_id
        self.write_record(rec)

    def write_edge(
        self,
        *,
        from_uid: Optional[Any] = None,
        to_uid: Optional[Any] = None,
        rel_type: str,
        update_tag: Any,
        props: Optional[Dict[str, Any]] = None,
        # Fallback matching description if uid is unknown
        from_match: Optional[Dict[str, Any]] = None,
        to_match: Optional[Dict[str, Any]] = None,
        sub_resource_label: Optional[str] = None,
        sub_resource_id: Optional[Any] = None,
    ) -> None:
        rec: Dict[str, Any] = {
            "record_type": "edge",
            "rel_type": rel_type,
            "update_tag": update_tag,
            "props": props or {},
        }
        if from_uid is not None:
            rec["from_uid"] = from_uid
        if to_uid is not None:
            rec["to_uid"] = to_uid
        if from_match is not None:
            rec["from_match"] = from_match
        if to_match is not None:
            rec["to_match"] = to_match
        if sub_resource_label is not None:
            rec["_sub_resource_label"] = sub_resource_label
        if sub_resource_id is not None:
            rec["_sub_resource_id"] = sub_resource_id
        self.write_record(rec)


# Module-level lifecycle and flags
_sink: Optional[FileExportSink] = None
_no_neo4j_write: bool = False


def enable(path: str, *, format: str = "ndjson") -> None:
    global _sink
    if _sink is not None:
        return
    _sink = FileExportSink(path=path, format=format)
    atexit.register(disable)


def disable() -> None:
    global _sink
    if _sink is not None:
        try:
            _sink.close()
        finally:
            _sink = None


def get_sink() -> Optional[FileExportSink]:
    return _sink


def is_enabled() -> bool:
    return _sink is not None


def set_no_neo4j_write(flag: bool) -> None:
    global _no_neo4j_write
    _no_neo4j_write = bool(flag)


def get_no_neo4j_write() -> bool:
    return _no_neo4j_write

