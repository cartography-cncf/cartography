import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Protocol

import boto3
from azure.storage import blob as azure_blob
from google.cloud import storage

import cartography.intel.gcp.clients as gcp_clients
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.common.report_source import build_azblob_source
from cartography.intel.common.report_source import build_gcs_source
from cartography.intel.common.report_source import build_s3_source


@dataclass(frozen=True)
class ReportRef:
    uri: str
    name: str


class ReportReader(Protocol):
    """Source-bound reader for report ingestion.

    source_uri is the configured source locator used for logging and provenance.
    ReportRef.uri identifies each listed report.
    """

    source_uri: str

    def list_reports(self) -> list[ReportRef]:
        pass

    def read_bytes(self, ref: ReportRef) -> bytes:
        pass


class ObjectStoreParseError(ValueError):
    def __init__(self, source: str, message: str) -> None:
        super().__init__(f"{message}: {source}")
        self.source = source


class LocalReportReader:
    def __init__(self, source_path: str) -> None:
        self.source_uri = source_path
        self._root = Path(source_path)

    def list_reports(self) -> list[ReportRef]:
        refs: list[ReportRef] = []
        for path in self._root.rglob("*"):
            if not path.is_file() or path.name.startswith("."):
                continue
            refs.append(
                ReportRef(
                    uri=str(path),
                    name=str(path.relative_to(self._root)),
                ),
            )
        return refs

    def read_bytes(self, ref: ReportRef) -> bytes:
        try:
            with open(ref.uri, "rb") as file_pointer:
                return file_pointer.read()
        except OSError as exc:
            raise ObjectStoreParseError(ref.uri, "Failed to read local report") from exc


class ListedReportReader:
    def __init__(
        self,
        source_uri: str,
        refs: Iterable[ReportRef],
        read_bytes: Callable[[ReportRef], bytes],
    ) -> None:
        self.source_uri = source_uri
        self._refs = list(refs)
        self._read_bytes = read_bytes

    def list_reports(self) -> list[ReportRef]:
        return self._refs

    def read_bytes(self, ref: ReportRef) -> bytes:
        return self._read_bytes(ref)


class S3BucketReader:
    def __init__(
        self,
        boto3_session: boto3.Session,
        bucket: str,
        prefix: str = "",
        source_uri: str | None = None,
    ) -> None:
        self.source_uri = source_uri or build_s3_source(bucket, prefix)
        self._bucket = bucket
        self._prefix = prefix
        self._client = create_boto3_client(boto3_session, "s3")

    def list_reports(self) -> list[ReportRef]:
        paginator = self._client.get_paginator("list_objects_v2")
        refs: list[ReportRef] = []
        for page in paginator.paginate(Bucket=self._bucket, Prefix=self._prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith("/"):
                    continue
                refs.append(
                    ReportRef(
                        uri=f"s3://{self._bucket}/{key}",
                        name=key,
                    ),
                )
        return refs

    def read_bytes(self, ref: ReportRef) -> bytes:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=ref.name)
            return response["Body"].read()
        except Exception as exc:
            raise ObjectStoreParseError(ref.uri, "Failed to read S3 report") from exc


class GCSBucketReader:
    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        source_uri: str | None = None,
    ) -> None:
        self.source_uri = source_uri or build_gcs_source(bucket, prefix)
        self._bucket = bucket
        self._prefix = prefix
        credentials = gcp_clients.get_gcp_credentials()
        self._client = storage.Client(credentials=credentials)

    def list_reports(self) -> list[ReportRef]:
        refs: list[ReportRef] = []
        for blob in self._client.list_blobs(self._bucket, prefix=self._prefix):
            if blob.name.endswith("/"):
                continue
            refs.append(
                ReportRef(
                    uri=f"gs://{self._bucket}/{blob.name}",
                    name=blob.name,
                ),
            )
        return refs

    def read_bytes(self, ref: ReportRef) -> bytes:
        try:
            bucket = self._client.bucket(self._bucket)
            blob = bucket.blob(ref.name)
            return blob.download_as_bytes()
        except Exception as exc:
            raise ObjectStoreParseError(ref.uri, "Failed to read GCS report") from exc


class AzureBlobContainerReader:
    def __init__(
        self,
        account_name: str,
        container_name: str,
        prefix: str,
        credential: Any,
        source_uri: str | None = None,
    ) -> None:
        self.source_uri = source_uri or build_azblob_source(
            account_name,
            container_name,
            prefix,
        )
        self._account_name = account_name
        self._container_name = container_name
        self._prefix = prefix
        self._client = azure_blob.BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            credential=credential,
        )

    def list_reports(self) -> list[ReportRef]:
        refs: list[ReportRef] = []
        container_client = self._client.get_container_client(self._container_name)
        for blob in container_client.list_blobs(name_starts_with=self._prefix):
            if blob.name.endswith("/"):
                continue
            refs.append(
                ReportRef(
                    uri=f"azblob://{self._account_name}/{self._container_name}/{blob.name}",
                    name=blob.name,
                ),
            )
        return refs

    def read_bytes(self, ref: ReportRef) -> bytes:
        try:
            blob_client = self._client.get_blob_client(
                container=self._container_name,
                blob=ref.name,
            )
            return blob_client.download_blob().readall()
        except Exception as exc:
            raise ObjectStoreParseError(
                ref.uri,
                "Failed to read Azure Blob report",
            ) from exc


def filter_report_refs(
    refs: Iterable[ReportRef],
    *,
    suffix: str | None = None,
    predicate: Callable[[ReportRef], bool] | None = None,
) -> list[ReportRef]:
    filtered: list[ReportRef] = []
    for ref in refs:
        if suffix and not ref.name.endswith(suffix):
            continue
        if predicate and not predicate(ref):
            continue
        filtered.append(ref)
    return filtered


def read_text_report(
    reader: ReportReader,
    ref: ReportRef,
    *,
    encoding: str = "utf-8",
) -> str:
    try:
        return reader.read_bytes(ref).decode(encoding)
    except UnicodeDecodeError as exc:
        raise ObjectStoreParseError(
            ref.uri, f"Failed to decode {encoding} text"
        ) from exc


def read_json_report(
    reader: ReportReader,
    ref: ReportRef,
) -> Any:
    try:
        return json.loads(read_text_report(reader, ref))
    except json.JSONDecodeError as exc:
        raise ObjectStoreParseError(ref.uri, "Failed to parse JSON document") from exc
