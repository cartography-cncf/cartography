import json
import logging

import requests
from azure.core.credentials import AccessToken
from azure.core.pipeline.transport import HttpTransport
from azure.core.pipeline.transport import RequestsTransportResponse
from azure.mgmt.security import SecurityCenter

from cartography.intel.azure.security_center import get_assessments

TEST_SUBSCRIPTION_ID = "00000000-0000-0000-0000-000000000000"
ASSESSMENT_ID = (
    f"/subscriptions/{TEST_SUBSCRIPTION_ID}/providers/Microsoft.Security/"
    "assessments/00000000-0000-0000-0000-000000000001"
)


class _FakeCredential:
    def get_token(self, *_scopes, **_kwargs):
        return AccessToken("token", 9999999999)


class _OnePageTransport(HttpTransport):
    def __init__(self, page):
        self._page = page

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        pass

    def open(self):
        pass

    def close(self):
        pass

    def send(self, request, **_kwargs):
        response = requests.Response()
        response.status_code = 200
        response.headers["Content-Type"] = "application/json"
        response._content = json.dumps(self._page).encode()
        return RequestsTransportResponse(request, response)


def test_get_assessments_does_not_warn_per_assessment_without_resource_source(
    caplog,
):
    # Arrange
    client = SecurityCenter(
        _FakeCredential(),
        TEST_SUBSCRIPTION_ID,
        transport=_OnePageTransport(
            {
                "value": [
                    {
                        "id": ASSESSMENT_ID,
                        "name": "00000000-0000-0000-0000-000000000001",
                        "properties": {
                            "displayName": "Example assessment",
                            "resourceDetails": {"Id": ASSESSMENT_ID},
                            "status": {"code": "Healthy"},
                        },
                    },
                ],
            },
        ),
    )

    # Act
    assessments = get_assessments(client, TEST_SUBSCRIPTION_ID)

    # Assert
    assert [assessment["id"] for assessment in assessments] == [ASSESSMENT_ID]
    assert [r for r in caplog.records if r.levelno >= logging.WARNING] == []
