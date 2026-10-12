from typing import Any

# Synthetic raw API payloads for GET /api/v1/policies?type=...,
# GET /api/v1/policies/{id}/rules and GET /api/v1/policies/{id}/mappings.

TS = "2026-01-01T00:00:00.000Z"

GLOBAL_SESSION_POLICY: dict[str, Any] = {
    "id": "00p-global-session",
    "type": "OKTA_SIGN_ON",
    "name": "Default Policy",
    "description": "The default global session policy",
    "status": "ACTIVE",
    "priority": 1,
    "system": True,
    "created": TS,
    "lastUpdated": TS,
    "conditions": {"people": {"groups": {"include": ["00g-everyone"]}}},
    "_links": {},
}

PASSWORD_POLICY_STRONG: dict[str, Any] = {
    "id": "00p-password-default",
    "type": "PASSWORD",
    "name": "Default Policy",
    "status": "ACTIVE",
    "priority": 2,
    "system": True,
    "created": TS,
    "lastUpdated": TS,
    "conditions": {
        "people": {"groups": {"include": ["00g-everyone"]}},
        "authProvider": {"provider": "OKTA"},
    },
    "settings": {
        "password": {
            "complexity": {
                "minLength": 15,
                "minLowerCase": 1,
                "minUpperCase": 1,
                "minNumber": 1,
                "minSymbol": 1,
                "excludeUsername": True,
                "excludeAttributes": ["firstName", "lastName"],
                "dictionary": {"common": {"exclude": True}},
            },
            "age": {
                "maxAgeDays": 60,
                "expireWarnDays": 7,
                "minAgeMinutes": 1440,
                "historyCount": 5,
            },
            "lockout": {
                "maxAttempts": 3,
                "autoUnlockMinutes": 15,
                "showLockoutFailures": False,
                "userLockoutNotificationChannels": ["EMAIL"],
            },
        },
        "recovery": {"factors": {"okta_email": {"status": "ACTIVE"}}},
        "delegation": {"options": {"skipUnlock": False}},
    },
}

PASSWORD_POLICY_WEAK: dict[str, Any] = {
    "id": "00p-password-legacy",
    "type": "PASSWORD",
    "name": "Legacy Contractors",
    "status": "ACTIVE",
    "priority": 1,
    "system": False,
    "created": TS,
    "lastUpdated": TS,
    "conditions": {
        "people": {
            "groups": {"include": ["00g-contractors"], "exclude": ["00g-admins"]},
        },
        "authProvider": {"provider": "OKTA"},
    },
    "settings": {
        "password": {
            "complexity": {
                "minLength": 8,
                "minLowerCase": 1,
                "minUpperCase": 0,
                "minNumber": 1,
                "minSymbol": 0,
                "excludeUsername": False,
                "excludeAttributes": [],
            },
            "age": {
                "maxAgeDays": 0,
                "expireWarnDays": 0,
                "minAgeMinutes": 0,
                "historyCount": 0,
            },
            "lockout": {"maxAttempts": 10},
        },
    },
}

AUTHENTICATOR_ENROLLMENT_POLICY: dict[str, Any] = {
    "id": "00p-enrollment",
    "type": "MFA_ENROLL",
    "name": "Default Policy",
    "status": "ACTIVE",
    "priority": 1,
    "system": True,
    "created": TS,
    "lastUpdated": TS,
    "conditions": {"people": {"groups": {"include": ["00g-everyone"]}}},
    "settings": {
        "type": "AUTHENTICATORS",
        "authenticators": [
            {"key": "okta_verify", "enroll": {"self": "REQUIRED"}},
            {"key": "webauthn", "enroll": {"self": "OPTIONAL"}},
            {"key": "phone_number", "enroll": {"self": "NOT_ALLOWED"}},
        ],
    },
}

ADMIN_CONSOLE_POLICY: dict[str, Any] = {
    "id": "rst-admin-console",
    "type": "ACCESS_POLICY",
    "name": "Okta Admin Console",
    "status": "ACTIVE",
    "priority": 1,
    "system": False,
    "created": TS,
    "lastUpdated": TS,
    "conditions": None,
}

DASHBOARD_POLICY: dict[str, Any] = {
    "id": "rst-dashboard",
    "type": "ACCESS_POLICY",
    "name": "Okta Dashboard",
    "status": "ACTIVE",
    "priority": 1,
    "system": False,
    "created": TS,
    "lastUpdated": TS,
    "conditions": None,
}

