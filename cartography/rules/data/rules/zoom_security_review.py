from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference


class ZoomSecurityReviewOutput(Finding):
    asset_name: str | None = None
    asset_id: str | None = None
    account_id: str | None = None
    issue: str | None = None
    current_value: str | None = None


_meeting_admission_controls = Fact(
    id="zoom_meeting_admission_controls",
    name="Meetings without admission controls",
    description=(
        "Unexpired scheduled meetings with explicitly disabled passcode, waiting room "
        "and participant authentication, without registration. This describes "
        "configured controls, not verified public reachability."
    ),
    cypher_query="""
    MATCH (n:ZoomMeeting)
    WHERE n.password_protected = false AND n.waiting_room = false
        AND n.meeting_authentication = false AND n.approval_type = 2
    RETURN coalesce(n.topic, n.meeting_id, n.id) AS asset_name,
        n.id AS asset_id, n.account_id AS account_id,
        'meeting_admission_controls' AS issue,
        'No passcode, waiting room, participant authentication or registration' AS current_value
    """,
    cypher_visual_query="""
    MATCH (n:ZoomMeeting)
    WHERE n.password_protected = false AND n.waiting_room = false
        AND n.meeting_authentication = false AND n.approval_type = 2
    RETURN n
    """,
    cypher_count_query="""
    MATCH (n:ZoomMeeting)
    WHERE n.password_protected IS NOT NULL AND n.waiting_room IS NOT NULL
        AND n.meeting_authentication IS NOT NULL AND n.approval_type IS NOT NULL
    RETURN count(n) AS count
    """,
    asset_label="ZoomMeeting",
    asset_id_field="asset_id",
    identity_fields=("asset_id", "issue"),
    module=Module.ZOOM,
    maturity=Maturity.EXPERIMENTAL,
)


_recording_viewer_controls = Fact(
    id="zoom_recording_viewer_controls",
    name="Publicly shared recordings without viewer controls",
    description=(
        "Recordings configured for public sharing without a passcode, viewer "
        "authentication or registration. This does not test whether a recording URL "
        "is reachable."
    ),
    cypher_query="""
    MATCH (n:ZoomRecording)
    WHERE n.share_recording = 'publicly' AND n.password_protected = false
        AND n.recording_authentication = false AND n.on_demand = false
    RETURN coalesce(n.topic, n.meeting_uuid, n.id) AS asset_name,
        n.id AS asset_id, n.account_id AS account_id,
        'recording_viewer_controls' AS issue,
        'Public sharing without passcode, authentication or registration' AS current_value
    """,
    cypher_visual_query="""
    MATCH (n:ZoomRecording)
    WHERE n.share_recording = 'publicly' AND n.password_protected = false
        AND n.recording_authentication = false AND n.on_demand = false
    RETURN n
    """,
    cypher_count_query="""
    MATCH (n:ZoomRecording)
    WHERE n.share_recording IS NOT NULL AND n.password_protected IS NOT NULL
        AND n.recording_authentication IS NOT NULL AND n.on_demand IS NOT NULL
    RETURN count(n) AS count
    """,
    asset_label="ZoomRecording",
    asset_id_field="asset_id",
    identity_fields=("asset_id", "issue"),
    module=Module.ZOOM,
    maturity=Maturity.EXPERIMENTAL,
)


_account_meeting_defaults = Fact(
    id="zoom_account_meeting_defaults",
    name="Account defaults without meeting admission controls",
    description=(
        "Configured account defaults explicitly disable every collected meeting "
        "admission control. Group or user overrides and lock flags are not treated as "
        "effective account policy."
    ),
    cypher_query="""
    MATCH (n:ZoomSecuritySettings)
    WHERE n.scope_type = 'account' AND n.kind = 'configured'
        AND n.meeting_passcode_required = false AND n.waiting_room = false
        AND n.meeting_authentication = false AND n.auto_security = false
    RETURN 'Meeting defaults for ' + n.account_id AS asset_name,
        n.id AS asset_id, n.account_id AS account_id,
        'account_meeting_defaults' AS issue,
        'Passcode, waiting room, authentication and auto-security disabled' AS current_value
    """,
    cypher_visual_query="""
    MATCH (n:ZoomSecuritySettings)
    WHERE n.scope_type = 'account' AND n.kind = 'configured'
        AND n.meeting_passcode_required = false AND n.waiting_room = false
        AND n.meeting_authentication = false AND n.auto_security = false
    RETURN n
    """,
    cypher_count_query="""
    MATCH (n:ZoomSecuritySettings)
    WHERE n.scope_type = 'account' AND n.kind = 'configured'
        AND n.meeting_passcode_required IS NOT NULL AND n.waiting_room IS NOT NULL
        AND n.meeting_authentication IS NOT NULL AND n.auto_security IS NOT NULL
    RETURN count(n) AS count
    """,
    asset_label="ZoomSecuritySettings",
    asset_id_field="asset_id",
    identity_fields=("asset_id", "issue"),
    module=Module.ZOOM,
    maturity=Maturity.EXPERIMENTAL,
)


