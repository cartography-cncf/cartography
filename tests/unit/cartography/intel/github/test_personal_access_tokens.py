import json
from datetime import datetime

from cartography.intel.github.personal_access_tokens import (
    _transform_fine_grained_token,
)
from cartography.intel.github.personal_access_tokens import (
    _transform_saml_credential_authorization,
)
from tests.data.github.personal_access_tokens import FINE_GRAINED_PERSONAL_ACCESS_TOKENS
from tests.data.github.personal_access_tokens import SAML_CREDENTIAL_AUTHORIZATIONS

ORG_URL = "https://github.com/simpsoncorp"


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_transform_fine_grained_pat_serializes_metadata_without_token_values():
    result = _transform_fine_grained_token(
        FINE_GRAINED_PERSONAL_ACCESS_TOKENS[0],
        ORG_URL,
        ["https://github.com/simpsoncorp/sample_repo"],
    )

    assert result == {
        "id": "https://github.com/simpsoncorp/personal-access-tokens/25381",
        "token_kind": "fine_grained",
        "token_id": 98716,
        "token_name": "cartography-readonly",
        "owner_login": "hjsimpson",
        "owner_user_id": "https://github.com/hjsimpson",
        "repository_selection": "selected",
        "permissions": json.dumps(
            {
                "organization": {"members": "read"},
                "repository": {"contents": "read", "metadata": "read"},
            },
            sort_keys=True,
        ),
        "scopes": None,
        "access_granted_at": _dt("2025-01-16T08:47:09.000-07:00"),
        "credential_authorized_at": None,
        "credential_accessed_at": None,
        "expires_at": _dt("2025-04-16T08:47:09.000-07:00"),
        "last_used_at": _dt("2025-02-16T08:47:09.000-07:00"),
        "repository_urls": ["https://github.com/simpsoncorp/sample_repo"],
    }


def test_transform_classic_pat_drops_token_fragment():
    result = _transform_saml_credential_authorization(
        SAML_CREDENTIAL_AUTHORIZATIONS[0],
        ORG_URL,
    )

    assert result == {
        "id": "https://github.com/simpsoncorp/credential-authorizations/161195",
        "token_kind": "classic",
        "token_id": None,
        "token_name": None,
        "owner_login": "hjsimpson",
        "owner_user_id": "https://github.com/hjsimpson",
        "repository_selection": None,
        "permissions": None,
        "scopes": ["read:org", "repo"],
        "access_granted_at": None,
        "credential_authorized_at": _dt("2024-01-26T19:06:43Z"),
        "credential_accessed_at": _dt("2024-02-26T19:06:43Z"),
        "expires_at": _dt("2024-04-26T19:06:43Z"),
        "last_used_at": None,
        "repository_urls": [],
    }
    assert "token_last_eight" not in result


def test_transform_saml_credential_ignores_ssh_keys():
    result = _transform_saml_credential_authorization(
        SAML_CREDENTIAL_AUTHORIZATIONS[1],
        ORG_URL,
    )

    assert result is None


def test_transform_pat_without_owner_or_id_handles_optional_data():
    assert (
        _transform_fine_grained_token({"token_name": "missing-id"}, ORG_URL, []) is None
    )

    result = _transform_saml_credential_authorization(
        {
            "credential_id": 123,
            "credential_type": "personal access token",
            "scopes": None,
        },
        ORG_URL,
    )

    assert result is not None
    assert result["owner_login"] is None
    assert result["owner_user_id"] is None
    assert result["scopes"] == []
