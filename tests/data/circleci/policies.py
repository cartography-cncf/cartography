# Raw shape of GET /owner/{orgID}/context/config/policy-bundle (map of name->policy)
# and GET .../decision/settings.
CIRCLECI_POLICY_BUNDLE = {
    "require_security_scan": [
        {
            "name": "require_security_scan",
            "content": "package org\npolicy_name['require_security_scan']\n",
            "created_at": "2021-09-07T10:00:00Z",
            "created_by": "alice",
        },
    ],
    "block_unapproved_orbs": [
        {
            "name": "block_unapproved_orbs",
            "content": "package org\npolicy_name['block_unapproved_orbs']\n",
            "created_at": "2021-09-07T11:00:00Z",
            "created_by": "bob",
        },
    ],
}

CIRCLECI_DECISION_SETTINGS = {"enabled": True}
