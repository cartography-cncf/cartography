import json
from dataclasses import dataclass
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Protocol

import boto3

from cartography.intel.aws.util.botocore_config import create_boto3_client


@dataclass(frozen=True)
class ObjectRef:
    provider: str
    bucket: str
    key: str

    @property
    def uri(self) -> str:
        return f"{self.provider}://{self.bucket}/{self.key}"


class BucketReader(Protocol):
    def list_objects(self, bucket: str, prefix: str) -> list[ObjectRef]:
        pass

    def read_bytes(self, ref: ObjectRef) -> bytes:
        pass


class ObjectStoreParseError(ValueError):
    def __init__(self, source: str, message: str) -> None:
        super().__init__(f"{message}: {source}")
        self.source = source


class S3BucketReader:
    def __init__(self, boto3_session: boto3.Session) -> None:
        self._client = create_boto3_client(boto3_session, "s3")

    def list_objects(self, bucket: str, prefix: str) -> list[ObjectRef]:
        paginator = self._client.get_paginator("list_objects_v2")
        refs: list[ObjectRef] = []
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith("/"):
                    continue
                refs.append(
                    ObjectRef(
                        provider="s3",
                        bucket=bucket,
                        key=key,
                    ),
                )
        return refs

    def read_bytes(self, ref: ObjectRef) -> bytes:
        response = self._client.get_object(Bucket=ref.bucket, Key=ref.key)
        return response["Body"].read()


class GCSBucketReader:
    def __init__(self) -> None:
        from google.cloud import storage

        from cartography.intel.gcp.clients import get_gcp_credentials

        credentials = get_gcp_credentials()
        self._client = storage.Client(credentials=credentials)

    def list_objects(self, bucket: str, prefix: str) -> list[ObjectRef]:
        refs: list[ObjectRef] = []
        for blob in self._client.list_blobs(bucket, prefix=prefix):
            if blob.name.endswith("/"):
                continue
            refs.append(
                ObjectRef(
                    provider="gs",
                    bucket=bucket,
                    key=blob.name,
                ),
            )
        return refs

    def read_bytes(self, ref: ObjectRef) -> bytes:
        bucket = self._client.bucket(ref.bucket)
        blob = bucket.blob(ref.key)
        return blob.download_as_bytes()


class AzureBlobContainerReader:
    def __init__(self, account_name: str, credential: Any) -> None:
        from azure.storage.blob import BlobServiceClient

        self._account_name = account_name
        self._client = BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            credential=credential,
        )

    def list_objects(self, bucket: str, prefix: str) -> list[ObjectRef]:
        refs: list[ObjectRef] = []
        container_client = self._client.get_container_client(bucket)
        for blob in container_client.list_blobs(name_starts_with=prefix):
            if blob.name.endswith("/"):
                continue
            refs.append(
                ObjectRef(
                    provider="azblob",
                    bucket=f"{self._account_name}/{bucket}",
                    key=blob.name,
                ),
            )
        return refs

    def read_bytes(self, ref: ObjectRef) -> bytes:
        account_name, _sep, container_name = ref.bucket.partition("/")
        if not account_name or not container_name:
            raise ObjectStoreParseError(
                ref.uri,
                "Azure blob reference is missing account or container information",
            )
        blob_client = self._client.get_blob_client(
            container=container_name,
            blob=ref.key,
        )
        return blob_client.download_blob().readall()


def filter_object_refs(
    refs: Iterable[ObjectRef],
    *,
    suffix: str | None = None,
    predicate: Callable[[ObjectRef], bool] | None = None,
) -> list[ObjectRef]:
    filtered: list[ObjectRef] = []
    for ref in refs:
        if suffix and not ref.key.endswith(suffix):
            continue
        if predicate and not predicate(ref):
            continue
        filtered.append(ref)
    return filtered


def read_text_document(
    reader: BucketReader,
    ref: ObjectRef,
    *,
    encoding: str = "utf-8",
) -> str:
    try:
        return reader.read_bytes(ref).decode(encoding)
    except UnicodeDecodeError as exc:
        raise ObjectStoreParseError(
            ref.uri, f"Failed to decode {encoding} text"
        ) from exc


def read_json_document(
    reader: BucketReader,
    ref: ObjectRef,
) -> Any:
    try:
        return json.loads(read_text_document(reader, ref))
    except ObjectStoreParseError:
        raise
    except json.JSONDecodeError as exc:
        raise ObjectStoreParseError(ref.uri, "Failed to parse JSON document") from exc
