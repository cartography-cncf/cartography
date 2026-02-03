from unittest.mock import MagicMock

from okta.models.user_factor import UserFactor


def create_test_factor():
    """Create a mock UserFactor object for testing."""
    factor = MagicMock(spec=UserFactor)

    factor.id = "factor_id_value"
    factor.factor_type = "factor_type_value"
    factor.provider = "factor_provider_value"
    factor.status = "factor_status_value"
    factor.created = None
    factor.last_updated = None

    return factor