_native_signin_two_factor_policy = Fact(
    id="zoom_native_signin_two_factor_policy",
    name="Native sign-in allowed without a two-factor requirement",
    description=(
        "Account policy permits Zoom work-email sign-in, disables the two-factor "
        "requirement and does not require SSO for domains. This does not infer "
        "individual MFA enrollment or identity-provider protection."
    ),
    cypher_query="""
    MATCH (n:ZoomSecuritySettings)
    WHERE n.scope_type = 'account' AND n.kind = 'configured'
        AND n.sign_in_with_work_email = true
        AND n.sign_in_with_two_factor_auth = 'none'
        AND n.require_sso_for_domains = false
    RETURN 'Sign-in policy for ' + n.account_id AS asset_name,
        n.id AS asset_id, n.account_id AS account_id,
        'native_signin_two_factor_policy' AS issue,
        'Native sign-in allowed; two-factor requirement disabled' AS current_value
    """,
    cypher_visual_query="""
    MATCH (n:ZoomSecuritySettings)
    WHERE n.scope_type = 'account' AND n.kind = 'configured'
        AND n.sign_in_with_work_email = true
        AND n.sign_in_with_two_factor_auth = 'none'
        AND n.require_sso_for_domains = false
    RETURN n
    """,
    cypher_count_query="""
    MATCH (n:ZoomSecuritySettings)
    WHERE n.scope_type = 'account' AND n.kind = 'configured'
        AND n.sign_in_with_work_email IS NOT NULL
        AND n.sign_in_with_two_factor_auth IS NOT NULL
        AND n.require_sso_for_domains IS NOT NULL
    RETURN count(n) AS count
    """,
    asset_label="ZoomSecuritySettings",
    asset_id_field="asset_id",
    identity_fields=("asset_id", "issue"),
    module=Module.ZOOM,
    maturity=Maturity.EXPERIMENTAL,
)


_unrestricted_edit_roles = Fact(
    id="zoom_unrestricted_edit_roles",
    name="Assigned roles with unrestricted edit privileges",
    description=(
        "Assigned roles grant edit privileges without a reported group restriction. "
        "Review least privilege; this is an administration surface, not evidence that "
        "the assignment is unauthorized."
    ),
    cypher_query="""
    MATCH (n:ZoomRole)
    WHERE EXISTS { MATCH (:ZoomUser)-[:HAS_ROLE]->(n) }
        AND EXISTS { MATCH (n)-[:GRANTS]->(p:ZoomRolePrivilege)
            WHERE p.restricted_to_groups = false AND p.privilege ENDS WITH ':Edit' }
    RETURN coalesce(n.name, n.id) AS asset_name,
        n.id AS asset_id, n.account_id AS account_id,
        'unrestricted_edit_roles' AS issue,
        'Assigned role has edit privileges without group restrictions' AS current_value
    """,
    cypher_visual_query="""
    MATCH (n:ZoomRole)
    WHERE EXISTS { MATCH (:ZoomUser)-[:HAS_ROLE]->(n) }
        AND EXISTS { MATCH (n)-[:GRANTS]->(p:ZoomRolePrivilege)
            WHERE p.restricted_to_groups = false AND p.privilege ENDS WITH ':Edit' }
    RETURN n
    """,
    cypher_count_query="""
    MATCH (n:ZoomRole)
    WHERE EXISTS { MATCH (:ZoomUser)-[:HAS_ROLE]->(n) }
        AND EXISTS { MATCH (n)-[:GRANTS]->(:ZoomRolePrivilege) }
    RETURN count(n) AS count
    """,
    asset_label="ZoomRole",
    asset_id_field="asset_id",
    identity_fields=("asset_id", "issue"),
    module=Module.ZOOM,
    maturity=Maturity.EXPERIMENTAL,
)


