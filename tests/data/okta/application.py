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


SAML_APPLICATION_WITH_UNKNOWN_FEATURE = {
    "id": "0oaFeatures",
    "name": "myorg_app_1",
    "label": "Custom SAML app",
    "status": "ACTIVE",
    "signOnMode": "SAML_2_0",
    "features": [
        "PUSH_NEW_USERS",
        "AUTO_CONFIRM_IMPORTS",
        "SCIM_PROVISIONING",
    ],
    "settings": {
        "signOn": {
            "allowMultipleAcsEndpoints": False,
            "assertionSigned": True,
            "honorForceAuthn": True,
            "requestCompressed": False,
            "responseSigned": True,
            "audience": "https://example.com",
            "destination": "https://example.com",
            "idpIssuer": "https://example.com",
            "recipient": "https://example.com",
            "ssoAcsUrl": "https://example.com",
            "digestAlgorithm": "SHA256",
            "signatureAlgorithm": "RSA_SHA256",
            "authnContextClassRef": "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
            "subjectNameIdFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
            "subjectNameIdTemplate": "${user.userName}",
        },
    },
}

OIN_BROWSER_PLUGIN_APPLICATION = {
    "id": "0oaOinSwa",
    "name": "docusign",
    "label": "DocuSign",
    "status": "ACTIVE",
    "signOnMode": "BROWSER_PLUGIN",
    "settings": {},
}

BOOKMARK_APPLICATION_WITHOUT_URL = {
    "id": "0oaBookmark",
    "name": "bookmark",
    "label": "Bookmark",
    "status": "ACTIVE",
    "signOnMode": "BOOKMARK",
    "settings": {
        "app": {
            "regionType": "com",
            "subdomain": "example",
            "domain": "example.com",
        },
    },
}

# The SDK falls back to the base Application class when signOnMode is unknown,
# and to ActiveDirectoryApplication when it is null. Neither declares every
# nested sub-object the transform reads.
APPLICATION_WITH_UNKNOWN_SIGN_ON_MODE = {
    "id": "0oaUnknownMode",
    "label": "MFA as a service app",
    "status": "ACTIVE",
    "signOnMode": "MFA_AS_SERVICE",
}

ACTIVE_DIRECTORY_APPLICATION = {
    "id": "0oaActiveDirectory",
    "name": "active_directory",
    "label": "example.com",
    "status": "ACTIVE",
    "signOnMode": None,
    "settings": {
        "app": {
            "domain": "example.com",
        },
    },
}

# An API Services app: an OAuth service app that authenticates with a private key
# and requires DPoP.
SERVICE_APPLICATION = {
    "id": "0oaService",
    "name": "oidc_client",
    "label": "Inventory service",
    "status": "ACTIVE",
    "signOnMode": "OPENID_CONNECT",
    "credentials": {
        "oauthClient": {
            "autoKeyRotation": True,
            "client_id": "0oaService",
            "token_endpoint_auth_method": "private_key_jwt",
        },
    },
    "settings": {
        "oauthClient": {
            "application_type": "service",
            "grant_types": ["client_credentials"],
            "response_types": ["token"],
            "dpop_bound_access_tokens": True,
        },
    },
}

# A web OIDC app that authenticates with a client secret.
WEB_OIDC_APPLICATION = {
    "id": "0oaWeb",
    "name": "oidc_client",
    "label": "Internal portal",
    "status": "ACTIVE",
    "signOnMode": "OPENID_CONNECT",
    "credentials": {
        "oauthClient": {
            "autoKeyRotation": True,
            "client_id": "0oaWeb",
            "token_endpoint_auth_method": "client_secret_basic",
        },
    },
    "settings": {
        "oauthClient": {
            "application_type": "web",
            "grant_types": ["authorization_code"],
            "redirect_uris": ["https://portal.example.com/callback"],
            "response_types": ["code"],
            "dpop_bound_access_tokens": False,
        },
    },
}

APPLICATIONS = [
    SERVICE_APPLICATION,
    WEB_OIDC_APPLICATION,
    SAML_APPLICATION_WITH_UNKNOWN_FEATURE,
]

# GET /oauth2/v1/clients/{clientId}/roles, by client ID. The assignment ID has
# the form Okta's API reference shows for standard roles: derived from the role
# type, so it can repeat across assignees.
CLIENT_ROLES = {
    "0oaService": [
        {
            "id": "KNKVARKSL5AUITKJJY",
            "label": "Super Administrator",
            "type": "SUPER_ADMIN",
            "status": "ACTIVE",
            "created": "2026-01-05T10:00:00.000Z",
            "lastUpdated": "2026-01-05T10:00:00.000Z",
            "assignmentType": "CLIENT",
            "_links": {
                "assignee": {
                    "href": "https://example.okta.com/oauth2/v1/clients/0oaService",
                },
            },
        },
    ],
}

# GET /api/v1/apps/{appId}/grants, by app ID.
APP_GRANTS = {
    "0oaService": [
        {
            "id": "oagUsersRead",
            "status": "ACTIVE",
            "issuer": "https://example.okta.com",
            "clientId": "0oaService",
            "scopeId": "okta.users.read",
            "source": "ADMIN",
        },
        {
            "id": "oagAppsRead",
            "status": "ACTIVE",
            "issuer": "https://example.okta.com",
            "clientId": "0oaService",
            "scopeId": "okta.apps.read",
            "source": "ADMIN",
        },
        {
            "id": "oagGroupsManage",
            "status": "REVOKED",
            "issuer": "https://example.okta.com",
            "clientId": "0oaService",
            "scopeId": "okta.groups.manage",
            "source": "ADMIN",
        },
    ],
    "0oaWeb": [
        {
            "id": "oagUsersManage",
            "status": "ACTIVE",
            "issuer": "https://example.okta.com",
            "clientId": "0oaWeb",
            "scopeId": "okta.users.manage",
            "source": "ADMIN",
        },
    ],
}
