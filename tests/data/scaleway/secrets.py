from datetime import datetime

from dateutil.tz import tzutc
from scaleway.secret.v1beta1 import Secret
from scaleway.secret.v1beta1 import SecretVersion

TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"

TEST_SECRET_ID = "aaaa1111-1111-4820-b8d6-0eef10cfcd6d"
TEST_KEY_ID = "kkkk1111-1111-4820-b8d6-0eef10cfcd6d"

SCALEWAY_SECRETS = [
    Secret(
        id=TEST_SECRET_ID,
        project_id=TEST_PROJECT_ID,
        name="demo-secret",
        status="ready",
        tags=["demo"],
        version_count=1,
        managed=False,
        protected=False,
        type_="opaque",
        path="/",
        used_by=[],
        region="fr-par",
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        description="Demo secret",
        ephemeral_policy=None,
        deletion_requested_at=None,
        key_id=TEST_KEY_ID,
    )
]

SCALEWAY_SECRET_VERSIONS_BY_SECRET = {
    TEST_SECRET_ID: [
        SecretVersion(
            revision=1,
            secret_id=TEST_SECRET_ID,
            status="enabled",
            latest=True,
            region="fr-par",
            created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
            updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
            deleted_at=None,
            description="initial",
            ephemeral_properties=None,
            deletion_requested_at=None,
        ),
    ],
}
