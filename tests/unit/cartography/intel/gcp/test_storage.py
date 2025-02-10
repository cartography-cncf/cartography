import cartography.intel.gcp.storage
from tests.data.gcp.storage import STORAGE_RESPONSE


def test_transform_gcp_buckets():
    bucket_list = cartography.intel.gcp.storage.transform_gcp_buckets(STORAGE_RESPONSE)
    assert len(bucket_list) == 1
    bucket = bucket_list[0]
    assert bucket["etag"] == "CAE="
    assert bucket["project_number"] == 9999
    assert bucket["id"] == "bucket_name"
    assert bucket["self_link"] == "https://www.googleapis.com/storage/v1/b/bucket_name"
    assert bucket["retention_period"] is None
