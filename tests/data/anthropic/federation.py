ANTHROPIC_FEDERATION_ISSUERS = [
    {
        "id": "fdis_01Ab2Cd3Ef4Gh5Ij6Kl7Mn8Op",
        "type": "federation_issuer",
        "name": "github-actions",
        "issuer_url": "https://token.actions.githubusercontent.com",
        "check_jti": True,
        "max_jwt_lifetime_seconds": 900,
        "jwks": {"type": "discovery"},
        "jwks_polling_disabled_at": None,
        "poll_status": {
            "consecutive_failures": 0,
            "last_fetched_at": "2025-02-01T10:00:00.000000Z",
            "next_poll_at": "2025-02-01T10:05:00.000000Z",
        },
        "created_at": "2025-01-20T08:00:00.000000Z",
        "updated_at": "2025-01-20T08:00:00.000000Z",
        "archived_at": None,
        "created_by_actor_id": "user_EneequohSheesh3Ohtaefu8we2aite",
    },
    {
        "id": "fdis_01Zy9Xw8Vu7Ts6Rq5Po4Nm3Lk",
        "type": "federation_issuer",
        "name": "springfield-k8s",
        "issuer_url": "https://kubernetes.springfield.corp",
        "check_jti": False,
        "max_jwt_lifetime_seconds": 3600,
        "jwks": {
            "type": "explicit_url",
            "url": "https://kubernetes.springfield.corp/openid/v1/jwks",
        },
        "jwks_polling_disabled_at": "2025-03-02T11:00:00.000000Z",
        "poll_status": {
            "consecutive_failures": 3,
            "last_fetched_at": "2025-03-02T10:00:00.000000Z",
            "next_poll_at": None,
        },
        "created_at": "2025-01-22T08:00:00.000000Z",
        "updated_at": "2025-03-02T11:00:00.000000Z",
        "archived_at": None,
        "created_by_actor_id": "user_EneequohSheesh3Ohtaefu8we2aite",
    },
]

ANTHROPIC_FEDERATION_RULES = [
    {
        "id": "fdrl_01Qw2Er3Ty4Ui5Op6As7Df8Gh",
        "type": "federation_rule",
        "name": "cartography-collector",
        "description": "Lets the cartography collector read the whole organization.",
        "issuer_id": "fdis_01Zy9Xw8Vu7Ts6Rq5Po4Nm3Lk",
        "issuer_name": "springfield-k8s",
        "match": {
            "subject_prefix": "system:serviceaccount:security:cartography",
            "audience": "https://api.anthropic.com",
            "claims": {"namespace": "security"},
            "condition": None,
        },
        "target": {
            "type": "service_account",
            "service_account_id": "svac_01Pq8WeRtYuIoPaSdFgHjKlM",
            "service_account_name": "cartography-collector",
        },
        "oauth_scope": "org:admin",
        "token_lifetime_seconds": 3600,
        "attributes": None,
        "applies_to_all_workspaces": False,
        "workspace_id": None,
        "workspace_ids": [],
        "created_at": "2025-02-01T10:30:00.000000Z",
        "updated_at": "2025-02-01T10:30:00.000000Z",
        "archived_at": None,
    },
    {
        "id": "fdrl_01Hj2Kl3Zx4Cv5Bn6Mq7Wt8Ry",
        "type": "federation_rule",
        "name": "ci-inference",
        "description": "Wildcard prefix: also matches fork pull request runs.",
        "issuer_id": "fdis_01Ab2Cd3Ef4Gh5Ij6Kl7Mn8Op",
        "issuer_name": "github-actions",
        "match": {
            "subject_prefix": "repo:springfield/reactor-control:*",
            "audience": None,
            "claims": {},
            "condition": None,
        },
        "target": {
            "type": "service_account",
            "service_account_id": "svac_01Nb5RtYuIoPaSdFgHjKlZxC",
            "service_account_name": "reactor-telemetry",
        },
        "oauth_scope": "workspace:developer",
        "token_lifetime_seconds": 900,
        "attributes": None,
        "applies_to_all_workspaces": True,
        "workspace_id": None,
        "workspace_ids": [],
        "created_at": "2025-02-03T14:00:00.000000Z",
        "updated_at": "2025-02-03T14:00:00.000000Z",
        "archived_at": None,
    },
]

# Keyed by federation rule id, as returned by
# GET /organizations/federation_rules/{id}/workspaces
ANTHROPIC_FEDERATION_RULE_WORKSPACES = {
    "fdrl_01Qw2Er3Ty4Ui5Op6As7Df8Gh": [],
    "fdrl_01Hj2Kl3Zx4Cv5Bn6Mq7Wt8Ry": [
        {
            "type": "federation_rule_workspace",
            "federation_rule_id": "fdrl_01Hj2Kl3Zx4Cv5Bn6Mq7Wt8Ry",
            "workspace_id": "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ",
            "workspace_name": "Springfield Nuclear Power Plant",
            "created_at": "2025-02-03T14:00:00.000000Z",
            "created_by_actor_id": "user_EneequohSheesh3Ohtaefu8we2aite",
        },
    ],
}
