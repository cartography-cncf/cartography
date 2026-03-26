from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.intel.aws.util.botocore_config import wrap_aioboto3_session
from cartography.intel.aws.util.botocore_config import wrap_boto3_session


class FakeSession:
    def __init__(self) -> None:
        self.profile_name = "default"

    def client(self, service_name, *args, **kwargs):
        return ("client", service_name, args, kwargs)

    def resource(self, service_name, *args, **kwargs):
        return ("resource", service_name, args, kwargs)


def test_get_botocore_config_defaults_to_adaptive_retries():
    config = get_botocore_config()

    assert config.retries["max_attempts"] == 10
    assert config.retries["mode"] == "adaptive"
    assert config.read_timeout == 360


def test_get_botocore_config_supports_pool_and_retry_overrides():
    config = get_botocore_config(max_pool_connections=50, max_attempts=8)

    assert config.max_pool_connections == 50
    assert config.retries["max_attempts"] == 8
    assert config.retries["mode"] == "adaptive"


def test_get_botocore_config_is_memoized_for_same_arguments():
    config_one = get_botocore_config(max_pool_connections=50)
    config_two = get_botocore_config(max_pool_connections=50)

    assert config_one is config_two


def test_wrap_boto3_session_injects_default_config_into_clients_and_resources():
    wrapped = wrap_boto3_session(FakeSession())

    client = wrapped.client("ec2", region_name="eu-west-1")
    resource = wrapped.resource("iam")

    assert client[3]["config"] is get_botocore_config()
    assert client[3]["region_name"] == "eu-west-1"
    assert resource[3]["config"] is get_botocore_config()
    assert wrapped.profile_name == "default"


def test_wrap_boto3_session_preserves_explicit_config_override():
    custom_config = get_botocore_config(max_attempts=8)
    wrapped = wrap_boto3_session(FakeSession())

    client = wrapped.client("s3", config=custom_config)

    assert client[3]["config"] is custom_config


def test_wrap_aioboto3_session_injects_default_config_into_clients():
    wrapped = wrap_aioboto3_session(FakeSession())

    client = wrapped.client("ecr", region_name="us-east-1")

    assert client[3]["config"] is get_botocore_config()
    assert client[3]["region_name"] == "us-east-1"


def test_wrap_boto3_session_is_idempotent():
    wrapped = wrap_boto3_session(FakeSession())

    assert wrap_boto3_session(wrapped) is wrapped
