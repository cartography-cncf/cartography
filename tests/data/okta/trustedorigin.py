# The API only returns allowedOktaApps on IFRAME_EMBED scopes, and both the
# scope list and the scope type are optional in the SDK model.
TRUSTED_ORIGIN_WITH_SPARSE_SCOPES = """
{
    "id": "tos1sparsescope0g5",
    "name": "Sparse Trusted Origin",
    "origin": "https://sparse.example.com",
    "scopes": [
        {
            "type": "IFRAME_EMBED",
            "allowedOktaApps": ["OKTA_ENDUSER"]
        },
        {
            "allowedOktaApps": ["OKTA_ENDUSER"]
        }
    ],
    "status": "ACTIVE",
    "created": "2018-01-13T01:22:10.000Z",
    "createdBy": "00ut5t92p6IEOi4bu0ge3",
    "lastUpdated": "2018-01-13T01:22:10.000Z",
    "lastUpdatedBy": "00ut5t92p6IEOi4bu0g3"
}
"""

TRUSTED_ORIGIN_WITHOUT_SCOPES = """
{
    "id": "tos1noscopes0000g6",
    "name": "Trusted Origin Without Scopes",
    "origin": "https://noscopes.example.com",
    "status": "ACTIVE",
    "created": "2018-01-13T01:22:10.000Z",
    "createdBy": "00ut5t92p6IEOi4bu0ge3",
    "lastUpdated": "2018-01-13T01:22:10.000Z",
    "lastUpdatedBy": "00ut5t92p6IEOi4bu0g3"
}
"""

LIST_TRUSTED_ORIGIN_RESPONSE = """
[
    {
        "id": "tosue7JvguwJ7U6kz0g3",
        "name": "Example Trusted Origin",
        "origin": "http://example.com",
        "scopes": [
            {
                "type": "CORS"
            }
        ],
        "status": "ACTIVE",
        "created": "2018-01-13T01:22:10.000Z",
        "createdBy": "00ut5t92p6IEOi4bu0ge3",
        "lastUpdated": "2018-01-13T01:22:10.000Z",
        "lastUpdatedBy": "00ut5t92p6IEOi4bu0g3",
        "_links": {
            "self": {
                "href": "https://{yourOktaDomain}/api/v1/trustedOrigins/tosue7JvguwJ7U6kz0g3",
                "hints": {
                    "allow": [
                        "GET",
                        "PUT",
                        "DELETE"
                    ]
                }
            },
            "deactivate": {
                "href": "https://{yourOktaDomain}/api/v1/trustedOrigins/tosue7JvguwJ7U6kz0g3/lifecycle/deactivate",
                "hints": {
                    "allow": [
                        "POST"
                    ]
                }
            }
        }
    },
    {
        "id": "tos10hzarOl8zfPM80g4",
        "name": "Another Trusted Origin",
        "origin": "https://rf.example.com",
        "scopes": [
            {
                "type": "CORS"
            },
            {
                "type": "REDIRECT"
            }
        ],
        "status": "ACTIVE",
        "created": "2017-11-16T05:01:12.000Z",
        "createdBy": "00ut5t92p6IEOi4bu10g31",
        "lastUpdated": "2017-12-16T05:01:12.000Z",
        "lastUpdatedBy": "00ut5t92p6IEOi4bu0g34",
        "_links": {
            "self": {
                "href": "https://{yourOktaDomain}/api/v1/trustedOrigins/tos10hzarOl8zfPM80g4",
                "hints": {
                    "allow": [
                        "GET",
                        "PUT",
                        "DELETE"
                    ]
                }
            },
            "deactivate": {
                "href": "https://{yourOktaDomain}/api/v1/trustedOrigins/tos10hzarOl8zfPM80g4/lifecycle/deactivate",
                "hints": {
                    "allow": [
                        "POST"
                    ]
                }
            }
        }
    }
]
"""
