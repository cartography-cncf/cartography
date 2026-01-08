from cartography.intel.slack.utils import slack_paginate


class FakeSlackClient:
    def __init__(self, responses):
        self._responses = responses
        self.calls = 0

    def users_list(self, **kwargs):
        response = self._responses[self.calls]
        self.calls += 1
        return response


def test_slack_paginate_stops_on_none_cursor():
    client = FakeSlackClient(
        [
            {
                "members": [{"id": "U1"}],
                "response_metadata": {"next_cursor": None},
            },
        ],
    )

    result = slack_paginate(client, "users_list", "members")

    assert result == [{"id": "U1"}]
    assert client.calls == 1


def test_slack_paginate_respects_page_limit(monkeypatch):
    import cartography.intel.slack.utils as slack_utils

    monkeypatch.setattr(slack_utils, "MAX_PAGINATION_PAGES", 1)

    client = FakeSlackClient(
        [
            {
                "members": [{"id": "U1"}],
                "response_metadata": {"next_cursor": "next"},
            },
            {
                "members": [{"id": "U2"}],
                "response_metadata": {"next_cursor": ""},
            },
        ],
    )

    result = slack_paginate(client, "users_list", "members")

    assert result == [{"id": "U1"}]
    assert client.calls == 1


def test_slack_paginate_respects_item_limit(monkeypatch):
    import cartography.intel.slack.utils as slack_utils

    monkeypatch.setattr(slack_utils, "MAX_PAGINATION_ITEMS", 1)

    client = FakeSlackClient(
        [
            {
                "members": [{"id": "U1"}, {"id": "U2"}],
                "response_metadata": {"next_cursor": "next"},
            },
        ],
    )

    result = slack_paginate(client, "users_list", "members")

    assert result == [{"id": "U1"}, {"id": "U2"}]
    assert client.calls == 1
