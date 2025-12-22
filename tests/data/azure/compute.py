DESCRIBE_VMS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
        "type": "Microsoft.Compute/virtualMachines",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "TestVM",
        "plan": {
            "product": "Standard",
        },
        "handware_profile": {
            "vm_size": "Standard_D2s_v3",
        },
        "license_type": "Windows_Client ",
        "os_profile": {
            "computer_name": "TestVM",
        },
        "identity": {
            "type": "SystemAssigned",
        },
        "zones": [
            "West US 2",
        ],
        "additional_capabilities": {
            "ultra_ssd_enabled": True,
        },
        "priority": "Low",
        "eviction_policy": "Deallocate",
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM1",
        "type": "Microsoft.Compute/virtualMachines",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "TestVM1",
        "plan": {
            "product": "Standard",
        },
        "handware_profile": {
            "vm_size": "Standard_D2s_v3",
        },
        "license_type": "Windows_Client ",
        "os_profile": {
            "computer_name": "TestVM1",
        },
        "identity": {
            "type": "SystemAssigned",
        },
        "zones": [
            "West US 2",
        ],
        "additional_capabilities": {
            "ultra_ssd_enabled": True,
        },
        "priority": "Low",
        "eviction_policy": "Deallocate",
    },
]


DESCRIBE_VM_DATA_DISKS = [
    {
        "lun": 0,
        "name": "dd0",
        "create_option": "Empty",
        "caching": "ReadWrite",
        "managed_disk": {
            "storage_account_type": "Premium_LRS",
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd0",
        },
        "disk_size_gb": 30,
        "vm_id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
    },
    {
        "lun": 0,
        "name": "dd1",
        "create_option": "Empty",
        "caching": "ReadWrite",
        "managed_disk": {
            "storage_account_type": "Premium_LRS",
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd1",
        },
        "disk_size_gb": 30,
        "vm_id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
    },
]

DESCRIBE_DISKS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd0",
        "type": "Microsoft.Compute/disks",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "dd0",
        "creation_data": {
            "create_option": "Attach",
        },
        "disk_size_gb": 100,
        "encryption_settings_collection": {
            "enabled": True,
        },
        "max_shares": 10,
        "network_access_policy": "AllowAll",
        "os_type": "Windows",
        "tier": "P4",
        "sku": {
            "name": "Standard_LRS",
        },
        "zones": [
            "West US 2",
        ],
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd1",
        "type": "Microsoft.Compute/disks",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "dd1",
        "creation_data": {
            "create_option": "Attach",
        },
        "disk_size_gb": 100,
        "encryption_settings_collection": {
            "enabled": True,
        },
        "max_shares": 10,
        "network_access_policy": "AllowAll",
        "os_type": "Windows",
        "tier": "P4",
        "sku": {
            "name": "Standard_LRS",
        },
        "zones": [
            "West US 2",
        ],
    },
]

DESCRIBE_SNAPSHOTS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/snapshots/ss0",
        "type": "Microsoft.Compute/snapshots",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "ss0",
        "creation_data": {
            "create_option": "Attach",
        },
        "disk_size_gb": 100,
        "encryption_settings_collection": {
            "enabled": True,
        },
        "incremental": True,
        "network_access_policy": "AllowAll",
        "os_type": "Windows",
        "tier": "P4",
        "sku": {
            "name": "Standard_LRS",
        },
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/snapshots/ss1",
        "type": "Microsoft.Compute/snapshots",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "ss1",
        "creation_data": {
            "create_option": "Attach",
        },
        "disk_size_gb": 100,
        "encryption_settings_collection": {
            "enabled": True,
        },
        "incremental": True,
        "network_access_policy": "AllowAll",
        "os_type": "Windows",
        "tier": "P4",
        "sku": {
            "name": "Standard_LRS",
        },
    },
]
