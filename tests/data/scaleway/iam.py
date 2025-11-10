from datetime import datetime

from dateutil.tz import tzutc
from scaleway.iam.v1alpha1 import APIKey
from scaleway.iam.v1alpha1 import Application
from scaleway.iam.v1alpha1 import Group
from scaleway.iam.v1alpha1 import User

SCALEWAY_USERS = [
    User(
        id="998cbe72-913f-4f55-8620-4b0f7655d343",
        email="mbsimpson@simpson.corp",
        username="mbsimpson@simpson.corp",
        organization_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        created_at=datetime(2025, 3, 20, 7, 39, 54, 526837, tzinfo=tzutc()),
        updated_at=datetime(2025, 6, 20, 9, 19, 54, 496281, tzinfo=tzutc()),
        deletable=False,
        type_="owner",
        status="activated",
        mfa=True,
        account_root_user_id="db2c157f-0ae0-4f9c-aa24-bcccba549e52",
        tags=[],
        locked=False,
        last_login_at=datetime(2025, 6, 20, 9, 19, 54, 502555, tzinfo=tzutc()),
        two_factor_enabled=True,
        first_name="Marge",
        last_name="Simpson",
        phone_number="",
        locale="en_US",
    ),
    User(
        id="b49932b2-2faa-4c56-905e-ffac52f063dc",
        email="hjsimpson@simpson.corp",
        username="hjsimpson@simpson.corp",
        organization_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        created_at=datetime(2025, 3, 20, 7, 39, 54, 526837, tzinfo=tzutc()),
        updated_at=datetime(2025, 6, 20, 9, 19, 54, 496281, tzinfo=tzutc()),
        deletable=False,
        type_="member",
        status="activated",
        mfa=True,
        account_root_user_id="2ee21608-b892-46c5-9acc-ee20a30ea7fe",
        tags=[],
        locked=False,
        last_login_at=datetime(2025, 6, 20, 9, 19, 54, 502555, tzinfo=tzutc()),
        two_factor_enabled=True,
        first_name="Homer",
        last_name="Simpson",
        phone_number="",
        locale="en_US",
    ),
]

SCALEWAY_APPLICATIONS = [
    Application(
        id="98300a5a-438e-45dc-8b34-07b1adc7c409",
        name="Mail Sender",
        description="System account for sending emails",
        organization_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        editable=True,
        deletable=True,
        managed=False,
        nb_api_keys=1,
        tags=[],
        created_at=datetime(2025, 3, 23, 20, 52, 20, 849566, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 23, 20, 52, 20, 849566, tzinfo=tzutc()),
    ),
    Application(
        id="c92d472f-f916-4071-b076-c8907c83e016",
        name="Terraform",
        description="System account for Terraform",
        organization_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        editable=True,
        deletable=True,
        managed=False,
        nb_api_keys=1,
        tags=[],
        created_at=datetime(2025, 3, 24, 9, 21, 55, 542948, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 24, 9, 21, 55, 542948, tzinfo=tzutc()),
    ),
]

SCALEWAY_GROUPS = [
    Group(
        id="1f767996-f6f6-4b0e-a7b1-6a255e809ed6",
        organization_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        name="Administrators",
        description="built-in admin group",
        user_ids=["998cbe72-913f-4f55-8620-4b0f7655d343"],
        application_ids=["c92d472f-f916-4071-b076-c8907c83e016"],
        tags=[],
        editable=True,
        deletable=True,
        managed=False,
        created_at=datetime(2025, 3, 20, 11, 13, 35, 109782, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 11, 13, 35, 109782, tzinfo=tzutc()),
    )
]

SCALEWAY_APIKEYS = [
    APIKey(
        access_key="SCWXXX",
        description="terraform",
        default_project_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        editable=True,
        deletable=True,
        managed=False,
        creation_ip="8.9.10.11",
        secret_key=None,
        created_at=datetime(2025, 3, 20, 10, 58, 0, 784077, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 10, 58, 0, 784077, tzinfo=tzutc()),
        expires_at=None,
        application_id="c92d472f-f916-4071-b076-c8907c83e016",
        user_id=None,
    ),
    APIKey(
        access_key="SCWYYY",
        description="",
        default_project_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        editable=True,
        deletable=True,
        managed=False,
        creation_ip="42.42.42.42",
        secret_key=None,
        created_at=datetime(2025, 3, 23, 20, 52, 21, 8165, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 23, 20, 52, 21, 8165, tzinfo=tzutc()),
        expires_at=datetime(2026, 3, 23, 20, 52, 20, tzinfo=tzutc()),
        application_id=None,
        user_id="b49932b2-2faa-4c56-905e-ffac52f063dc",
    ),
]
