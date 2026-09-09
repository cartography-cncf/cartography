import base64
import hashlib
from collections.abc import Sequence
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.runpod.util import get_string_list
from cartography.intel.runpod.util import require_non_empty
from cartography.models.runpod.sshkey import RunPodSSHKeySchema
from cartography.util import timeit


def _fingerprint(public_key: str | None) -> str | None:
    if not public_key:
        return None
    parts = public_key.split()
    if len(parts) < 2:
        return None
    try:
        raw_key = base64.b64decode(parts[1].encode("ascii"), validate=True)
    except (ValueError, TypeError):
        return None
    digest = (
        base64.b64encode(hashlib.sha256(raw_key).digest()).decode("ascii").rstrip("=")
    )
    return f"SHA256:{digest}"


@timeit
def get(session: requests.Session, base_url: str) -> list[str]:
    return get_string_list(session, base_url, "/account/ssh-keys", ("keys",))


def transform(
    keys: Sequence[str | dict[str, Any]], account_id: str
) -> list[dict[str, Any]]:
    transformed = []
    for key in keys:
        public_key: str | None
        if isinstance(key, str):
            public_key = key
            name = None
            fingerprint = _fingerprint(public_key)
            key_id = fingerprint
            created_at = None
        elif isinstance(key, dict):
            public_key = key.get("publicKey")
            name = key.get("name")
            fingerprint = key.get("fingerprint") or _fingerprint(public_key)
            key_id = key.get("id") or fingerprint
            created_at = key.get("createdAt")
        else:
            raise ValueError(
                f"RunPod SSH key entry must be a string or object, got "
                f"{type(key).__name__}."
            )

        transformed.append(
            {
                "id": require_non_empty(key_id, "SSH key id or fingerprint"),
                "account_id": account_id,
                "name": name,
                "fingerprint": fingerprint,
                "created_at": created_at,
            }
        )
    return transformed


@timeit
def load_ssh_keys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RunPodSSHKeySchema(),
        data,
        lastupdated=update_tag,
        RUNPOD_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RunPodSSHKeySchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    base_url: str,
    account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    keys = get(session, base_url)
    transformed = transform(keys, account_id)
    load_ssh_keys(neo4j_session, transformed, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
