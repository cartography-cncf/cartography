import pytest

from cartography.intel.trivy.scanner import _build_image_subcommand


def test_build_image_subcommand_default_args():
    """Test the function with default arguments."""
    result = _build_image_subcommand(skip_update=False)

    # Should contain default arguments
    assert "--format" in result
    assert "json" in result
    assert "--timeout" in result
    assert "15m" in result
    assert "--ignore-unfixed" in result
    assert len(result) == 5  # 2 pairs of arguments plus one single argument


def test_build_image_subcommand_skip_update():
    """Test the function with skip_update=True."""
    result = _build_image_subcommand(skip_update=True)

    assert "--skip-update" in result
    assert "--ignore-unfixed" in result


def test_build_image_subcommand_with_policy_file():
    """Test the function with a policy file path."""
    policy_path = "/path/to/policy.yaml"
    result = _build_image_subcommand(
        skip_update=False, triage_filter_policy_file_path=policy_path
    )

    assert "--ignore-policy" in result
    assert policy_path in result


def test_build_image_subcommand_os_findings_only():
    """Test the function with os_findings_only=True."""
    result = _build_image_subcommand(skip_update=False, os_findings_only=True)

    assert "--vuln-type" in result
    assert "os" in result


def test_build_image_subcommand_list_all_packages():
    """Test the function with list_all_pkgs=True."""
    result = _build_image_subcommand(skip_update=False, list_all_pkgs=True)

    assert "--list-all-pkgs" in result


def test_build_image_subcommand_security_checks():
    """Test the function with security_checks parameter."""
    security_checks = "vuln,config"
    result = _build_image_subcommand(skip_update=False, security_checks=security_checks)

    assert "--security-checks" in result
    assert security_checks in result


def test_build_image_subcommand_all_options():
    """Test the function with all options enabled."""
    policy_path = "/path/to/policy.yaml"
    security_checks = "vuln,config"

    result = _build_image_subcommand(
        skip_update=True,
        ignore_unfixed=True,
        triage_filter_policy_file_path=policy_path,
        os_findings_only=True,
        list_all_pkgs=True,
        security_checks=security_checks,
    )

    # Check all expected arguments are present
    assert "--skip-update" in result
    assert "--ignore-unfixed" in result
    assert "--ignore-policy" in result
    assert policy_path in result
    assert "--vuln-type" in result
    assert "os" in result
    assert "--list-all-pkgs" in result
    assert "--security-checks" in result
    assert security_checks in result
