"""
Mock data for Proxmox backup job tests.
"""

MOCK_BACKUP_JOB_DATA = [
    {
        "id": "backup-daily-vms",
        "schedule": "0 2 * * *",  # Daily at 2 AM
        "storage": "nfs-backup",
        "enabled": 1,
        "mode": "snapshot",
        "compress": "zstd",
        "mailnotification": "always",
        "mailto": "admin@example.com",
        "notes": "Daily backup of all VMs",
        "prune-backups": "keep-last=7,keep-weekly=4,keep-monthly=6",
        "repeat-missed": 1,
        "vmid": "100,101",  # Backup specific VMs
    },
    {
        "id": "backup-weekly-full",
        "schedule": "0 0 * * 0",  # Weekly on Sunday
        "storage": "nfs-backup",
        "enabled": 1,
        "mode": "stop",
        "compress": "gzip",
        "mailnotification": "failure",
        "mailto": "ops@example.com",
        "notes": "Weekly full backup",
        "prune-backups": "keep-last=4",
        "repeat-missed": 0,
        "vmid": "all",  # Backup all VMs
    },
    {
        "id": "backup-containers",
        "schedule": "0 3 * * *",  # Daily at 3 AM
        "storage": "local",
        "enabled": 1,
        "mode": "suspend",
        "compress": "lzo",
        "mailnotification": "never",
        "notes": "Container backups",
        "prune-backups": "keep-last=3",
        "repeat-missed": 0,
        "vmid": "200",  # Specific container
    },
    {
        "id": "backup-disabled",
        "schedule": "0 4 * * *",
        "storage": "local",
        "enabled": 0,  # Disabled
        "mode": "snapshot",
        "vmid": "all",
    },
]