DEFAULT_ACCESS_POLICY: dict[str, Any] = {
    "id": "rst-default",
    "type": "ACCESS_POLICY",
    "name": "Default Policy",
    "status": "ACTIVE",
    "priority": 1,
    "system": True,
    "created": TS,
    "lastUpdated": TS,
    "conditions": None,
}

PROFILE_ENROLLMENT_POLICY: dict[str, Any] = {
    "id": "rst-profile-enrollment",
    "type": "PROFILE_ENROLLMENT",
    "name": "Default Policy",
    "status": "ACTIVE",
    "priority": 1,
    "system": True,
    "created": TS,
    "lastUpdated": TS,
    "conditions": None,
}

POLICIES_BY_TYPE: dict[str, list[dict[str, Any]]] = {
    "OKTA_SIGN_ON": [GLOBAL_SESSION_POLICY],
    "PASSWORD": [PASSWORD_POLICY_WEAK, PASSWORD_POLICY_STRONG],
    "MFA_ENROLL": [AUTHENTICATOR_ENROLLMENT_POLICY],
    "ACCESS_POLICY": [ADMIN_CONSOLE_POLICY, DASHBOARD_POLICY, DEFAULT_ACCESS_POLICY],
    "PROFILE_ENROLLMENT": [PROFILE_ENROLLMENT_POLICY],
}

