import json

from okta.models.trusted_origin import TrustedOrigin

from cartography.intel.okta import origins
from tests.data.okta.trustedorigin import LIST_TRUSTED_ORIGIN_RESPONSE
from tests.data.okta.trustedorigin import TRUSTED_ORIGIN_WITH_SPARSE_SCOPES
from tests.data.okta.trustedorigin import TRUSTED_ORIGIN_WITHOUT_SCOPES


def test_transform_handles_scopes_without_allowed_apps() -> None:
    """
    CORS and REDIRECT scopes come back without allowedOktaApps, which the SDK
    models as None. That must not abort the sync.
    """
    # Arrange
    okta_origins = [
        TrustedOrigin.from_dict(item)
        for item in json.loads(LIST_TRUSTED_ORIGIN_RESPONSE)
    ]

    # Act
    result = origins._transform_okta_origins(okta_origins)

    # Assert
    assert result[0]["cors_allowed"] is True
    assert result[0]["cors_allowed_okta_apps"] == []
    assert result[1]["redirect_allowed"] is True
    assert result[1]["redirect_allowed_okta_apps"] == []


def test_transform_handles_sparse_and_missing_scopes() -> None:
    """
    An IFRAME_EMBED scope carries allowed apps, a scope can be missing its type,
    and the scope list itself is optional.
    """
    # Arrange
    okta_origins = [
        TrustedOrigin.from_dict(json.loads(TRUSTED_ORIGIN_WITH_SPARSE_SCOPES)),
        TrustedOrigin.from_dict(json.loads(TRUSTED_ORIGIN_WITHOUT_SCOPES)),
    ]

    # Act
    result = origins._transform_okta_origins(okta_origins)

    # Assert
    assert result[0]["iframe_allowed"] is True
    assert result[0]["iframe_allowed_okta_apps"] == ["OKTA_ENDUSER"]
    assert result[1]["id"] == "tos1noscopes0000g6"
    assert "iframe_allowed" not in result[1]
