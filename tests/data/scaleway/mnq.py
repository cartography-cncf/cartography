from datetime import datetime

from dateutil.tz import tzutc
from scaleway.mnq.v1beta1 import SqsCredentials
from scaleway.mnq.v1beta1 import SqsInfo
from scaleway.mnq.v1beta1 import SqsInfoStatus
from scaleway.mnq.v1beta1 import SqsPermissions

TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"

TEST_CREDENTIAL_ID = "crcrcrcr-1111-4820-b8d6-0eef10cfcd6d"

SCALEWAY_MNQ_SQS_INFO = [
    SqsInfo(
        project_id=TEST_PROJECT_ID,
        region="fr-par",
        status=SqsInfoStatus.ENABLED,
        sqs_endpoint_url="https://sqs.mnq.fr-par.scw.cloud/v2",
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
    ),
]

# `secret_key` mirrors what the live API actually returns alongside the credential's
# metadata, so tests can assert it is discarded rather than merely absent from the
# fixture.
SCALEWAY_MNQ_SQS_CREDENTIALS = [
    SqsCredentials(
        id=TEST_CREDENTIAL_ID,
        name="demo-sqs-credentials",
        project_id=TEST_PROJECT_ID,
        region="fr-par",
        access_key="SCWTESTACCESSKEY0001",
        secret_key="SUPER_SECRET_VALUE=do-not-ingest-me",
        secret_checksum="deadbeef",
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        permissions=SqsPermissions(
            can_publish=True, can_receive=True, can_manage=False
        ),
    ),
]
