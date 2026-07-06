from datetime import datetime

from dateutil.tz import tzutc
from scaleway.registry.v1 import Image
from scaleway.registry.v1 import ImageStatus
from scaleway.registry.v1 import ImageVisibility
from scaleway.registry.v1 import Namespace
from scaleway.registry.v1 import NamespaceStatus
from scaleway.registry.v1 import Tag
from scaleway.registry.v1 import TagStatus

TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_NAMESPACE_ID = "aaaaaaaa-1111-4820-b8d6-0eef10cfcd6d"
TEST_IMAGE_ID = "bbbbbbbb-2222-4820-b8d6-0eef10cfcd6d"
TEST_TAG_ID = "cccccccc-3333-4820-b8d6-0eef10cfcd6d"
TEST_TAG_DIGEST = (
    "sha256:1111111111111111111111111111111111111111111111111111111111111111"
)


SCALEWAY_REGISTRY_NAMESPACES = [
    Namespace(
        id=TEST_NAMESPACE_ID,
        name="demo-namespace",
        description="Demo namespace",
        organization_id=TEST_ORG_ID,
        project_id=TEST_PROJECT_ID,
        status=NamespaceStatus.READY,
        status_message="",
        endpoint="rg.fr-par.scw.cloud/demo-namespace",
        is_public=True,
        size=1024,
        image_count=1,
        region="fr-par",
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
    )
]


SCALEWAY_REGISTRY_IMAGES = [
    Image(
        id=TEST_IMAGE_ID,
        name="demo-image",
        namespace_id=TEST_NAMESPACE_ID,
        status=ImageStatus.READY,
        visibility=ImageVisibility.INHERIT,
        size=1024,
        tags=["latest"],
        status_message=None,
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
    )
]


SCALEWAY_REGISTRY_TAGS = [
    Tag(
        id=TEST_TAG_ID,
        name="latest",
        image_id=TEST_IMAGE_ID,
        status=TagStatus.READY,
        digest=TEST_TAG_DIGEST,
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
    )
]
