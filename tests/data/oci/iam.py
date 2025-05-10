# Copyright (c) 2020, Oracle and/or its affiliates.
import datetime

LIST_USERS = {
    "Users": [
        {
            "capabilities": {
                "can-use-api-keys": True,
                "can-use-auth-tokens": True,
                "can-use-console-password": True,
                "can-use-customer-secret-keys": True,
                "can-use-smtp-credentials": True,
            },
            "compartment-id": "ocid1.tenancy.oc1..nqilyrb1l5t6gnmlcjgeim8q47vccnklev8k2ud9skn78eapu116oyv9wcr0",
            "defined-tags": {},
            "description": "example-description-0",
            "email": None,
            "external-identifier": None,
            "freeform-tags": {},
            "id": "ocid1.user.oc1..m5oaceraqeiq47zqstzy6ickbbfkw7vg4srozp4sskn78eapu116oyv9wcr0",
            "identity-provider-id": None,
            "inactive-status": None,
            "is-mfa-activated": False,
            "lifecycle-state": "ACTIVE",
            "name": "example-user-0",
            "time-created": datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
        {
            "capabilities": {
                "can-use-api-keys": True,
                "can-use-auth-tokens": True,
                "can-use-console-password": True,
                "can-use-customer-secret-keys": True,
                "can-use-smtp-credentials": True,
            },
            "compartment-id": "ocid1.tenancy.oc1..nqilyrb1l5t6gnmlcjgeim8q47vccnklev8k2ud9skn78eapu116oyv9wcr0",
            "defined-tags": {},
            "description": "example-description-1",
            "email": None,
            "external-identifier": None,
            "freeform-tags": {},
            "id": "ocid1.user.oc1..srozp4sskn78eapu116oyv9wcr06ickbbfkw7vg4m5oaceraqeiq47zqstzy",
            "identity-provider-id": None,
            "inactive-status": None,
            "is-mfa-activated": False,
            "lifecycle-state": "ACTIVE",
            "name": "example-user-1",
            "time-created": datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
    ],
}


LIST_GROUPS = {
    "Groups": [
        {
            "compartment-id": "ocid1.tenancy.oc1..nqilyrb1l5t6gnmlcjgeim8q47vccnklev8k2ud9skn78eapu116oyv9wcr0",
            "defined-tags": {},
            "description": "example-description-0",
            "freeform-tags": {},
            "id": "ocid1.group.oc1..wa03xlg35zi0tb33qyrjteen36zrkauzhjz8pi0yzt4d2b78uo745h5ze6at",
            "inactive-status": None,
            "lifecycle-state": "ACTIVE",
            "name": "example-group-0",
            "time-created": datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
        {
            "compartment-id": "ocid1.tenancy.oc1..nqilyrb1l5t6gnmlcjgeim8q47vccnklev8k2ud9skn78eapu116oyv9wcr0",
            "defined-tags": {},
            "description": "example-description-1",
            "freeform-tags": {},
            "id": "ocid1.group.oc1..bkan5que3j9ixlsf0xn56xrj7xnjgez0bhfqll68zt4d2b78uo745h5ze6at",
            "inactive-status": None,
            "lifecycle-state": "ACTIVE",
            "name": "example-group-1",
            "time-created": datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
    ],
}


LIST_POLICIES = {
    "Policies": [
        {
            "compartment-id": "ocid1.tenancy.oc1..nqilyrb1l5t6gnmlcjgeim8q47vccnklev8k2ud9skn78eapu116oyv9wcr0",
            "defined-tags": {},
            "description": "example-description-0",
            "freeform-tags": {},
            "id": "ocid1.policy.oc1..aecin4w1x06m8lm4tvutzd5lmibackk8r1vgnb54h038960q9i41f11rwazz",
            "inactive-status": None,
            "lifecycle-state": "ACTIVE",
            "name": "example-policy-0",
            "statements": [
                "allow group example-group-0 to read all-resources in compartment example-compartment-0",
                "allow group example-group-0 to inspect all-resources in compartment example-compartment-0",
            ],
            "time-created": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "version-date": None,
        },
        {
            "compartment-id": "ocid1.tenancy.oc1..nqilyrb1l5t6gnmlcjgeim8q47vccnklev8k2ud9skn78eapu116oyv9wcr0",
            "defined-tags": {},
            "description": "example-description-1",
            "freeform-tags": {},
            "id": "ocid1.policy.oc1..4tvutzd5lmibackk8r1vaecin4w1x06m8lmgnb54h038960q9i41f11rwazz",
            "inactive-status": None,
            "lifecycle-state": "ACTIVE",
            "name": "example-policy-1",
            "statements": [
                "allow group example-group-1 to read all-resources in compartment example-compartment-1",
                "allow group example-group-1 to inspect all-resources in compartment example-compartment-1",
            ],
            "time-created": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "version-date": None,
        },
    ],
}

LIST_COMPARTMENTS = {
    "Compartments": [
        {
            "compartment-id": "ocid1.tenancy.oc1..nqilyrb1l5t6gnmlcjgeim8q47vccnklev8k2ud9skn78eapu116oyv9wcr0",
            "defined-tags": {},
            "description": "example-description-0",
            "freeform-tags": {},
            "id": "ocid1.compartment.oc1..cin4w1x06m84tnb54h038960q9i41vutzd5lmibackk8r1vaelmgf11rwazz",
            "inactive-status": None,
            "is-accessible": None,
            "lifecycle-state": "ACTIVE",
            "name": "example-compartment-0",
            "time-created": datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
        {
            "compartment-id": "ocid1.tenancy.oc1..nqilyrb1l5t6gnmlcjgeim8q47vccnklev8k2ud9skn78eapu116oyv9wcr0",
            "defined-tags": {},
            "description": "example-description-1",
            "freeform-tags": {},
            "id": "ocid1.compartment.oc1..54h038960q9i41vutzd5lmibac4tnbkkcin4w1x06m88r1vaelmgf11rwazz",
            "inactive-status": None,
            "is-accessible": None,
            "lifecycle-state": "ACTIVE",
            "name": "example-compartment-1",
            "time-created": datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
    ],
}

LIST_GROUP_MEMBERSHIPS = {
    "GroupMemberships": [
        {
            "compartment-id": "ocid1.tenancy.oc1..nqilyrb1l5t6gnmlcjgeim8q47vccnklev8k2ud9skn78eapu116oyv9wcr0",
            "group-id": "ocid1.group.oc1..wa03xlg35zi0tb33qyrjteen36zrkauzhjz8pi0yzt4d2b78uo745h5ze6at",
            "id": "ocid1.groupmembership.oc1..t6gnmlcjgeim8q47nqilyrb1l5vccnklev8k2ud9skn78eapu116oyv9wcr0",
            "inactive-status": None,
            "lifecycle-state": "ACTIVE",
            "time-created": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "user-id": "ocid1.user.oc1..m5oaceraqeiq47zqstzy6ickbbfkw7vg4srozp4sskn78eapu116oyv9wcr0",
        },
        {
            "compartment-id": "ocid1.tenancy.oc1..nqilyrb1l5t6gnmlcjgeim8q47vccnklev8k2ud9skn78eapu116oyv9wcr0",
            "group-id": "ocid1.group.oc1..wa03xlg35zi0tb33qyrjteen36zrkauzhjz8pi0yzt4d2b78uo745h5ze6at",
            "id": "ocid1.groupmembership.oc1..ud9skn78et6gnmlcjgeim8q47nqilyrb1l5vccnklev8k2apu116oyv9wcr0",
            "inactive-status": None,
            "lifecycle-state": "ACTIVE",
            "time-created": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "user-id": "ocid1.user.oc1..srozp4sskn78eapu116oyv9wcr06ickbbfkw7vg4m5oaceraqeiq47zqstzy",
        },
    ],
}
