from cartography.intel.okta.origins import transform_trusted_origins
from tests.data.okta.trustedorigin import LIST_TRUSTED_ORIGIN_RESPONSE


def test_transform_trusted_origin_all_values():
    result = transform_trusted_origins(LIST_TRUSTED_ORIGIN_RESPONSE)

    expected = [
        {
            "id": "tosue7JvguwJ7U6kz0g3",
            "name": "Example Trusted Origin",
            "origin": "http://example.com",
            "scopes": ["CORS"],
            "status": "ACTIVE",
            "created": "2018-01-13T01:22:10.000Z",
            "created_by": "00ut5t92p6IEOi4bu0ge3",
            "okta_last_updated": "2018-01-13T01:22:10.000Z",
            "okta_last_updated_by": "00ut5t92p6IEOi4bu0g3",
        },
        {
            "id": "tos10hzarOl8zfPM80g4",
            "name": "Another Trusted Origin",
            "origin": "https://rf.example.com",
            "scopes": ["CORS", "REDIRECT"],
            "status": "ACTIVE",
            "created": "2017-11-16T05:01:12.000Z",
            "created_by": "00ut5t92p6IEOi4bu10g31",
            "okta_last_updated": "2017-12-16T05:01:12.000Z",
            "okta_last_updated_by": "00ut5t92p6IEOi4bu0g34",
        },
    ]

    assert result == expected
