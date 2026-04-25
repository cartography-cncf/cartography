import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Protocol

import boto3

from cartography.intel.aws.util.botocore_config import create_boto3_client


@dataclass(frozen=True)
class ReportRef:
    uri: str
    name: str


# DEPRECATED: ObjectRef will be removed in v1.0.0. Use ReportRef.
class ObjectRef(ReportRef):
    def __init__(self, provider: str, bucket: str, key: str) -> None:
        object.__setattr__(self, "uri", f"{provider}://{bucket}/{key}")
        object.__setattr__(self, "name", key)
        object.__setattr__(self, "provider", provider)
        object.__setattr__(self, "bucket", bucket)
        object.__setattr__(self, "key", key)


class ReportReader(Protocol):
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
        with open(ref.uri, "rb") as file_pointer:
            data = file_pointer.read()
        if isinstance(data, str):
            return data.encode("utf-8")
        return data


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
        self.source_uri = source_uri or _build_cloud_source_uri("s3", bucket, prefix)
        self._bucket = bucket
        self._prefix = prefix
        self._client = create_boto3_client(boto3_session, "s3")

    def list_reports(self) -> list[ReportRef]:
        return self._list_reports(self._bucket, self._prefix)

    def _list_reports(self, bucket: str, prefix: str) -> list[ReportRef]:
        paginator = self._client.get_paginator("list_objects_v2")
        refs: list[ReportRef] = []
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith("/"):
                    continue
                refs.append(
                    ReportRef(
                        uri=f"s3://{bucket}/{key}",
                        name=key,
                    ),
                )
        return refs

    # DEPRECATED: list_objects() will be removed in v1.0.0.
    def list_objects(
        self,
        bucket: str | None = None,
        prefix: str | None = None,
    ) -> list[ReportRef]:
        if bucket is None and prefix is None:
            return self.list_reports()
        return self._list_reports(
            bucket or self._bucket,
            self._prefix if prefix is None else prefix,
        )

    def read_bytes(self, ref: ReportRef) -> bytes:
        response = self._client.get_object(
            Bucket=getattr(ref, "bucket", self._bucket),
            Key=getattr(ref, "key", ref.name),
        )
        return response["Body"].read()


class GCSBucketReader:
    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        source_uri: str | None = None,
    ) -> None:
        from google.cloud import storage

        from cartography.intel.gcp.clients import get_gcp_credentials

        self.source_uri = source_uri or _build_cloud_source_uri("gs", bucket, prefix)
        self._bucket = bucket
        self._prefix = prefix
        credentials = get_gcp_credentials()
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
        bucket = self._client.bucket(self._bucket)
        blob = bucket.blob(ref.name)
        return blob.download_as_bytes()


class AzureBlobContainerReader:
    def __init__(
        self,
        account_name: str,
        container_name: str,
        prefix: str,
        credential: Any,
        source_uri: str | None = None,
    ) -> None:
        from azure.storage.blob import BlobServiceClient

        self.source_uri = source_uri or _build_cloud_source_uri(
            "azblob",
            f"{account_name}/{container_name}",
            prefix,
        )
        self._account_name = account_name
        self._container_name = container_name
        self._prefix = prefix
        self._client = BlobServiceClient(
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
        blob_client = self._client.get_blob_client(
            container=self._container_name,
            blob=ref.name,
        )
        return blob_client.download_blob().readall()


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


def _build_cloud_source_uri(provider: str, bucket: str, prefix: str | None) -> str:
    normalized_prefix = (prefix or "").lstrip("/")
    if normalized_prefix:
        return f"{provider}://{bucket}/{normalized_prefix}"
    return f"{provider}://{bucket}"


# DEPRECATED: compatibility aliases will be removed in v1.0.0.
BucketReader = ReportReader
filter_object_refs = filter_report_refs
read_text_document = read_text_report
read_json_document = read_json_report
