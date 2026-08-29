import json
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Protocol

from azure.storage import blob as azure_blob
from typing_extensions import Self

from cartography.intel.common.report_source import build_azblob_source
from cartography.intel.common.report_source import build_gcs_source
from cartography.intel.common.report_source import build_s3_source


@dataclass(frozen=True)
class ReportRef:
    """One enumerated report.

    uri: human-readable provenance string (used in logs and errors).
    name: backend-specific key passed to read_bytes (S3 object key, blob name,
    or absolute filesystem path).
    """

    uri: str
    name: str


class ReportReader(Protocol):
    """Source-bound reader for report ingestion.

    Lifecycle: readers should be used as context managers so backend clients
    (e.g. Azure BlobServiceClient) release their connection pools on exit.

    Ordering: list_reports() returns refs in lexicographic name order. Callers
    that depend on a specific order must sort explicitly.

    Memory: read_bytes() loads the full object into memory. Reports are
    expected to fit comfortably in RAM (typical scan outputs are <10 MB).
    """

    source_uri: str

    def list_reports(self) -> list[ReportRef]:
        pass

    def read_bytes(self, ref: ReportRef) -> bytes:
        pass

    def close(self) -> None:
        pass

    def __enter__(self) -> Self:
        pass

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass


class ObjectStoreError(Exception):
    """Raised on read or parse failures from a ReportReader.

    Covers both transport failures (S3/GCS/Azure exceptions, local OSError)
    and decode/parse failures (UnicodeDecodeError, JSONDecodeError).
    """

    def __init__(self, message: str, *, source: str | None = None) -> None:
        super().__init__(f"{message}: {source}" if source else message)
        self.source = source


class _BaseReader:
    """Default context-manager and close() behavior for readers.

    Subclasses override close() when they hold resources that need releasing.
    """

    def close(self) -> None:
        pass

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class LocalReportReader(_BaseReader):
    def __init__(self, source_path: str) -> None:
        self.source_uri = source_path
        self._root = Path(source_path)

    def list_reports(self) -> list[ReportRef]:
        if self._root.is_file():
            return [ReportRef(uri=str(self._root), name=self._root.name)]

        refs: list[ReportRef] = [
            ReportRef(
                uri=str(path),
                name=str(path.relative_to(self._root)),
            )
            for path in self._root.rglob("*")
            if path.is_file()
        ]
        refs.sort(key=lambda r: r.name)
        return refs

    def read_bytes(self, ref: ReportRef) -> bytes:
        try:
            with open(ref.uri, "rb") as file_pointer:
                return file_pointer.read()
        except OSError as exc:
            raise ObjectStoreError(
                "Failed to read local report", source=ref.uri
            ) from exc


class ListedReportReader(_BaseReader):
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


class S3BucketReader(_BaseReader):
    def __init__(
        self,
        boto3_session: Any,
        bucket: str,
        prefix: str = "",
        source_uri: str | None = None,
    ) -> None:
        from cartography.intel.aws.util.botocore_config import create_boto3_client

        self.source_uri = source_uri or build_s3_source(bucket, prefix)
        self._bucket = bucket
        self._prefix = prefix
        self._client = create_boto3_client(boto3_session, "s3")

    def close(self) -> None:
        self._client.close()

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
        from botocore.exceptions import BotoCoreError
        from botocore.exceptions import ClientError

        expected_prefix = f"s3://{self._bucket}/"
        if not ref.uri.startswith(expected_prefix):
            raise ObjectStoreError(
                f"Ref does not belong to S3 bucket {self._bucket!r}",
                source=ref.uri,
            )

        try:
            response = self._client.get_object(Bucket=self._bucket, Key=ref.name)
        except (BotoCoreError, ClientError) as exc:
            raise ObjectStoreError("Failed to read S3 report", source=ref.uri) from exc

        body = response["Body"]
        try:
            return body.read()
        except (BotoCoreError, ClientError) as exc:
            raise ObjectStoreError("Failed to read S3 report", source=ref.uri) from exc
        finally:
            body.close()


class GCSBucketReader(_BaseReader):
    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        source_uri: str | None = None,
    ) -> None:
        self.source_uri = source_uri or build_gcs_source(bucket, prefix)
        self._bucket = bucket
        self._prefix = prefix
        from google.cloud import storage

        import cartography.intel.gcp.clients as gcp_clients

        credentials = gcp_clients.get_gcp_credentials()
        self._client = storage.Client(credentials=credentials)

    def close(self) -> None:
        self._client.close()

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
        from google.api_core import exceptions as google_exceptions

        expected_prefix = f"gs://{self._bucket}/"
        if not ref.uri.startswith(expected_prefix):
            raise ObjectStoreError(
                f"Ref does not belong to GCS bucket {self._bucket!r}",
                source=ref.uri,
            )

        try:
            bucket = self._client.bucket(self._bucket)
            blob = bucket.blob(ref.name)
            return blob.download_as_bytes()
        except google_exceptions.GoogleAPIError as exc:
            raise ObjectStoreError("Failed to read GCS report", source=ref.uri) from exc


class AzureBlobContainerReader(_BaseReader):
    def __init__(
        self,
        account_name: str,
        container_name: str,
        prefix: str,
        credential: Any = None,
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

        if credential is None:
            from azure.identity import AzureCliCredential

            credential = AzureCliCredential()

        self._client = azure_blob.BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            credential=credential,
        )

    def close(self) -> None:
        self._client.close()

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
        from azure.core import exceptions as azure_exceptions

        expected_prefix = f"azblob://{self._account_name}/{self._container_name}/"
        if not ref.uri.startswith(expected_prefix):
            raise ObjectStoreError(
                f"Ref does not belong to Azure container {self._account_name}/{self._container_name}",
                source=ref.uri,
            )

        try:
            blob_client = self._client.get_blob_client(
                container=self._container_name,
                blob=ref.name,
            )
            return blob_client.download_blob().readall()
        except azure_exceptions.AzureError as exc:
            raise ObjectStoreError(
                "Failed to read Azure Blob report", source=ref.uri
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
        raise ObjectStoreError(
            f"Failed to decode {encoding} text", source=ref.uri
        ) from exc


def read_json_report(
    reader: ReportReader,
    ref: ReportRef,
) -> Any:
    try:
        return json.loads(read_text_report(reader, ref))
    except json.JSONDecodeError as exc:
        raise ObjectStoreError("Failed to parse JSON document", source=ref.uri) from exc
