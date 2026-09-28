from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.data.frameworks.soc2 import soc2_tsc
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AWSRDSAutomatedBackupsDisabledOutput(Finding):
    instance_name: str | None = None
    instance_id: str | None = None
    account_id: str | None = None
    account: str | None = None
    engine: str | None = None
    region: str | None = None
    backup_retention_period: int | None = None


_aws_rds_automated_backups_disabled = Fact(
    id="aws_rds_automated_backups_disabled",
    name="AWS RDS instances without automated backups",
    description=(
        "Detects standalone AWS RDS instances whose backup retention period is "
        "zero, which disables automated backups."
    ),
    cypher_query="""
    MATCH (account:AWSAccount)-[:RESOURCE]->(instance:AWSRDSInstance)
    WHERE instance.db_cluster_identifier IS NULL
      AND coalesce(instance.backup_retention_period, 0) = 0
    RETURN
        instance.db_instance_identifier AS instance_name,
        instance.id AS instance_id,
        account.id AS account_id,
        account.name AS account,
        instance.engine AS engine,
        instance.region AS region,
        instance.backup_retention_period AS backup_retention_period
    """,
    cypher_visual_query="""
    MATCH p=(account:AWSAccount)-[:RESOURCE]->(instance:AWSRDSInstance)
    WHERE instance.db_cluster_identifier IS NULL
      AND coalesce(instance.backup_retention_period, 0) = 0
    RETURN *
    """,
    cypher_count_query="""
    MATCH (instance:AWSRDSInstance)
    WHERE instance.db_cluster_identifier IS NULL
    RETURN COUNT(instance) AS count
    """,
    asset_label="AWSRDSInstance",
    asset_id_field="instance_id",
    identity_fields=("instance_id",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_automated_backups_disabled = Rule(
    id="aws_rds_automated_backups_disabled",
    name="AWS RDS Automated Backups Disabled",
    description=(
        "Detects standalone AWS RDS instances with automated backups disabled."
    ),
    output_model=AWSRDSAutomatedBackupsDisabledOutput,
    facts=(_aws_rds_automated_backups_disabled,),
    tags=("aws", "rds", "database", "backup", "resilience"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.13"),
        soc2_tsc("A1.2"),
    ),
)
