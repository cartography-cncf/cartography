from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID

# Shape returned by shares.get() (the "shares" list).
DATABRICKS_SHARES = [
    {
        "id": "08069ca2-3917-4304-aa4c-a32ea240bbef",
        "name": "carto_test_share",
        "owner": "jeremy@subimage.io",
        "comment": "sub-1580 test",
        "created_at": 1782952357810,
        "created_by": "jeremy@subimage.io",
        "updated_at": 1782952357810,
    },
]

SHARE_ID = f"{DATABRICKS_METASTORE_ID}/carto_test_share"
