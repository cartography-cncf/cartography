from cartography.intel.okta.api_tokens import _transform_okta_api_tokens
from tests.data.okta.api_tokens import API_TOKENS


def test_transform_okta_api_tokens() -> None:
    # Act
    tokens = {token["id"]: token for token in _transform_okta_api_tokens(API_TOKENS)}

    # Assert
    assert tokens["00T-zone-restricted"] == {
        "id": "00T-zone-restricted",
        "name": "SIEM integration",
        "client_name": "Okta API",
        "user_id": "00u-svc-siem",
        "token_window": "P30D",
        "created": "2026-01-01T00:00:00.000Z",
        "expires_at": "2026-10-30T00:00:00.000Z",
        "okta_last_updated": "2026-01-01T00:00:00.000Z",
        "network_connection": "ZONE",
        "network_include_zone_ids": ["nzo-corp"],
        "network_exclude_zone_ids": ["nzo-tor"],
    }
    assert tokens["00T-anywhere"]["network_connection"] == "ANYWHERE"
    assert tokens["00T-anywhere"]["network_include_zone_ids"] == []
    assert tokens["00T-no-network"]["network_connection"] is None
