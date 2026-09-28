from cartography.models.zendesk.api_token import ZendeskAPITokenSchema


def test_api_token_native_id_is_indexed() -> None:
    assert ZendeskAPITokenSchema().properties.token_id.extra_index is True
