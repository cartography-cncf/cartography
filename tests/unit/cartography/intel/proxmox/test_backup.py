"""
Unit tests for Proxmox backup job transform functions.
"""

from cartography.intel.proxmox.backup import transform_backup_job_data


def test_transform_backup_job_with_prune_settings():
    """
    Test that prune-backups map is correctly flattened into primitive properties.
    This verifies the fix for Neo4j CypherTypeError when storing map values.
    """
    # Arrange
    raw_jobs = [
        {
            "id": "job-1",
            "schedule": "0 2 * * *",
            "storage": "nfs-backup",
            "enabled": 1,
            "mode": "snapshot",
            "compress": "zstd",
            "prune-backups": {
                "keep-last": "7",
                "keep-weekly": "4",
                "keep-monthly": "6",
            },
            "repeat-missed": 1,
        },
    ]
    cluster_id = "test-cluster"

    # Act
    transformed = transform_backup_job_data(raw_jobs, cluster_id)

    # Assert
    assert len(transformed) == 1
    job = transformed[0]

    # Check required fields
    assert job["id"] == "job-1"
    assert job["job_id"] == "job-1"
    assert job["cluster_id"] == "test-cluster"
    assert job["schedule"] == "0 2 * * *"
    assert job["storage"] == "nfs-backup"
    assert job["enabled"] == 1
    assert job["mode"] == "snapshot"
    assert job["compression"] == "zstd"
    assert job["repeat_missed"] == 1

    # Check flattened prune properties - should be integers
    assert job["prune_keep_last"] == 7
    assert job["prune_keep_weekly"] == 4
    assert job["prune_keep_monthly"] == 6
    # Missing prune properties should be None
    assert job["prune_keep_hourly"] is None
    assert job["prune_keep_daily"] is None
    assert job["prune_keep_yearly"] is None


def test_transform_backup_job_without_prune_settings():
    """
    Test that jobs without prune-backups have all prune properties set to None.
    """
    # Arrange
    raw_jobs = [
        {
            "id": "job-2",
            "schedule": "0 3 * * *",
            "storage": "local",
            "enabled": 0,
            "mode": "snapshot",
        },
    ]
    cluster_id = "test-cluster"

    # Act
    transformed = transform_backup_job_data(raw_jobs, cluster_id)

    # Assert
    assert len(transformed) == 1
    job = transformed[0]

    # All prune properties should be None
    assert job["prune_keep_last"] is None
    assert job["prune_keep_hourly"] is None
    assert job["prune_keep_daily"] is None
    assert job["prune_keep_weekly"] is None
    assert job["prune_keep_monthly"] is None
    assert job["prune_keep_yearly"] is None


def test_transform_backup_job_with_partial_prune_settings():
    """
    Test that jobs with partial prune-backups have correct mix of values and None.
    """
    # Arrange
    raw_jobs = [
        {
            "id": "job-3",
            "schedule": "0 0 * * 0",
            "storage": "nfs-backup",
            "enabled": 1,
            "mode": "stop",
            "prune-backups": {
                "keep-last": "4",
                "keep-hourly": "2",
            },
        },
    ]
    cluster_id = "test-cluster"

    # Act
    transformed = transform_backup_job_data(raw_jobs, cluster_id)

    # Assert
    assert len(transformed) == 1
    job = transformed[0]

    # Present prune properties should be integers
    assert job["prune_keep_last"] == 4
    assert job["prune_keep_hourly"] == 2
    # Missing prune properties should be None
    assert job["prune_keep_daily"] is None
    assert job["prune_keep_weekly"] is None
    assert job["prune_keep_monthly"] is None
    assert job["prune_keep_yearly"] is None


def test_transform_backup_job_with_all_prune_settings():
    """
    Test that jobs with all prune-backups settings are correctly transformed.
    """
    # Arrange
    raw_jobs = [
        {
            "id": "job-4",
            "schedule": "0 1 * * *",
            "storage": "local",
            "enabled": 1,
            "mode": "suspend",
            "prune-backups": {
                "keep-last": "5",
                "keep-hourly": "24",
                "keep-daily": "7",
                "keep-weekly": "4",
                "keep-monthly": "12",
                "keep-yearly": "3",
            },
        },
    ]
    cluster_id = "test-cluster"

    # Act
    transformed = transform_backup_job_data(raw_jobs, cluster_id)

    # Assert
    assert len(transformed) == 1
    job = transformed[0]

    # All prune properties should be present as integers
    assert job["prune_keep_last"] == 5
    assert job["prune_keep_hourly"] == 24
    assert job["prune_keep_daily"] == 7
    assert job["prune_keep_weekly"] == 4
    assert job["prune_keep_monthly"] == 12
    assert job["prune_keep_yearly"] == 3


def test_transform_multiple_backup_jobs():
    """
    Test transforming multiple backup jobs with varying prune settings.
    """
    # Arrange
    raw_jobs = [
        {
            "id": "job-a",
            "schedule": "0 2 * * *",
            "storage": "nfs-backup",
            "enabled": 1,
            "mode": "snapshot",
            "prune-backups": {
                "keep-last": "7",
            },
        },
        {
            "id": "job-b",
            "schedule": "0 3 * * *",
            "storage": "local",
            "enabled": 0,
            "mode": "suspend",
            # No prune-backups
        },
        {
            "id": "job-c",
            "schedule": "0 4 * * *",
            "storage": "nfs-backup",
            "enabled": 1,
            "mode": "stop",
            "prune-backups": {
                "keep-weekly": "4",
                "keep-monthly": "6",
            },
        },
    ]
    cluster_id = "test-cluster"

    # Act
    transformed = transform_backup_job_data(raw_jobs, cluster_id)

    # Assert
    assert len(transformed) == 3

    # Job A - only keep-last
    assert transformed[0]["id"] == "job-a"
    assert transformed[0]["prune_keep_last"] == 7
    assert transformed[0]["prune_keep_weekly"] is None

    # Job B - no prune settings
    assert transformed[1]["id"] == "job-b"
    assert transformed[1]["prune_keep_last"] is None
    assert transformed[1]["prune_keep_weekly"] is None

    # Job C - weekly and monthly only
    assert transformed[2]["id"] == "job-c"
    assert transformed[2]["prune_keep_last"] is None
    assert transformed[2]["prune_keep_weekly"] == 4
    assert transformed[2]["prune_keep_monthly"] == 6
