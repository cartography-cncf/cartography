from okta.models.usergroup.UserGroup import UserGroup
from okta.models.usergroup.UserGroupProfile import UserGroupProfile

LIST_GROUP_MEMBER_RESPONSE = """
[
  {
    "id": "00u1f96ECLNVOKVMUSEA",
    "status": "ACTIVE",
    "created": "2013-12-12T16:14:22.000Z",
    "activated": "2013-12-12T16:14:22.000Z",
    "statusChanged": "2013-12-12T22:14:22.000Z",
    "lastLogin": "2013-12-12T22:14:22.000Z",
    "lastUpdated": "2015-11-15T19:23:32.000Z",
    "passwordChanged": "2013-12-12T22:14:22.000Z",
    "profile": {
      "firstName": "Easy",
      "lastName": "E",
      "email": "easy-e@example.com",
      "login": "easy-e@example.com",
      "mobilePhone": null
    },
    "credentials": {
      "password": {},
      "provider": {
        "type": "OKTA",
        "name": "OKTA"
      }
    },
    "_links": {
      "self": {
        "href": "https://{yourOktaDomain}/api/v1/users/00u1f96ECLNVOKVMUSEA"
      }
    }
  },
  {
    "id": "00u1f9cMYQZFMPVXIDIZ",
    "status": "ACTIVE",
    "created": "2013-12-12T16:14:42.000Z",
    "activated": "2013-12-12T16:14:42.000Z",
    "statusChanged": "2013-12-12T16:14:42.000Z",
    "lastLogin": "2013-12-12T18:14:42.000Z",
    "lastUpdated": "2013-12-12T16:14:42.000Z",
    "passwordChanged": "2013-12-12T16:14:42.000Z",
    "profile": {
      "firstName": "Dr.",
      "lastName": "Dre",
      "email": "dr.dre@example.com",
      "login": "dr.dre@example.com",
      "mobilePhone": null
    },
    "credentials": {
      "password": {},
      "provider": {
        "type": "OKTA",
        "name": "OKTA"
      }
    },
    "_links": {
      "self": {
        "href": "https://{yourOktaDomain}/api/v1/users/00u1f9cMYQZFMPVXIDIZ"
      }
    }
  }
]
"""

GROUP_MEMBERS_SAMPLE_DATA = [
    {
        "_links": {
            "self": {"href": "https://example.okta.com/api/v1/users/OKTA_USER_ID_1"},
        },
        "activated": "2017-05-02T00:42:33.000Z",
        "created": "2017-03-16T19:07:26.000Z",
        "credentials": {
            "emails": [
                {
                    "status": "VERIFIED",
                    "type": "PRIMARY",
                    "value": "jclarkson@example.com",
                },
                {
                    "status": "VERIFIED",
                    "type": "SECONDARY",
                    "value": "jclarkson@example.com",
                },
            ],
            "password": {},
            "provider": {"name": "OKTA", "type": "OKTA"},
            "recovery_question": {
                "question": "How many acres is the farm you " "bought?",
            },
        },
        "id": "OKTA_USER_ID_1",
        "lastLogin": "2021-08-20T21:03:13.000Z",
        "lastUpdated": "2021-08-12T03:46:45.000Z",
        "passwordChanged": "2020-11-19T21:07:19.000Z",
        "profile": {
            "firstName": "Jeremy",
            "lastName": "Clarkson",
            "login": "jclarkson@example.com",
            "email": "jclarkson@example.com",
            "secondEmail": "jclarkson@example.com",
        },
        "status": "ACTIVE",
        "statusChanged": "2017-05-30T18:19:05.000Z",
        "type": {"id": "OKTA_USER_TYPE"},
    },
    {
        "_links": {
            "self": {"href": "https://example.okta.com/api/v1/users/OKTA_USER_ID_2"},
        },
        "activated": "2017-05-02T00:44:47.000Z",
        "created": "2017-03-16T19:07:29.000Z",
        "credentials": {
            "emails": [
                {
                    "status": "VERIFIED",
                    "type": "PRIMARY",
                    "value": "jmay@example.com",
                },
                {
                    "status": "VERIFIED",
                    "type": "SECONDARY",
                    "value": "jmay2@example.com",
                },
            ],
            "password": {},
            "provider": {"name": "OKTA", "type": "OKTA"},
            "recovery_question": {
                "question": "What year was your " "favorite gin " "invented?",
            },
        },
        "id": "OKTA_USER_ID_2",
        "lastLogin": "2021-08-20T13:22:34.000Z",
        "lastUpdated": "2021-08-12T23:47:52.000Z",
        "passwordChanged": "2020-06-20T14:57:06.000Z",
        "profile": {
            "firstName": "James",
            "lastName": "May",
            "login": "jmay@example.com",
            "email": "jmay@example.com",
            "secondEmail": "jmay2@example.com",
        },
        "status": "ACTIVE",
        "statusChanged": "2017-06-20T14:57:06.000Z",
        "type": {"id": "OKTA_USER_TYPE"},
    },
    {
        "_links": {
            "self": {"href": "https://example.okta.com/api/v1/users/OKTA_USER_ID_3"},
        },
        "activated": "2017-05-02T00:42:49.000Z",
        "created": "2017-03-16T19:07:32.000Z",
        "credentials": {
            "emails": [
                {
                    "status": "VERIFIED",
                    "type": "PRIMARY",
                    "value": "rhammond@example.com",
                },
                {
                    "status": "VERIFIED",
                    "type": "SECONDARY",
                    "value": "rhammond2@example.com",
                },
            ],
            "password": {},
            "provider": {"name": "OKTA", "type": "OKTA"},
            "recovery_question": {
                "question": "What is the last car " "you destroyed?",
            },
        },
        "id": "OKTA_USER_ID_3",
        "lastLogin": "2021-08-09T18:03:58.000Z",
        "lastUpdated": "2021-08-17T18:59:44.000Z",
        "passwordChanged": "2021-05-24T15:18:33.000Z",
        "profile": {
            "firstName": "Richard",
            "lastName": "Hammond",
            "login": "rhammond@example.com",
            "email": "rhammond@example.com",
            "secondEmail": "rhammond2@example.com",
        },
        "status": "ACTIVE",
        "statusChanged": "2017-06-15T15:02:50.000Z",
        "type": {"id": "OKTA_USER_TYPE"},
    },
]


def create_test_group():
    group = UserGroup()
    group.id = "group_id_value"

    group.profile = UserGroupProfile()
    group.profile.name = "group_profile_name_value"
    group.profile.description = "group_profile_description_value"
    group.profile.samAccountName = "group_profile_samAccountName_value"
    group.profile.dn = "group_profile_dn_value"
    group.profile.windowsDomainQualifiedName = (
        "group_profile_windowsDomainQualifiedName_value"
    )
    group.profile.externalId = "group_profile_external_id_value"

    return group
