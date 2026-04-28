from cartography.rules.spec.model import Framework
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import MODULE_TO_CARTOGRAPHY_INTEL
from cartography.sync import TOP_LEVEL_MODULES


def test_framework_normalizes_to_lowercase():
    """Test that Framework fields are normalized to lowercase."""
    fw = Framework(
        name="CIS AWS Foundations Benchmark",
        short_name="CIS",
        requirement="1.14",
        scope="AWS",
        revision="5.0",
    )
    assert fw.name == "cis aws foundations benchmark"
    assert fw.short_name == "cis"
    assert fw.scope == "aws"
    assert fw.revision == "5.0"
    assert fw.requirement == "1.14"


def test_framework_optional_fields():
    """Test that Framework works with optional scope and revision."""
    # Only required fields
    fw_minimal = Framework(
        name="NIST Framework",
        short_name="NIST",
        requirement="AC-1",
    )
    assert fw_minimal.scope is None
    assert fw_minimal.revision is None
    assert fw_minimal.requirement == "ac-1"

    # With scope only
    fw_with_scope = Framework(
        name="CIS Benchmark",
        short_name="CIS",
        requirement="1.1",
        scope="aws",
    )
    assert fw_with_scope.scope == "aws"
    assert fw_with_scope.revision is None

    # With revision only
    fw_with_revision = Framework(
        name="SOC 2",
        short_name="SOC2",
        requirement="CC6.1",
        revision="2017",
    )
    assert fw_with_revision.scope is None
    assert fw_with_revision.revision == "2017"


def test_framework_matches_case_insensitive():
    """Test that Framework.matches() is case-insensitive."""
    fw = Framework(
        name="CIS AWS Foundations Benchmark",
        short_name="CIS",
        requirement="1.14",
        scope="aws",
        revision="5.0",
    )
    # All match variations should work
    assert fw.matches("CIS")
    assert fw.matches("cis")
    assert fw.matches("CIS", "AWS")
    assert fw.matches("cis", "aws", "5.0")
    assert fw.matches(short_name="CIS", scope="AWS", revision="5.0")


def test_framework_matches_partial_filter():
    """Test that Framework.matches() works with partial filters."""
    fw = Framework(
        name="CIS AWS Foundations Benchmark",
        short_name="CIS",
        requirement="1.14",
        scope="aws",
        revision="5.0",
    )
    # Partial matches
    assert fw.matches("cis")
    assert fw.matches("cis", "aws")
    assert fw.matches(scope="aws")
    assert fw.matches(revision="5.0")

    # Non-matches
    assert not fw.matches("nist")
    assert not fw.matches("cis", "gcp")
    assert not fw.matches("cis", "aws", "4.0")


def test_framework_matches_with_optional_fields():
    """Test that Framework.matches() handles optional fields correctly."""
    # Framework without scope
    fw_no_scope = Framework(
        name="NIST Framework",
        short_name="NIST",
        requirement="AC-1",
    )
    assert fw_no_scope.matches("nist")
    assert not fw_no_scope.matches("nist", "aws")  # Can't match scope if None

    # Framework without revision
    fw_no_revision = Framework(
        name="CIS Benchmark",
        short_name="CIS",
        requirement="1.1",
        scope="aws",
    )
    assert fw_no_revision.matches("cis")
    assert fw_no_revision.matches("cis", "aws")
    assert not fw_no_revision.matches(
        "cis", "aws", "5.0"
    )  # Can't match revision if None


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
