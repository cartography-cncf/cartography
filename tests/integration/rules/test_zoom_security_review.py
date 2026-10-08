from datetime import datetime
from datetime import timezone

import pytest

from cartography.client.core.tx import load
from cartography.models.zoom.app import ZoomAppSchema
from cartography.models.zoom.meeting import ZoomMeetingSchema
from cartography.models.zoom.privilege import ZoomRolePrivilegeSchema
from cartography.models.zoom.recording import ZoomRecordingSchema
from cartography.models.zoom.role import ZoomRoleSchema
from cartography.models.zoom.settings import ZoomSecuritySettingsSchema
from cartography.models.zoom.user import ZoomUserSchema
from cartography.rules.data.rules.zoom_security_review import zoom_security_review


def _assert_fact(neo4j_session, issue, expected_count):
    fact = next(f for f in zoom_security_review.facts if f.id == f"zoom_{issue}")
    rows = neo4j_session.run(fact.cypher_query).data()
    visual = neo4j_session.run(fact.cypher_visual_query).data()
    count = neo4j_session.run(fact.cypher_count_query).single()["count"]
    assert {row["asset_id"] for row in rows} == {"a:positive", "b:positive"}
    assert len(rows) == 2
    assert {row["n"]["id"] for row in visual} == {"a:positive", "b:positive"}
    assert len(visual) == 2
    assert count == expected_count
    for row in rows:
        finding = zoom_security_review.output_model(**row)
        assert finding.asset_name
        assert finding.account_id in {"a", "b"}
        assert finding.issue == issue
        assert finding.current_value


@pytest.mark.parametrize(
    "issue,schema,positive,negatives,expected_count",
    [
        (
            "meeting_admission_controls",
            ZoomMeetingSchema(),
            {
                "password_protected": False,
                "waiting_room": False,
                "meeting_authentication": False,
                "approval_type": 2,
            },
            [
                {"password_protected": True},
                {"waiting_room": True},
                {"meeting_authentication": True},
                {"password_protected": None},
                {"approval_type": 0},
                {"approval_type": 1},
                {"approval_type": None},
            ],
            7,
        ),
        (
            "recording_viewer_controls",
            ZoomRecordingSchema(),
            {
                "share_recording": "publicly",
                "password_protected": False,
                "recording_authentication": False,
                "on_demand": False,
            },
            [
                {"share_recording": "internally"},
                {"password_protected": True},
                {"recording_authentication": True},
                {"on_demand": True},
                {"on_demand": None},
            ],
            6,
        ),
        (
            "account_meeting_defaults",
            ZoomSecuritySettingsSchema(),
            {
                "scope_type": "account",
                "kind": "configured",
                "meeting_passcode_required": False,
                "waiting_room": False,
                "meeting_authentication": False,
                "auto_security": False,
            },
            [
                {"scope_type": "user"},
                {"kind": "locked"},
                {"meeting_passcode_required": True},
                {"waiting_room": True},
                {"meeting_authentication": True},
                {"auto_security": True},
                {"auto_security": None},
            ],
            6,
        ),
        (
            "account_pmi_defaults",
            ZoomSecuritySettingsSchema(),
            {
                "scope_type": "account",
                "kind": "configured",
                "pmi_passcode_required": False,
                "waiting_room": False,
                "meeting_authentication": False,
            },
            [
                {"scope_type": "user"},
                {"kind": "locked"},
                {"pmi_passcode_required": True},
                {"waiting_room": True},
                {"meeting_authentication": True},
                {"pmi_passcode_required": None},
            ],
            5,
        ),
        (
            "native_signin_two_factor_policy",
            ZoomSecuritySettingsSchema(),
            {
                "scope_type": "account",
                "kind": "configured",
                "sign_in_with_work_email": True,
                "sign_in_with_two_factor_auth": "none",
                "require_sso_for_domains": False,
            },
            [
                {"scope_type": "group"},
                {"kind": "locked"},
                {"sign_in_with_work_email": False},
                {"sign_in_with_two_factor_auth": "all"},
                {"sign_in_with_two_factor_auth": "group"},
                {"sign_in_with_two_factor_auth": "role"},
                {"require_sso_for_domains": True},
                {"require_sso_for_domains": None},
            ],
            7,
        ),
        (
            "third_party_admin_write_scopes",
            ZoomAppSchema(),
            {
                "installed": True,
                "developer_type": "THIRD_PARTY",
                "app_scopes": [
                    "user:write:admin",
                    "role:update:role:admin",
                    "meeting:delete:meeting:master",
                ],
                "name": "Synthetic app",
            },
            [
                {"installed": False, "approved": True},
                {"developer_type": "INTERNAL"},
                {"app_scopes": ["user:read:user:admin"]},
                {"app_scopes": ["meeting:write"]},
                {"app_scopes": ["user:write:user"]},
                {"app_scopes": []},
                {"app_scopes": None},
            ],
            6,
        ),
        (
            "stale_licensed_users",
            ZoomUserSchema(),
            {
                "status": "active",
                "type": 2,
                "last_login_time": datetime(2000, 1, 1, tzinfo=timezone.utc),
            },
            [
                {"status": "inactive"},
                {"status": "pending"},
                {"type": 1},
                {"last_login_time": datetime(2999, 1, 1, tzinfo=timezone.utc)},
                {"last_login_time": None},
            ],
            3,
        ),
    ],
)
def test_zoom_facts_skip_protected_and_unknown_snapshots(
    neo4j_session, issue, schema, positive, negatives, expected_count
):
    # Arrange: use actual schemas so labels, stored types and property names agree.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    for account in ("a", "b"):
        records = [{**positive, "id": f"{account}:positive"}]
        if account == "a":
            records.extend(
                {**positive, **override, "id": f"a:negative:{i}"}
                for i, override in enumerate(negatives)
            )
        load(
            neo4j_session,
            schema,
            records,
            ACCOUNT_ID=account,
            lastupdated=1,
        )

    # Act and assert: finding, count and visual queries agree on the same assets.
    _assert_fact(neo4j_session, issue, expected_count)


