from cartography.intel.gcp import iam


def test_build_role_permissions_by_name_skips_empty_permission_roles():
    roles = [
        {
            "name": "roles/storage.objectViewer",
            "includedPermissions": ["storage.objects.get"],
        },
        {
            "name": "roles/empty",
            "includedPermissions": [],
        },
        {
            "name": "roles/missing",
        },
        {
            "includedPermissions": ["storage.objects.create"],
        },
    ]

    assert iam.build_role_permissions_by_name(roles) == {
        "roles/storage.objectViewer": ["storage.objects.get"],
    }
