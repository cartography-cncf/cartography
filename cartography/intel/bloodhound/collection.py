"""Locate and open the JSON files of a BloodHound collection.

A collection source is a local path or object-store prefix holding SharpHound
zip archives, loose JSON files, or both. Archives are streamed to a temporary
directory first because zip members cannot be read without seeking.
"""

import datetime
import logging
import os
import re
import tempfile
import zipfile
from collections.abc import Callable
from collections.abc import Iterator
from contextlib import contextmanager
from contextlib import ExitStack
from dataclasses import dataclass
from functools import partial
from typing import IO

from cartography.intel.common.object_store import download_report
from cartography.intel.common.object_store import LocalReportReader
from cartography.intel.common.object_store import ReportReader
from cartography.intel.common.object_store import ReportRef

logger = logging.getLogger(__name__)

# SharpHound prefixes every output file with the collection start time in the
# collector host's local time: 20261012143015_users.json, 20261012143015_BloodHound.zip.
_FILENAME_TIMESTAMP = re.compile(r"^(\d{14})_")


class BloodHoundImportError(Exception):
    """The collection is unreadable, incomplete or in an unsupported format.

    Raised before anything is written, so the previously imported graph is kept.
    """


@dataclass(frozen=True)
class CollectionFile:
    """One JSON file of a collection, which can be re-opened for each pass."""

    source_uri: str
    open: Callable[[], IO[bytes]]
    collected_at: str | None


def timestamp_from_filename(name: str) -> str | None:
    match = _FILENAME_TIMESTAMP.match(os.path.basename(name))
    if not match:
        return None
    try:
        parsed = datetime.datetime.strptime(match.group(1), "%Y%m%d%H%M%S")
    except ValueError:
        return None
    return parsed.isoformat()


def _timestamp_from_zip_info(info: zipfile.ZipInfo) -> str | None:
    try:
        return datetime.datetime(*info.date_time).isoformat()
    except ValueError:
        return None


def _local_path(
    reader: ReportReader,
    ref: ReportRef,
    tmp_dir: str,
    index: int,
) -> str:
    if isinstance(reader, LocalReportReader):
        return ref.uri
    suffix = os.path.splitext(ref.name)[1]
    path = os.path.join(tmp_dir, f"{index}{suffix}")
    logger.info("Downloading BloodHound collection file %s", ref.uri)
    with open(path, "wb") as fileobj:
        download_report(reader, ref, fileobj)
    return path


def _open_binary(path: str) -> IO[bytes]:
    return open(path, "rb")


@contextmanager
def open_collection(reader: ReportReader) -> Iterator[list[CollectionFile]]:
    """Yield every JSON file in the source, including JSON inside zip archives.

    The files stay readable until the context exits.
    """
    with ExitStack() as stack:
        tmp_dir = stack.enter_context(
            tempfile.TemporaryDirectory(prefix="cartography-bloodhound-"),
        )
        files: list[CollectionFile] = []
        for index, ref in enumerate(reader.list_reports()):
            lowered = ref.name.lower()
            if lowered.endswith(".zip"):
                path = _local_path(reader, ref, tmp_dir, index)
                try:
                    archive = stack.enter_context(zipfile.ZipFile(path))
                except (zipfile.BadZipFile, OSError) as exc:
                    raise BloodHoundImportError(
                        f"{ref.uri} is not a readable zip archive: {exc}",
                    ) from exc
                for info in archive.infolist():
                    if info.is_dir() or not info.filename.lower().endswith(".json"):
                        continue
                    files.append(
                        CollectionFile(
                            source_uri=f"{ref.uri}!{info.filename}",
                            open=partial(archive.open, info),
                            collected_at=timestamp_from_filename(info.filename)
                            or timestamp_from_filename(ref.name)
                            or _timestamp_from_zip_info(info),
                        ),
                    )
            elif lowered.endswith(".json"):
                path = _local_path(reader, ref, tmp_dir, index)
                files.append(
                    CollectionFile(
                        source_uri=ref.uri,
                        open=partial(_open_binary, path),
                        collected_at=timestamp_from_filename(ref.name),
                    ),
                )
            else:
                logger.debug("Skipping non-BloodHound file %s", ref.uri)
        yield files
