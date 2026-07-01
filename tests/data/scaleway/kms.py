from datetime import datetime

from dateutil.tz import tzutc
from scaleway.key_manager.v1alpha1 import Key

TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"

TEST_KEY_ID = "kkkk1111-1111-4820-b8d6-0eef10cfcd6d"

SCALEWAY_KEYS = [
    Key(
        id=TEST_KEY_ID,
        project_id=TEST_PROJECT_ID,
        name="demo-key",
        state="enabled",
        rotation_count=0,
        protected=False,
        locked=False,
        tags=["demo"],
        origin="scaleway_kms",
        region="fr-par",
        usage=None,
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        description="Demo key",
        rotated_at=None,
        rotation_policy=None,
        deletion_requested_at=None,
    )
]
