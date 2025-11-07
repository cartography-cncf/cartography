from cartography.rules.spec.model import Module
from cartography.rules.spec.model import MODULE_TO_CARTOGRAPHY_INTEL
from cartography.sync import TOP_LEVEL_MODULES


def test_all_module_keys_in_mapping_except_cross_cloud():
    """
    Test that all keys from the Module enum are present in MODULE_TO_CARTOGRAPHY_INTEL
    except for CROSS_CLOUD.
    """
    # Get all module enum values except CROSS_CLOUD
    expected_modules = {module for module in Module if module != Module.CROSS_CLOUD}

    # Get the keys from the mapping dictionary
    mapping_keys = set(MODULE_TO_CARTOGRAPHY_INTEL.keys())

    # Verify that all expected modules are in the mapping
    missing_modules = expected_modules - mapping_keys
    extra_modules = mapping_keys - expected_modules

    # Assert no modules are missing from the mapping
    assert (
        missing_modules == set()
    ), f"The following modules are missing from MODULE_TO_CARTOGRAPHY_INTEL: {missing_modules}"

    # Assert no extra modules are in the mapping
    assert (
        extra_modules == set()
    ), f"The following unexpected modules are in MODULE_TO_CARTOGRAPHY_INTEL: {extra_modules}"


def test_cross_cloud_not_in_mapping():
    """
    Test that CROSS_CLOUD is specifically not in the MODULE_TO_CARTOGRAPHY_INTEL mapping.
    """
    assert (
        Module.CROSS_CLOUD not in MODULE_TO_CARTOGRAPHY_INTEL
    ), "CROSS_CLOUD should not be present in MODULE_TO_CARTOGRAPHY_INTEL"


def test_mapping_values_exists():
    """
    Test that all values in MODULE_TO_CARTOGRAPHY_INTEL are strings.
    """
    for module, intel_name in MODULE_TO_CARTOGRAPHY_INTEL.items():
        assert intel_name is not None, f"Value for {module} should not be None"
        assert isinstance(intel_name, str), f"Value for {module} should be a string"
        assert intel_name != "", f"Value for {module} should not be empty"
        assert (
            intel_name in TOP_LEVEL_MODULES
        ), f"Value for {module} ('{intel_name}') should be a valid Cartography INTEL module"
