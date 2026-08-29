from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID

# Shape returned by recipients.get() (the "recipients" list). One open (TOKEN)
# recipient and one Databricks-to-Databricks recipient.
DATABRICKS_RECIPIENTS = [
    {
        "name": "carto_test_recipient",
        "authentication_type": "TOKEN",
        "activated": True,
        "owner": "jeremy@subimage.io",
        "comment": "sub-1580 open-sharing test",
        "cloud": "aws",
        "region": "us-west-2",
        "created_at": 1782952000000,
        "created_by": "jeremy@subimage.io",
        "updated_at": 1782952000000,
    },
    {
        "name": "partner_account",
        "authentication_type": "DATABRICKS",
        "activated": True,
        "owner": "jeremy@subimage.io",
        "data_recipient_global_metastore_id": "aws:us-east-1:abc-def-partner",
        "created_at": 1782952000000,
        "created_by": "jeremy@subimage.io",
    },
]

# Metastore-scoped node id for each recipient (uc_id(metastore_id, name)).
RECIPIENT_TOKEN_ID = f"{DATABRICKS_METASTORE_ID}/carto_test_recipient"
RECIPIENT_DB_ID = f"{DATABRICKS_METASTORE_ID}/partner_account"