_third_party_admin_write_scopes = Fact(
    id="zoom_third_party_admin_write_scopes",
    name="Installed third-party apps with administrative write scopes",
    description=(
        "Account-added third-party apps with reported admin scopes for write, create, "
        "update or delete operations. Review whether the scopes are needed; "
        "installation and scopes do not prove an active token or malicious behavior."
    ),
    cypher_query="""
    MATCH (n:ZoomApp)
    WHERE n.installed = true AND n.developer_type = 'THIRD_PARTY'
        AND any(scope IN n.app_scopes WHERE scope ENDS WITH ':admin'
            AND split(scope, ':')[1] IN ['write', 'create', 'update', 'delete'])
    RETURN coalesce(n.name, n.app_id, n.id) AS asset_name,
        n.id AS asset_id, n.account_id AS account_id,
        'third_party_admin_write_scopes' AS issue,
        head([scope IN n.app_scopes WHERE scope ENDS WITH ':admin'
            AND split(scope, ':')[1] IN ['write', 'create', 'update', 'delete']]) AS current_value
    """,
    cypher_visual_query="""
    MATCH (n:ZoomApp)
    WHERE n.installed = true AND n.developer_type = 'THIRD_PARTY'
        AND any(scope IN n.app_scopes WHERE scope ENDS WITH ':admin'
            AND split(scope, ':')[1] IN ['write', 'create', 'update', 'delete'])
    RETURN n
    """,
    cypher_count_query="""
    MATCH (n:ZoomApp)
    WHERE n.installed = true AND n.developer_type = 'THIRD_PARTY'
        AND n.app_scopes IS NOT NULL
    RETURN count(n) AS count
    """,
    asset_label="ZoomApp",
    asset_id_field="asset_id",
    identity_fields=("asset_id", "issue"),
    module=Module.ZOOM,
    maturity=Maturity.EXPERIMENTAL,
)


_stale_licensed_users = Fact(
    id="zoom_stale_licensed_users",
    name="Active licensed users without a recent reported sign-in",
    description=(
        "Active licensed users whose known last sign-in is older than 90 days. "
        "Missing timestamps are unknown, not evidence of inactivity. Zoom reports "
        "this field with a three-day buffer."
    ),
    cypher_query="""
    MATCH (n:ZoomUser)
    WHERE n.status = 'active' AND n.type = 2
        AND n.last_login_time < datetime() - duration('P90D')
    RETURN coalesce(n.display_name, n.email, n.id) AS asset_name,
        n.id AS asset_id, n.account_id AS account_id,
        'stale_licensed_users' AS issue,
        toString(n.last_login_time) AS current_value
    """,
    cypher_visual_query="""
    MATCH (n:ZoomUser)
    WHERE n.status = 'active' AND n.type = 2
        AND n.last_login_time < datetime() - duration('P90D')
    RETURN n
    """,
    cypher_count_query="""
    MATCH (n:ZoomUser)
    WHERE n.status = 'active' AND n.type = 2 AND n.last_login_time IS NOT NULL
    RETURN count(n) AS count
    """,
    asset_label="ZoomUser",
    asset_id_field="asset_id",
    identity_fields=("asset_id", "issue"),
    module=Module.ZOOM,
    maturity=Maturity.EXPERIMENTAL,
)

zoom_security_review = Rule(
    id="zoom_security_review",
    name="Zoom Security Review",
    description=(
        "Reviews observed Zoom configuration, administrative access and stale licensed "
        "accounts. Missing fields are unknown. Findings reflect the last successfully "
        "collected snapshot, not live reachability or effective policy inheritance."
    ),
    output_model=ZoomSecurityReviewOutput,
    facts=(
        _meeting_admission_controls,
        _recording_viewer_controls,
        _account_meeting_defaults,
        _native_signin_two_factor_policy,
        _unrestricted_edit_roles,
        _third_party_admin_write_scopes,
        _stale_licensed_users,
    ),
    tags=("zoom", "identity", "data", "attack_surface"),
    version="0.1.0",
    references=[
        RuleReference(
            text="Zoom REST API reference",
            url="https://developers.zoom.us/docs/api/",
        ),
    ],
)
