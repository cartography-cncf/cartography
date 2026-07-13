import pytest

from cartography.intel.aws.util.botocore_config import create_aioboto3_client
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.botocore_config import create_boto3_resource
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.intel.aws.util.botocore_config import get_lambda_botocore_config


class FakeSession:
    def client(self, service_name, *args, **kwargs):
        return ("client", service_name, args, kwargs)

    def resource(self, service_name, *args, **kwargs):
        return ("resource", service_name, args, kwargs)


def test_get_botocore_config_defaults_to_standard_retries():
    config = get_botocore_config()

    assert config.retries["max_attempts"] == 3
    assert config.retries["mode"] == "standard"
    assert config.read_timeout == 120


def test_get_botocore_config_supports_pool_and_retry_overrides():
    config = get_botocore_config(max_pool_connections=50, max_attempts=8)

    assert config.max_pool_connections == 50
    assert config.retries["max_attempts"] == 8
    assert config.retries["mode"] == "standard"


def test_get_botocore_config_is_memoized_for_same_arguments():
    config_one = get_botocore_config(max_pool_connections=50)
    config_two = get_botocore_config(max_pool_connections=50)

    assert config_one is config_two


def test_get_botocore_config_supports_environment_overrides(monkeypatch):
    monkeypatch.setenv("CARTOGRAPHY_AWS_RETRY_MODE", "adaptive")
    monkeypatch.setenv("CARTOGRAPHY_AWS_MAX_ATTEMPTS", "5")
    monkeypatch.setenv("CARTOGRAPHY_AWS_READ_TIMEOUT", "45")

    config = get_botocore_config()

    assert config.retries["max_attempts"] == 5
    assert config.retries["mode"] == "adaptive"
    assert config.read_timeout == 45


def test_get_botocore_config_rejects_invalid_retry_mode(monkeypatch):
    monkeypatch.setenv("CARTOGRAPHY_AWS_RETRY_MODE", "fast")

    with pytest.raises(ValueError, match="CARTOGRAPHY_AWS_RETRY_MODE must be one of"):
        get_botocore_config()


def test_get_lambda_botocore_config_uses_fail_fast_standard_retries():
    config = get_lambda_botocore_config()

    assert config.retries["max_attempts"] == 2
    assert config.retries["mode"] == "standard"
    assert config.read_timeout == 30


def test_get_lambda_botocore_config_inherits_global_retry_mode_override(monkeypatch):
    monkeypatch.setenv("CARTOGRAPHY_AWS_RETRY_MODE", "adaptive")

    config = get_lambda_botocore_config()

    assert config.retries["max_attempts"] == 2
    assert config.retries["mode"] == "adaptive"
    assert config.read_timeout == 30


def test_create_boto3_client_uses_shared_config_by_default():
    client = create_boto3_client(FakeSession(), "ec2", region_name="eu-west-1")

    assert client[3]["config"] is get_botocore_config()
    assert client[3]["region_name"] == "eu-west-1"


def test_create_boto3_resource_uses_shared_config_by_default():
    resource = create_boto3_resource(FakeSession(), "iam")

    assert resource[3]["config"] is get_botocore_config()


def test_create_aioboto3_client_preserves_explicit_config_override():
    custom_config = get_botocore_config(max_attempts=8)

    client = create_aioboto3_client(FakeSession(), "ecr", config=custom_config)

    assert client[3]["config"] is custom_config
