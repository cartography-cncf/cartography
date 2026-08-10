from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID


def _uc_id(full_name):
    return f"{DATABRICKS_METASTORE_ID}/{full_name}"


# One row per (principal, securable), as databricks.grants.get() produces after
# flattening privilege_assignments across securables. Principals are named the
# way UC reports them: username for users, display name for groups, OAuth
# application id for service principals.
DATABRICKS_GRANTS = [
    {
        "principal": "jeremy@subimage.io",
        "securable_id": _uc_id("prod"),
        "privileges": ["USE_CATALOG", "ALL_PRIVILEGES"],
    },
    {
        "principal": "admins",
        "securable_id": _uc_id("prod.finance.customers"),
        "privileges": ["SELECT"],
    },
    {
        "principal": "abcd1234-5678-90ab-cdef-1234567890ab",
        "securable_id": _uc_id("prod.finance"),
        "privileges": ["USE_SCHEMA"],
    },
]
