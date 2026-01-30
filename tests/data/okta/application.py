LIST_APPLICATION_USER_ASSIGNED_RESPONSE = """
[
  {
    "id": "00ui2sVIFZNCNKFFNBPM",
    "externalId": "005o0000000umnEAAQ",
    "created": "2014-08-15T18:59:43.000Z",
    "lastUpdated": "2014-08-15T18:59:48.000Z",
    "scope": "USER",
    "status": "PROVISIONED",
    "statusChanged": "2014-08-15T18:59:48.000Z",
    "passwordChanged": null,
    "syncState": "SYNCHRONIZED",
    "lastSync": "2014-08-15T18:59:48.000Z",
    "credentials": {
      "userName": "user@example.com"
    },
    "profile": {
      "secondEmail": null,
      "lastName": "McJanky",
      "mobilePhone": "415-555-555",
      "email": "user@example.com",
      "salesforceGroups": [],
      "role": "CEO",
      "firstName": "Karl",
      "profile": "Standard Platform User"
    },
    "_links": {
      "app": {
        "href": "https://{yourOktaDomain}/api/v1/apps/0oajiqIRNXPPJBNZMGYL"
      },
      "user": {
        "href": "https://{yourOktaDomain}/api/v1/users/00ui2sVIFZNCNKFFNBPM"
      }
    }
  },
  {
    "id": "00ujsgVNDRESKKXERBUJ",
    "externalId": "005o0000000uqJaAAI",
    "created": "2014-08-16T02:35:14.000Z",
    "lastUpdated": "2014-08-16T02:56:49.000Z",
    "scope": "USER",
    "status": "PROVISIONED",
    "statusChanged": "2014-08-16T02:56:49.000Z",
    "passwordChanged": null,
    "syncState": "SYNCHRONIZED",
    "lastSync": "2014-08-16T02:56:49.000Z",
    "credentials": {
      "userName": "saml.jackson@example.com"
    },
    "profile": {
      "secondEmail": null,
      "lastName": "Jackson",
      "mobilePhone": null,
      "email": "saml.jackson@example.com",
      "salesforceGroups": [
        "Employee"
      ],
      "role": "Developer",
      "firstName": "Saml",
      "profile": "Standard User"
    },
    "_links": {
      "app": {
        "href": "https://{yourOktaDomain}/api/v1/apps/0oajiqIRNXPPJBNZMGYL"
      },
      "user": {
        "href": "https://{yourOktaDomain}/api/v1/users/00ujsgVNDRESKKXERBUJ"
      }
    }
  }
]
"""

LIST_APPLICATION_GROUP_ASSIGNED_RESPONSE = """
[
  {
    "id": "00gbkkGFFWZDLCNTAGQR",
    "lastUpdated": "2013-10-02T07:38:20.000Z",
    "priority": 0
  },
  {
    "id": "00gg0xVALADWBPXOFZAS",
    "lastUpdated": "2013-10-02T14:40:29.000Z",
    "priority": 1
  }
]
"""

APPLICATION_WITH_REDITECT_URIS = """
{
    "id": "someid",
    "name": "redirec_app",
    "label": "ciexec",
    "status": "ACTIVE",
    "lastUpdated": "2019-01-10T18:28:42.000Z",
    "created": "2019-01-10T18:28:42.000Z",
    "accessibility": {
        "selfService": false,
        "errorRedirectUrl": null,
        "loginRedirectUrl": null
    },
    "visibility": {
        "autoSubmitToolbar": false,
        "hide": {
            "iOS": true,
            "web": true
        },
        "appLinks": {
            "oidc_client_link": true
        }
    },
    "features": [],
    "signOnMode": "OPENID_CONNECT",
    "credentials": {
        "userNameTemplate": {
            "template": "${source.login}",
            "type": "BUILT_IN"
        },
        "signing": {},
        "oauthClient": {
            "autoKeyRotation": true,
            "client_id": "someid",
            "token_endpoint_auth_method": "client_secret_basic"
        }
    },
    "settings": {
        "app": {},
        "notifications": {},
        "oauthClient": {
            "client_uri": null,
            "logo_uri": null,
            "redirect_uris": [
                "https://domain.net/auth/oauth2/callback1",
                "https://domain.net/auth/oauth2/callback"
            ],
            "response_types": [
                "code"
            ],
            "grant_types": [
                "authorization_code"
            ],
            "application_type": "web",
            "issuer_mode": "ORG_URL"
        }
    }
}
"""


def create_test_application():
    app = {
        "id": "app_id_value",
        "name": "app_name_value",
        "label": "app_label_value",
        "created": "2019-01-01T00:00:01.000Z",
        "lastUpdated": "2019-01-01T00:00:01.000Z",
        "status": "app_status_value",
        "activated": "2019-01-01T00:00:01.000Z",
        "features": "app_features_value",
        "signOnMode": "app_signonmode_value",
    }
    return app