def test_zoom_stale_privileged_users_fact_needs_dormancy_and_an_unrestricted_edit_role(
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    stale = datetime(2000, 1, 1, tzinfo=timezone.utc)
    fresh = datetime(2999, 1, 1, tzinfo=timezone.utc)
    for account in ("a", "b"):
        users = [
            {
                "id": f"{account}:positive",
                "display_name": "Synthetic administrator",
                "status": "active",
                "last_login_time": stale,
            }
        ]
        admins = [f"{account}:positive"]
        roles = []
        privileges = [
            {
                "id": f"{account}:admin:{i}",
                "role_node_id": f"{account}:admin",
                "privilege": privilege,
                "restricted_to_groups": False,
            }
            for i, privilege in enumerate(("User:Edit", "AccountSetting:Edit"))
        ]
        if account == "a":
            # Same privileged role, but not dormant, unknown, or not active.
            users += [
                {"id": "a:fresh", "status": "active", "last_login_time": fresh},
                {"id": "a:unknown", "status": "active", "last_login_time": None},
                {"id": "a:inactive", "status": "inactive", "last_login_time": stale},
            ]
            admins += ["a:fresh", "a:unknown", "a:inactive"]
            # Dormant users whose role has no unrestricted edit privilege.
            for name, privilege, restricted in (
                ("reader", "User:Read", False),
                ("scoped", "User:Edit", True),
                ("undetermined", "User:Edit", None),
            ):
                users.append(
                    {"id": f"a:{name}", "status": "active", "last_login_time": stale}
                )
                roles.append(
                    {
                        "id": f"a:{name}-role",
                        "name": name,
                        "member_ids": [f"a:{name}"],
                    }
                )
                privileges.append(
                    {
                        "id": f"a:{name}-role:privilege",
                        "role_node_id": f"a:{name}-role",
                        "privilege": privilege,
                        "restricted_to_groups": restricted,
                    }
                )
            users.append(
                {"id": "a:no-role", "status": "active", "last_login_time": stale}
            )
        roles.append(
            {
                "id": f"{account}:admin",
                "name": "Synthetic role",
                "member_ids": admins,
            }
        )
        load(neo4j_session, ZoomUserSchema(), users, ACCOUNT_ID=account, lastupdated=1)
        load(neo4j_session, ZoomRoleSchema(), roles, ACCOUNT_ID=account, lastupdated=1)
        load(
            neo4j_session,
            ZoomRolePrivilegeSchema(),
            privileges,
            ACCOUNT_ID=account,
            lastupdated=1,
        )

    # Act and assert: the evaluated population is active users with a known sign-in
    # time and an unrestricted edit role (two positives and the non-dormant user).
    _assert_fact(neo4j_session, "stale_privileged_users", 3)
    fact = next(
        f for f in zoom_security_review.facts if f.id == "zoom_stale_privileged_users"
    )
    values = {
        row["current_value"] for row in neo4j_session.run(fact.cypher_query).data()
    }
    assert all(
        value.startswith("Synthetic role, last sign-in 2000-01-01") for value in values
    )


def test_zoom_app_fact_lists_every_matching_scope(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    many = [f"user:write:{i}:admin" for i in range(7)]
    apps = [
        {
            "id": "a:many",
            "name": "Many scopes",
            "installed": True,
            "developer_type": "THIRD_PARTY",
            "app_scopes": [*many, "user:read:admin"],
        },
        {
            "id": "a:few",
            "name": "Few scopes",
            "installed": True,
            "developer_type": "THIRD_PARTY",
            "app_scopes": [
                "user:read:admin",
                "role:update:role:admin",
                "meeting:delete:meeting:master",
            ],
        },
    ]
    load(neo4j_session, ZoomAppSchema(), apps, ACCOUNT_ID="a", lastupdated=1)
    fact = next(
        f
        for f in zoom_security_review.facts
        if f.id == "zoom_third_party_admin_write_scopes"
    )

    # Act
    rows = neo4j_session.run(fact.cypher_query).data()

    # Assert: the count is exact, and long lists are shortened after five scopes.
    values = {row["asset_id"]: row["current_value"] for row in rows}
    assert values == {
        "a:many": (
            "7 administrative write scopes: user:write:0:admin, user:write:1:admin, "
            "user:write:2:admin, user:write:3:admin, user:write:4:admin, ..."
        ),
        "a:few": (
            "2 administrative write scopes: role:update:role:admin, "
            "meeting:delete:meeting:master"
        ),
    }
