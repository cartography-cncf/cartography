import logging

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.cloudsql.backup_config import GCPSqlBackupConfigSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def transform_sql_backup_configs(instances_data: list[dict]) -> list[dict]:
    """
    Transforms backup configuration data from Cloud SQL instances for ingestion.
    """
    transformed: list[dict] = []
    for inst in instances_data:
        instance_id = inst.get("selfLink")
        if not instance_id:
            continue

        settings = inst.get("settings", {})
        backup_config = settings.get("backupConfiguration", {})

        # Only create a backup config node if backup configuration exists
        if not backup_config:
            continue

        backup_retention = backup_config.get("backupRetentionSettings", {})

        transformed.append(
            {
                "id": f"{instance_id}/backupConfig",
                "enabled": backup_config.get("enabled", False),
                "start_time": backup_config.get("startTime"),
                "location": backup_config.get("location"),
                "point_in_time_recovery_enabled": backup_config.get(
                    "pointInTimeRecoveryEnabled", False
                ),
                "transaction_log_retention_days": backup_config.get(
                    "transactionLogRetentionDays"
                ),
                "backup_retention_settings": (
                    str(backup_retention) if backup_retention else None
                ),
                "binary_log_enabled": backup_config.get("binaryLogEnabled", False),
                "instance_id": instance_id,
            },
        )
    return transformed


@timeit
def load_sql_backup_configs(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Loads GCPSqlBackupConfig nodes and their relationships.
    """
    load(
        neo4j_session,
        GCPSqlBackupConfigSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_sql_backup_configs(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Cleans up stale Cloud SQL backup configurations.
    """
    GraphJob.from_node_schema(GCPSqlBackupConfigSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_sql_backup_configs(
    neo4j_session: neo4j.Session,
    instances: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Syncs Cloud SQL Backup Configurations from instance data.
    """
    logger.info(f"Syncing Cloud SQL Backup Configurations for project {project_id}.")
    backup_configs = transform_sql_backup_configs(instances)
    load_sql_backup_configs(neo4j_session, backup_configs, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_sql_backup_configs(neo4j_session, cleanup_job_params)
