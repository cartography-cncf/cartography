import neo4j


def create_test_entra_tenant(
    neo4j_session: neo4j.Session, tenant_id: str, update_tag: int
) -> None:
    neo4j_session.run(
        """
        MERGE (tenant:EntraTenant{id: $tenant_id})
        ON CREATE SET tenant.firstseen = timestamp()
        SET tenant.lastupdated = $update_tag,
            tenant.display_name = $display_name
        """,
        tenant_id=tenant_id,
        display_name="Test Tenant",
        update_tag=update_tag,
    )
