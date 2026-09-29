from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.zoom.resource import ZoomAccountResourceRel
from cartography.models.zoom.resource import ZoomResourceRelProperties


@dataclass(frozen=True)
class ZoomSecuritySettingsNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped owner and settings-kind identity."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID",
        set_in_kwargs=True,
        extra_index=True,
        description="Owning Zoom account ID.",
    )
    scope_type: PropertyRef = PropertyRef(
        "scope_type", description="Owner type: account, group, or user."
    )
    scope_id: PropertyRef = PropertyRef(
        "scope_id", description="Provider ID of the owning account, group, or user."
    )
    kind: PropertyRef = PropertyRef(
        "kind",
        description="configured contains values; locked contains lock flags, not enabled values.",
    )
    sso_enabled: PropertyRef = PropertyRef(
        "sso_enabled", description="security.signin_with_sso.enable."
    )
    require_sso_for_domains: PropertyRef = PropertyRef(
        "require_sso_for_domains",
        description="security.signin_with_sso.require_sso_for_domains; domains are not collected.",
    )
    sign_in_with_work_email: PropertyRef = PropertyRef(
        "sign_in_with_work_email", description="security.sign_in_with_work_email."
    )
    sign_in_with_two_factor_auth: PropertyRef = PropertyRef(
        "sign_in_with_two_factor_auth",
        description="security.sign_in_with_two_factor_auth: all, group, role, or none; configured only.",
    )
    meeting_authentication: PropertyRef = PropertyRef(
        "meeting_authentication",
        description="option=meeting_authentication meeting_authentication, or schedule_meeting.meeting_authentication for locks.",
    )
    allow_authentication_exception: PropertyRef = PropertyRef(
        "allow_authentication_exception",
        description="option=meeting_authentication allow_authentication_exception.",
    )
    recording_authentication: PropertyRef = PropertyRef(
        "recording_authentication",
        description="option=recording_authentication recording_authentication, or recording.recording_authentication for locks.",
    )
    waiting_room: PropertyRef = PropertyRef(
        "waiting_room", description="meeting_security.waiting_room."
    )
    auto_security: PropertyRef = PropertyRef(
        "auto_security",
        description="meeting_security.auto_security; require at least one meeting security option.",
    )
    meeting_passcode_required: PropertyRef = PropertyRef(
        "meeting_passcode_required",
        description="meeting_security.meeting_password; stores the policy, never the passcode.",
    )
    phone_passcode_required: PropertyRef = PropertyRef(
        "phone_passcode_required",
        description="meeting_security.phone_password; stores the policy, never the passcode.",
    )
    pmi_passcode_required: PropertyRef = PropertyRef(
        "pmi_passcode_required",
        description="meeting_security.pmi_password boolean policy; never schedule_meeting.pmi_password, which is a secret.",
    )
    embed_passcode_in_join_link: PropertyRef = PropertyRef(
        "embed_passcode_in_join_link",
        description="meeting_security.embed_password_in_join_link.",
    )
    only_authenticated_can_join_from_webclient: PropertyRef = PropertyRef(
        "only_authenticated_can_join_from_webclient",
        description="meeting_security.only_authenticated_can_join_from_webclient.",
    )
    end_to_end_encrypted_meetings: PropertyRef = PropertyRef(
        "end_to_end_encrypted_meetings",
        description="meeting_security.end_to_end_encrypted_meetings.",
    )
    encryption_type: PropertyRef = PropertyRef(
        "encryption_type",
        description="meeting_security.encryption_type: enhanced_encryption or e2ee; configured only.",
    )
    join_before_host: PropertyRef = PropertyRef(
        "join_before_host", description="schedule_meeting.join_before_host."
    )
    file_transfer: PropertyRef = PropertyRef(
        "file_transfer", description="in_meeting.file_transfer."
    )
    private_chat: PropertyRef = PropertyRef(
        "private_chat",
        description="in_meeting.private_chat; allows participants to message each other privately.",
    )
    allow_participants_to_rename: PropertyRef = PropertyRef(
        "allow_participants_to_rename",
        description="in_meeting.allow_participants_to_rename; configured account snapshots only.",
    )
    screen_sharing: PropertyRef = PropertyRef(
        "screen_sharing", description="in_meeting.screen_sharing."
    )
    who_can_share_screen: PropertyRef = PropertyRef(
        "who_can_share_screen",
        description="in_meeting.who_can_share_screen: host or all; configured only.",
    )
    remote_control: PropertyRef = PropertyRef(
        "remote_control", description="in_meeting.remote_control."
    )
    cloud_recording: PropertyRef = PropertyRef(
        "cloud_recording", description="recording.cloud_recording."
    )
    local_recording: PropertyRef = PropertyRef(
        "local_recording", description="recording.local_recording."
    )
    cloud_recording_download: PropertyRef = PropertyRef(
        "cloud_recording_download", description="recording.cloud_recording_download."
    )
    cloud_recording_download_host: PropertyRef = PropertyRef(
        "cloud_recording_download_host",
        description="recording.cloud_recording_download_host; restrict downloads to the host.",
    )
    recording_sharing: PropertyRef = PropertyRef(
        "recording_sharing", description="recording.allow_share."
    )
    recording_account_members_only: PropertyRef = PropertyRef(
        "recording_account_members_only",
        description="recording.account_user_access_recording.",
    )
    recording_passcode_required: PropertyRef = PropertyRef(
        "recording_passcode_required",
        description="recording.required_password_for_shared_cloud_recordings.",
    )
    recording_embed_passcode_in_link: PropertyRef = PropertyRef(
        "recording_embed_passcode_in_link",
        description="recording.embed_passcode_in_shareable_link.",
    )
    recording_invitees_without_passcode: PropertyRef = PropertyRef(
        "recording_invitees_without_passcode",
        description="recording.allow_invitees_access_recordings_without_passcode.",
    )
    auto_delete_cloud_recordings: PropertyRef = PropertyRef(
        "auto_delete_cloud_recordings",
        description="recording.auto_delete_cmr; account and user values, account and group lock flags.",
    )
    auto_delete_cloud_recordings_days: PropertyRef = PropertyRef(
        "auto_delete_cloud_recordings_days",
        description="recording.auto_delete_cmr_days, such as 30, 60, 90 or 120; configured account and user only.",
    )
    waiting_room_scope: PropertyRef = PropertyRef(
        "waiting_room_scope",
        description="meeting_security.waiting_room_settings.participants_to_place_in_waiting_room: 0 all participants, 1 users outside the account, 2 users outside the account and allowed domains; configured only.",
    )
    two_factor_auth_group_ids: PropertyRef = PropertyRef(
        "two_factor_auth_group_ids",
        description="security.sign_in_with_two_factor_auth_groups; provider group IDs requiring 2FA when sign_in_with_two_factor_auth is group. Configured account only.",
    )
    two_factor_auth_role_ids: PropertyRef = PropertyRef(
        "two_factor_auth_role_ids",
        description="security.sign_in_with_two_factor_auth_roles; provider role IDs requiring 2FA when sign_in_with_two_factor_auth is role. Configured account only.",
    )
    sign_again_period_for_inactivity_on_client: PropertyRef = PropertyRef(
        "sign_again_period_for_inactivity_on_client",
        description="security.sign_again_period_for_inactivity_on_client; minutes of client inactivity before sign-out, 0 when disabled. Configured account only.",
    )
    sign_again_period_for_inactivity_on_web: PropertyRef = PropertyRef(
        "sign_again_period_for_inactivity_on_web",
        description="security.sign_again_period_for_inactivity_on_web; minutes of web inactivity before sign-out, 0 when disabled. Configured account only.",
    )


