import copy
from typing import Any


def _id(name: str) -> str:
    # 1Password UUIDs are 26 lowercase alphanumeric characters.
    return name.ljust(26, "0")


ACCOUNT_ID = _id("springfield")
OTHER_ACCOUNT_ID = _id("shelbyville")

HOMER_ID = _id("homer")
MARGE_ID = _id("marge")
BART_ID = _id("bart")
DEPLOY_BOT_ID = _id("deploybot")
COLLECTOR_ID = _id("collector")

OWNERS_ID = _id("owners")
ENGINEERING_ID = _id("engineering")

INFRA_VAULT_ID = _id("infra")
SHARED_VAULT_ID = _id("shared")

ROOT_LOGIN_ID = _id("rootlogin")
DEPLOY_KEY_ID = _id("deploykey")
OLD_NOTE_ID = _id("oldnote")

READ_ITEMS = 32
REVEAL_ITEM_PASSWORD = 16
MANAGE_VAULT = 2
UNKNOWN_BIT = 1 << 30

SNAPSHOT: dict[str, Any] = {
    "schema_version": "1.0",
    "collector": {"name": "subimage-collector-onepassword", "version": "0.1.0"},
    "provider": "onepassword",
    "account_id": ACCOUNT_ID,
    "collected_at": "2026-11-10T08:00:00Z",
    "snapshot_id": "11111111-1111-4111-8111-111111111111",
    "scope": {
        "kind": "configured_vaults",
        "vault_ids": [INFRA_VAULT_ID, SHARED_VAULT_ID],
        "include_archived": True,
    },
    "status": "complete",
    "users": [
        {
            "id": HOMER_ID,
            "name": "Homer Simpson",
            "email": "homer@example.com",
            "state": "ACTIVE",
            "type": "MEMBER",
        },
        {
            "id": MARGE_ID,
            "name": "Marge Simpson",
            "email": "marge@example.com",
            "state": "ACTIVE",
            "type": "MEMBER",
        },
        {
            "id": BART_ID,
            "name": "Bart Simpson",
            "email": "bart@example.com",
            "state": "SUSPENDED",
            "type": "GUEST",
        },
        {
            "id": DEPLOY_BOT_ID,
            "name": "Deploy bot",
            "email": "",
            "state": "ACTIVE",
            "type": "SERVICE_ACCOUNT",
        },
        # The collector's own service account is absent from the user directory,
        # so the snapshot knows only its ID and type.
        {"id": COLLECTOR_ID, "type": "SERVICE_ACCOUNT"},
    ],
    "groups": [
        {"id": ENGINEERING_ID, "name": "Engineering"},
        {"id": OWNERS_ID, "name": "Owners"},
    ],
    "group_memberships": [
        {"group_id": ENGINEERING_ID, "user_id": DEPLOY_BOT_ID},
        {"group_id": ENGINEERING_ID, "user_id": HOMER_ID},
        {"group_id": OWNERS_ID, "user_id": MARGE_ID},
    ],
    "vaults": [{"id": INFRA_VAULT_ID}, {"id": SHARED_VAULT_ID}],
    "vault_user_grants": [
        {
            "vault_id": INFRA_VAULT_ID,
            "user_id": BART_ID,
            "permissions": ["read_items"],
            "permissions_bitmask": READ_ITEMS,
        },
        {
            "vault_id": INFRA_VAULT_ID,
            "user_id": COLLECTOR_ID,
            "permissions": ["read_items"],
            "permissions_bitmask": READ_ITEMS,
        },
    ],
    "vault_group_grants": [
        {
            "vault_id": INFRA_VAULT_ID,
            "group_id": ENGINEERING_ID,
            "permissions": ["read_items", "reveal_item_password"],
            "permissions_bitmask": READ_ITEMS | REVEAL_ITEM_PASSWORD,
        },
        {
            "vault_id": SHARED_VAULT_ID,
            "group_id": OWNERS_ID,
            "permissions": ["manage_vault"],
            "permissions_bitmask": MANAGE_VAULT | UNKNOWN_BIT,
        },
    ],
    "items": [
        {
            "id": DEPLOY_KEY_ID,
            "vault_id": INFRA_VAULT_ID,
            "category": "SSH_KEY",
            "created_at": "2026-01-02T03:04:05Z",
            "updated_at": "2026-06-07T08:09:10Z",
            "version": 3,
        },
        {
            "id": OLD_NOTE_ID,
            "vault_id": SHARED_VAULT_ID,
            "category": "SECURE_NOTE",
            "state": "ARCHIVED",
            "created_at": "2025-01-02T03:04:05Z",
            "updated_at": "2025-01-02T03:04:05Z",
            "version": 1,
        },
        {
            "id": ROOT_LOGIN_ID,
            "vault_id": INFRA_VAULT_ID,
            "category": "LOGIN",
            "created_at": "2026-02-03T04:05:06Z",
            "updated_at": "2026-02-03T04:05:06Z",
            "version": 1,
        },
    ],
}


def newer_snapshot() -> dict[str, Any]:
    """
    The next collection after Bart left, Engineering lost password reveal on
    the infra vault, and Owners lost the shared vault.
    """
    snapshot = copy.deepcopy(SNAPSHOT)
    snapshot["collected_at"] = "2026-11-11T08:00:00Z"
    snapshot["snapshot_id"] = "22222222-2222-4222-8222-222222222222"
    snapshot["users"] = [user for user in snapshot["users"] if user["id"] != BART_ID]
    snapshot["vault_user_grants"] = [
        grant for grant in snapshot["vault_user_grants"] if grant["user_id"] != BART_ID
    ]
    snapshot["vault_group_grants"] = [
        {
            "vault_id": INFRA_VAULT_ID,
            "group_id": ENGINEERING_ID,
            "permissions": ["read_items"],
            "permissions_bitmask": READ_ITEMS,
        },
    ]
    return snapshot


def other_account_snapshot() -> dict[str, Any]:
    snapshot = copy.deepcopy(SNAPSHOT)
    snapshot["account_id"] = OTHER_ACCOUNT_ID
    snapshot["snapshot_id"] = "33333333-3333-4333-8333-333333333333"
    snapshot["users"] = [{"id": _id("bob"), "type": "SERVICE_ACCOUNT"}]
    snapshot["groups"] = []
    snapshot["group_memberships"] = []
    snapshot["vaults"] = [{"id": _id("shelbyvault"), "name": "Shelbyville"}]
    snapshot["scope"]["vault_ids"] = [_id("shelbyvault")]
    snapshot["vault_user_grants"] = []
    snapshot["vault_group_grants"] = []
    snapshot["items"] = []
    return snapshot
