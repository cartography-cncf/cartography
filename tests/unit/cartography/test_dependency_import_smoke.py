import importlib


def test_dependency_resolve_import_smoke() -> None:
    modules = [
        "cartography",
        "cartography.intel.azure.util.credentials",
        "cartography.intel.azure.subscription",
        "cartography.intel.aws.ec2",
        "cartography.intel.gcp.crm.projects",
    ]

    for module_name in modules:
        importlib.import_module(module_name)