RULES_BY_POLICY: dict[str, list[dict[str, Any]]] = {
    "00p-global-session": [
        {
            "id": "0pr-session-hardened",
            "type": "SIGN_ON",
            "name": "Hardened session",
            "status": "ACTIVE",
            "priority": 1,
            "system": False,
            "created": TS,
            "lastUpdated": TS,
            "conditions": {
                "people": {"users": {"exclude": ["00u-breakglass"]}},
                "network": {"connection": "ZONE", "include": ["nzo-corp"]},
                "authContext": {"authType": "ANY"},
                "riskScore": {"level": "ANY"},
            },
            "actions": {
                "signon": {
                    "access": "ALLOW",
                    "requireFactor": True,
                    "factorPromptMode": "ALWAYS",
                    "factorLifetime": 15,
                    "primaryFactor": "PASSWORD_IDP_ANY_FACTOR",
                    "rememberDeviceByDefault": False,
                    "session": {
                        "usePersistentCookie": False,
                        "maxSessionIdleMinutes": 15,
                        "maxSessionLifetimeMinutes": 1080,
                    },
                },
            },
        },
        {
            "id": "0pr-session-default",
            "type": "SIGN_ON",
            "name": "Default Rule",
            "status": "ACTIVE",
            "priority": 2,
            "system": True,
            "created": TS,
            "lastUpdated": TS,
            "conditions": {
                "people": {"users": {"exclude": []}},
                "network": {"connection": "ANYWHERE"},
            },
            "actions": {
                "signon": {
                    "access": "ALLOW",
                    "requireFactor": False,
                    "primaryFactor": "PASSWORD_IDP",
                    "rememberDeviceByDefault": False,
                    "session": {
                        "usePersistentCookie": True,
                        "maxSessionIdleMinutes": 120,
                        "maxSessionLifetimeMinutes": 0,
                    },
                },
            },
        },
    ],
    "00p-password-default": [
        {
            "id": "0pr-password-default",
            "type": "PASSWORD",
            "name": "Default Rule",
            "status": "ACTIVE",
            "priority": 1,
            "system": True,
            "created": TS,
            "lastUpdated": TS,
            "conditions": {
                "people": {"users": {"exclude": []}},
                "network": {"connection": "ANYWHERE"},
            },
            "actions": {
                "passwordChange": {"access": "ALLOW"},
                "selfServicePasswordReset": {"access": "ALLOW"},
                "selfServiceUnlock": {"access": "DENY"},
            },
        },
    ],
    "00p-password-legacy": [],
    "00p-enrollment": [
        {
            "id": "0pr-enrollment-default",
            "type": "MFA_ENROLL",
            "name": "Default Rule",
            "status": "ACTIVE",
            "priority": 1,
            "system": True,
            "created": TS,
            "lastUpdated": TS,
            "conditions": {
                "people": {"users": {"exclude": []}},
                "network": {"connection": "ANYWHERE"},
            },
            "actions": {"enroll": {"self": "CHALLENGE"}},
        },
    ],
    "rst-admin-console": [
        {
            "id": "rul-admin-phishing-resistant",
            "type": "ACCESS_POLICY",
            "name": "Admins require phishing-resistant MFA",
            "status": "ACTIVE",
            "priority": 0,
            "system": False,
            "created": TS,
            "lastUpdated": TS,
            "conditions": {
                "people": {"groups": {"include": ["00g-admins"]}},
                "network": {"connection": "ZONE", "exclude": ["nzo-blocklist"]},
                "riskScore": {"level": "ANY"},
                # A platform value newer than the SDK enum must not break the sync.
                "platform": {"include": [{"type": "DESKTOP", "os": {"type": "MACOS"}}]},
            },
            "actions": {
                "appSignOn": {
                    "access": "ALLOW",
                    "verificationMethod": {
                        "type": "ASSURANCE",
                        "factorMode": "2FA",
                        "reauthenticateIn": "PT2H",
                        "constraints": [
                            {
                                "possession": {
                                    "phishingResistant": "REQUIRED",
                                    "hardwareProtection": "REQUIRED",
                                    "deviceBound": "REQUIRED",
                                },
                                "knowledge": {"types": ["password"]},
                            },
                        ],
                    },
                },
            },
        },
        {
            "id": "rul-admin-catch-all",
            "type": "ACCESS_POLICY",
            "name": "Catch-all Rule",
            "status": "ACTIVE",
            "priority": 99,
            "system": True,
            "created": TS,
            "lastUpdated": TS,
            "conditions": None,
            "actions": {
                "appSignOn": {
                    "access": "DENY",
                    "verificationMethod": {
                        "type": "ASSURANCE",
                        "factorMode": "1FA",
                        "reauthenticateIn": "PT2H",
                        "constraints": [],
                    },
                },
            },
        },
    ],
    "rst-dashboard": [
        {
            "id": "rul-dashboard-one-factor",
            "type": "ACCESS_POLICY",
            "name": "Everyone",
            "status": "ACTIVE",
            "priority": 0,
            "system": False,
            "created": TS,
            "lastUpdated": TS,
            "conditions": {"people": {"groups": {"include": ["00g-everyone"]}}},
            "actions": {
                "appSignOn": {
                    "access": "ALLOW",
                    "verificationMethod": {
                        "type": "ASSURANCE",
                        "factorMode": "1FA",
                        "reauthenticateIn": "PT12H",
                        "constraints": [
                            {"possession": {"phishingResistant": "OPTIONAL"}},
                        ],
                    },
                },
            },
        },
    ],
    "rst-default": [
        {
            "id": "rul-default-mixed",
            "type": "ACCESS_POLICY",
            "name": "Two factors, any possession",
            "status": "ACTIVE",
            "priority": 0,
            "system": False,
            "created": TS,
            "lastUpdated": TS,
            "conditions": {"network": {"connection": "ANYWHERE"}},
            "actions": {
                "appSignOn": {
                    "access": "ALLOW",
                    "verificationMethod": {
                        "type": "ASSURANCE",
                        "factorMode": "2FA",
                        "reauthenticateIn": "PT8H",
                        "constraints": [
                            {"possession": {"phishingResistant": "REQUIRED"}},
                            {"knowledge": {"types": ["password"]}},
                        ],
                    },
                },
            },
        },
    ],
    "rst-profile-enrollment": [
        {
            "id": "rul-profile-enrollment",
            "type": "PROFILE_ENROLLMENT",
            "name": "Catch-all Rule",
            "status": "ACTIVE",
            "priority": 99,
            "system": True,
            "created": TS,
            "lastUpdated": TS,
            "conditions": None,
            "actions": {
                "profileEnrollment": {
                    "access": "DENY",
                    "unknownUserAction": "DENY",
                    "activationRequirements": {"emailVerification": True},
                },
            },
        },
    ],
}


def _mapping(app_id: str, policy_id: str) -> dict[str, Any]:
    return {
        "id": f"map-{app_id}",
        "_links": {
            "application": {"href": f"https://example.okta.com/api/v1/apps/{app_id}"},
            "policy": {
                "href": f"https://example.okta.com/api/v1/policies/{policy_id}",
            },
        },
    }


MAPPINGS_BY_POLICY: dict[str, list[dict[str, Any]]] = {
    "rst-admin-console": [_mapping("0oa-admin-console", "rst-admin-console")],
    "rst-dashboard": [_mapping("0oa-dashboard", "rst-dashboard")],
    "rst-default": [
        _mapping("0oa-slack", "rst-default"),
        _mapping("0oa-github", "rst-default"),
    ],
}

# GET /api/v1/apps/{id} for first-party apps the Applications API does not list.
FIRST_PARTY_APPS: dict[str, dict[str, Any]] = {
    "0oa-admin-console": {
        "id": "0oa-admin-console",
        "name": "saasure",
        "label": "Okta Admin Console",
    },
    "0oa-dashboard": {
        "id": "0oa-dashboard",
        "name": "okta_enduser",
        "label": "Okta Dashboard",
    },
}
