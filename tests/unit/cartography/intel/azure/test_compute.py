from cartography.intel.azure.compute import transform_disk
from cartography.intel.azure.compute import transform_snapshot
from cartography.intel.azure.compute import transform_vm
from cartography.intel.azure.compute import transform_vm_list


def test_transform_vm_flattens_sdk_38_properties():
    vm = transform_vm(
        {
            "id": "vm-id",
            "properties": {
                "storageProfile": {
                    "dataDisks": [
                        {
                            "name": "data-disk",
                            "lun": 0,
                            "diskSizeGB": 128,
                        }
                    ]
                },
                "hardwareProfile": {"vmSize": "Standard_D2s_v3"},
                "osProfile": {"computerName": "vm"},
                "additionalCapabilities": {"ultraSSDEnabled": True},
                "licenseType": "Windows_Server",
                "evictionPolicy": "Deallocate",
            },
        }
    )

    assert vm["storage_profile"]["data_disks"][0]["disk_size_gb"] == 128
    assert vm["hardware_profile"]["vm_size"] == "Standard_D2s_v3"
    assert vm["os_profile"]["computer_name"] == "vm"
    assert vm["additional_capabilities"]["ultra_ssd_enabled"] is True
    assert vm["license_type"] == "Windows_Server"
    assert vm["eviction_policy"] == "Deallocate"


def test_transform_vm_list_finds_sdk_38_data_disks():
    vms, data_disks = transform_vm_list(
        [
            transform_vm(
                {
                    "id": "vm-id",
                    "properties": {
                        "storageProfile": {
                            "dataDisks": [
                                {
                                    "name": "data-disk",
                                    "lun": 0,
                                    "diskSizeGB": 128,
                                }
                            ]
                        }
                    },
                }
            )
        ]
    )

    assert vms[0]["id"] == "vm-id"
    assert data_disks == [
        {
            "name": "data-disk",
            "lun": 0,
            "diskSizeGB": 128,
            "disk_size_gb": 128,
            "vm_id": "vm-id",
        }
    ]


def test_transform_disk_and_snapshot_flatten_sdk_38_properties():
    disk = transform_disk(
        {
            "id": "disk-id",
            "properties": {
                "diskSizeGB": 128,
                "networkAccessPolicy": "AllowAll",
                "osType": "Linux",
                "diskState": "Attached",
            },
        }
    )
    snapshot = transform_snapshot(
        {
            "id": "snapshot-id",
            "properties": {
                "diskSizeGB": 128,
                "networkAccessPolicy": "AllowAll",
                "osType": "Linux",
                "incremental": True,
            },
        }
    )

    assert disk["disk_size_gb"] == 128
    assert disk["network_access_policy"] == "AllowAll"
    assert disk["os_type"] == "Linux"
    assert disk["disk_state"] == "Attached"
    assert snapshot["disk_size_gb"] == 128
    assert snapshot["network_access_policy"] == "AllowAll"
    assert snapshot["os_type"] == "Linux"
    assert snapshot["incremental"] is True
