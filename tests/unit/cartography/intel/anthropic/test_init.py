from unittest.mock import MagicMock

import pytest

from cartography.config import Config
from cartography.intel.anthropic import start_anthropic_ingestion

FEDERATION = {
    "anthropic_identity_token_file": "/token",
    "anthropic_federation_rule_id": "fdrl_test",
    "anthropic_organization_id": "00000000-0000-0000-0000-000000000000",
    "anthropic_service_account_id": "svac_test",
}


@pytest.mark.parametrize(
    ("settings", "message"),
    [
        ({**FEDERATION, "anthropic_apikey": "sk-ant-admin01-test"}, "not both"),
        ({"anthropic_workspace_id": "wrkspc_test"}, "needs an identity token file"),
    ],
)
def test_an_ambiguous_or_partial_credential_is_rejected(settings, message):
    config = Config(neo4j_uri="bolt://localhost:7687", update_tag=1, **settings)

    with pytest.raises(ValueError, match=message):
        start_anthropic_ingestion(MagicMock(), config)
