from cartography.intel.okta.factors import transform_okta_user_factor
from tests.data.okta.userfactors import create_test_factor


def test_factor_transform_with_all_values():
    factor = create_test_factor()

    result = transform_okta_user_factor(factor)

    expected = {
        "id": factor.id,
        "factor_type": factor.factorType,
        "provider": factor.provider,
        "status": factor.status,
        "created": "01/01/2019, 00:00:01",
        "okta_last_updated": "01/01/2019, 00:00:01",
    }

    assert result == expected


def test_factor_transform_with_created_none():
    factor = create_test_factor()
    factor.created = None

    result = transform_okta_user_factor(factor)

    expected = {
        "id": factor.id,
        "factor_type": factor.factorType,
        "provider": factor.provider,
        "status": factor.status,
        "created": None,
        "okta_last_updated": "01/01/2019, 00:00:01",
    }

    assert result == expected


def test_factor_transform_with_lastupdated_none():
    factor = create_test_factor()
    factor.lastUpdated = None

    result = transform_okta_user_factor(factor)

    expected = {
        "id": factor.id,
        "factor_type": factor.factorType,
        "provider": factor.provider,
        "status": factor.status,
        "created": "01/01/2019, 00:00:01",
        "okta_last_updated": None,
    }

    assert result == expected
