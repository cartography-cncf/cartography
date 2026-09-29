import logging
from typing import Any
from urllib.parse import quote

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.util import fetch_many
from cartography.intel.zoom.util import is_zoom_error
from cartography.intel.zoom.util import optional_call
from cartography.models.zoom.settings import ZoomSecuritySettingsSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Only these scalar policy fields leave the provider response. In particular,
# password values, authentication profiles, and arbitrary settings are excluded.
BOOLEAN_FIELDS = {
    "sso_enabled": ("security", "signin_with_sso", "enable"),
    "require_sso_for_domains": (
        "security",
        "signin_with_sso",
        "require_sso_for_domains",
    ),
    "sign_in_with_work_email": ("security", "sign_in_with_work_email"),
    "meeting_authentication": ("meeting_authentication", "meeting_authentication"),
    "allow_authentication_exception": (
        "meeting_authentication",
        "allow_authentication_exception",
    ),
    "recording_authentication": (
        "recording_authentication",
        "recording_authentication",
    ),
    "waiting_room": ("meeting_security", "waiting_room"),
    "auto_security": ("meeting_security", "auto_security"),
    "meeting_passcode_required": ("meeting_security", "meeting_password"),
    "phone_passcode_required": ("meeting_security", "phone_password"),
    "pmi_passcode_required": ("meeting_security", "pmi_password"),
    "embed_passcode_in_join_link": ("meeting_security", "embed_password_in_join_link"),
    "only_authenticated_can_join_from_webclient": (
        "meeting_security",
        "only_authenticated_can_join_from_webclient",
    ),
    "end_to_end_encrypted_meetings": (
        "meeting_security",
        "end_to_end_encrypted_meetings",
    ),
    "join_before_host": ("default", "schedule_meeting", "join_before_host"),
    "file_transfer": ("default", "in_meeting", "file_transfer"),
    "private_chat": ("default", "in_meeting", "private_chat"),
    # Account settings only; group and user responses do not expose it.
    "allow_participants_to_rename": (
        "default",
        "in_meeting",
        "allow_participants_to_rename",
    ),
    "screen_sharing": ("default", "in_meeting", "screen_sharing"),
    "remote_control": ("default", "in_meeting", "remote_control"),
    "cloud_recording": ("default", "recording", "cloud_recording"),
    "local_recording": ("default", "recording", "local_recording"),
    "cloud_recording_download": ("default", "recording", "cloud_recording_download"),
    "cloud_recording_download_host": (
        "default",
        "recording",
        "cloud_recording_download_host",
    ),
    "recording_sharing": ("default", "recording", "allow_share"),
    "recording_account_members_only": (
        "default",
        "recording",
        "account_user_access_recording",
    ),
    "recording_passcode_required": (
        "default",
        "recording",
        "required_password_for_shared_cloud_recordings",
    ),
    "recording_embed_passcode_in_link": (
        "default",
        "recording",
        "embed_passcode_in_shareable_link",
    ),
    "recording_invitees_without_passcode": (
        "default",
        "recording",
        "allow_invitees_access_recordings_without_passcode",
    ),
    # Account and user settings; account and group lock flags.
    "auto_delete_cloud_recordings": ("default", "recording", "auto_delete_cmr"),
}

# Configured-only non-boolean values. Lock endpoints return flags, not values.
INTEGER_FIELDS = {
    "auto_delete_cloud_recordings_days": (
        "default",
        "recording",
        "auto_delete_cmr_days",
    ),
    "waiting_room_scope": (
        "meeting_security",
        "waiting_room_settings",
        "participants_to_place_in_waiting_room",
    ),
    "sign_again_period_for_inactivity_on_client": (
        "security",
        "sign_again_period_for_inactivity_on_client",
    ),
    "sign_again_period_for_inactivity_on_web": (
        "security",
        "sign_again_period_for_inactivity_on_web",
    ),
}
# Returned only when sign_in_with_two_factor_auth is group or role.
ID_LIST_FIELDS = {
    "two_factor_auth_group_ids": ("security", "sign_in_with_two_factor_auth_groups"),
    "two_factor_auth_role_ids": ("security", "sign_in_with_two_factor_auth_roles"),
}
# Documented codes for an owner deleted after the group or user list was read.
MISSING_OWNER_CODES = {"group": 4130, "user": 1001}


def get(
    client: ZoomClient,
    path: str,
    scope_type: str,
    kind: str,
) -> dict[str, dict[str, Any]]:
    """Fetch a complete owner/kind before replacing any of its policy values."""
    result = {"default": client.get(path)}
    options = ["meeting_security"]
    if kind == "configured":
        options.extend(("meeting_authentication", "recording_authentication"))
        if scope_type == "account":
            options.append("security")
    for option in options:
        result[option] = client.get(path, {"option": option})
    return result