@dataclass(frozen=True)
class ZoomAccountHasSettingsRel(CartographyRelSchema):
    target_node_label: str = "ZoomAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_owner_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SETTINGS"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomGroupHasSettingsRel(CartographyRelSchema):
    target_node_label: str = "ZoomGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_owner_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SETTINGS"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomUserHasSettingsRel(CartographyRelSchema):
    target_node_label: str = "ZoomUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_owner_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SETTINGS"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomGroupOwnsSettingsRel(CartographyRelSchema):
    """The group owns these settings; removing the group removes them."""

    target_node_label: str = "ZoomGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_owner_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomUserOwnsSettingsRel(CartographyRelSchema):
    """The user owns these settings; removing the user removes them."""

    target_node_label: str = "ZoomUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_owner_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomSecuritySettingsSchema(CartographyNodeSchema):
    """Allowlisted security policy metadata from Zoom's settings endpoints.

    Configured values and lock flags are separate nodes. A locked flag describes
    whether members may change a setting, not whether that setting is enabled.
    These are provider-reported settings, not a computed inheritance hierarchy.
    Missing values are unknown. Passcodes and raw settings payloads are excluded.
    Denied snapshots are retained until their owning group or user is removed.
    """

    label: str = "ZoomSecuritySettings"
    properties: ZoomSecuritySettingsNodeProperties = (
        ZoomSecuritySettingsNodeProperties()
    )
    sub_resource_relationship: ZoomAccountResourceRel = ZoomAccountResourceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ZoomAccountHasSettingsRel(),
            ZoomGroupHasSettingsRel(),
            ZoomUserHasSettingsRel(),
            ZoomGroupOwnsSettingsRel(),
            ZoomUserOwnsSettingsRel(),
        ]
    )
