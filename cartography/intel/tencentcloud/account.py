import logging
from typing import Any

import neo4j
from tencentcloud.common.credential import Credential

from cartography.client.core.tx import load
from cartography.intel.tencentcloud.util import build_client
from cartography.intel.tencentcloud.util import call
from cartography.models.tencentcloud.account import TencentCloudAccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(credential: Credential) -> dict[str, Any]:
    client = build_client(credential, "cam")
    return call(client, "GetUserAppId")


def transform(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(raw["OwnerUin"]),
        "app_id": str(raw["AppId"]),
    }


@timeit
def load_account(
    neo4j_session: neo4j.Session,
    account: dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        TencentCloudAccountSchema(),
        [account],
        lastupdated=update_tag,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credential: Credential,
    update_tag: int,
) -> dict[str, Any]:
    """Load the account that owns the credential and return it.

    The account is the tenant root: it is not cleaned up here, only refreshed.
    """
    account = transform(get(credential))
    logger.info("Syncing Tencent Cloud account %s.", account["id"])
    load_account(neo4j_session, account, update_tag)
    return account