def _value(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = data
    for key in path:
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ValueError(
                "Zoom settings response contains a malformed policy section"
            )
        value = value.get(key)
    return value


def transform(
    responses: dict[str, dict[str, Any]],
    account_id: str,
    scope_type: str,
    scope_id: str,
    kind: str,
) -> dict[str, Any]:
    default = responses["default"]
    data: dict[str, Any] = {"default": default}
    for section in ("security", "meeting_security"):
        response = responses.get(section, {})
        data[section] = response.get(section, response)
    for section in ("meeting_authentication", "recording_authentication"):
        if kind == "locked":
            parent = (
                "schedule_meeting"
                if section == "meeting_authentication"
                else "recording"
            )
            data[section] = {section: _value(default, (parent, section))}
        else:
            response = responses[section]
            # The Users API documents both top-level and nested auth variants.
            options = response.get("authentication_options")
            data[section] = (
                options.get(section, {}) if isinstance(options, dict) else response
            )

    result: dict[str, Any] = {
        "id": f"{account_id}:settings:{scope_type}:{scope_id}:{kind}",
        "scope_type": scope_type,
        "scope_id": scope_id,
        "kind": kind,
        "account_owner_id": account_id if scope_type == "account" else None,
        "group_owner_id": (
            f"{account_id}:group:{scope_id}" if scope_type == "group" else None
        ),
        "user_owner_id": (
            f"{account_id}:user:{scope_id}" if scope_type == "user" else None
        ),
    }
    for field, path in BOOLEAN_FIELDS.items():
        value = _value(data, path)
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"Zoom settings {field} must be a boolean")
        result[field] = value

    for field, path, allowed in (
        (
            "sign_in_with_two_factor_auth",
            ("security", "sign_in_with_two_factor_auth"),
            {"all", "group", "role", "none"},
        ),
        (
            "encryption_type",
            ("meeting_security", "encryption_type"),
            {"enhanced_encryption", "e2ee"},
        ),
        (
            "who_can_share_screen",
            ("default", "in_meeting", "who_can_share_screen"),
            {"host", "all"},
        ),
    ):
        # Lock endpoints report lock flags, not configured enum values.
        value = _value(data, path) if kind == "configured" else None
        if value is not None and (not isinstance(value, str) or value not in allowed):
            raise ValueError(f"Zoom settings {field} has an unsupported value")
        result[field] = value

    for field, path in INTEGER_FIELDS.items():
        value = _value(data, path) if kind == "configured" else None
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool)
        ):
            raise ValueError(f"Zoom settings {field} must be an integer")
        result[field] = value
    for field, path in ID_LIST_FIELDS.items():
        value = _value(data, path) if kind == "configured" else None
        if value is not None and (
            not isinstance(value, list)
            or not all(isinstance(item, str) for item in value)
        ):
            raise ValueError(f"Zoom settings {field} must be a list of IDs")
        result[field] = value
    return result


def read(
    client: ZoomClient,
    owner: tuple[str, str, str, str],
    unavailable: set[str],
) -> dict[str, dict[str, Any]] | None:
    scope_type, _, path, kind = owner
    endpoint = "settings" if kind == "configured" else "lock_settings"

    def fetch() -> dict[str, dict[str, Any]] | None:
        try:
            return get(client, f"{path}/{endpoint}", scope_type, kind)
        except requests.HTTPError as exc:
            code = MISSING_OWNER_CODES.get(scope_type)
            if code is not None and is_zoom_error(exc, 404, code):
                logger.warning(
                    "Zoom %s no longer exists; preserving its settings until removed",
                    scope_type,
                )
                return None
            raise

    return optional_call(f"{scope_type} {kind} settings", fetch, unavailable)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: ZoomClient,
    account_id: str,
    update_tag: int,
    users: list[dict[str, Any]],
    groups: list[dict[str, Any]] | None,
) -> None:
    logger.info("Syncing Zoom security settings")
    owners = [("account", account_id, "/accounts/me")]
    owners.extend(
        ("group", group["id"], f"/groups/{quote(group['id'], safe='')}")
        for group in groups or []
    )
    owners.extend(
        ("user", user["zoom_id"], f"/users/{quote(user['zoom_id'], safe='')}")
        for user in users
        if user.get("zoom_id") and user["status"] != "pending"
    )
    reads = [
        (scope_type, scope_id, path, kind)
        for scope_type, scope_id, path in owners
        for kind in (
            ("configured",) if scope_type == "user" else ("configured", "locked")
        )
    ]
    unavailable: set[str] = set()
    responses = fetch_many(
        client, reads, lambda worker, owner: read(worker, owner, unavailable)
    )
    records = [
        transform(response, account_id, scope_type, scope_id, kind)
        for (scope_type, scope_id, _, kind), response in zip(
            reads, responses, strict=True
        )
        if response is not None
    ]
    # Each owner/kind has one stable node. load() clears absent properties;
    # unread owner/kinds are not loaded and keep their snapshots. Removed groups
    # and users take their settings with them during their own cleanup.
    load(
        neo4j_session,
        ZoomSecuritySettingsSchema(),
        records,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )
    if len(records) < len(reads):
        logger.warning(
            "Zoom settings: %d of %d owner snapshots were not read; preserving them.",
            len(reads) - len(records),
            len(reads),
        )
