from tests.data.databricks.workspace import scoped

# One row per (principal, object), as databricks.permissions.get() +
# get_secret_scope_acls() produce after flattening each object's ACL. Principals
# are named the way the permissions API reports them: user_name for users,
# display name for groups, OAuth application id for service principals.
# object_id is the workspace-scoped node id of the ACL-bearing object.
DATABRICKS_PERMISSIONS = [
    # User -> Cluster
    {
        "principal": "jeremy@subimage.io",
        "object_id": scoped("0202-cluster-aaaa"),
        "permission_level": ["CAN_MANAGE"],
        "object_type": "clusters",
    },
    # Group -> Job
    {
        "principal": "admins",
        "object_id": scoped("1011944831447606"),
        "permission_level": ["CAN_MANAGE_RUN", "CAN_VIEW"],
        "object_type": "jobs",
    },
    # ServicePrincipal -> Secret scope (from the secrets ACL endpoint)
    {
        "principal": "abcd1234-5678-90ab-cdef-1234567890ab",
        "object_id": scoped("ci-cd"),
        "permission_level": ["MANAGE"],
        "object_type": "secret-scope",
    },
    # Principal not ingested in this workspace: dropped by resolve_principals.
    {
        "principal": "account users",
        "object_id": scoped("0202-cluster-aaaa"),
        "permission_level": ["CAN_ATTACH_TO"],
        "object_type": "clusters",
    },
]
