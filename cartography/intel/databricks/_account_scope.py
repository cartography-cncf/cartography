def account_scoped_id(account_id: str, scim_id: str) -> str:
    """Build an account-scoped node id ``{account_id}/{scim_id}``.

    Account-level SCIM ids (users, groups, service principals) are unique within
    a Databricks account but not globally, so node ids embed the account to keep
    multi-account ingestion from collapsing same-id principals into one Neo4j
    node. Mirrors the workspace-scoped ``util.scoped_id`` helper but keys on the
    account instead of a workspace.
    """
    return f"{account_id}/{scim_id}"
