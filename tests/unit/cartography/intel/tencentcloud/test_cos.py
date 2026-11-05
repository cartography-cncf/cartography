from unittest.mock import Mock
from unittest.mock import patch

from tencentcloud.common.credential import Credential

from cartography.intel.tencentcloud import cos

TEST_CREDENTIAL = Credential("test-secret-id", "test-secret-key")


def test_sign_request_produces_the_cos_authorization_header():
    # Expected value derived independently from the official cos-python-sdk-v5
    # CosS3Auth implementation for the same inputs.

    # Act
    authorization = cos.sign_request(
        TEST_CREDENTIAL,
        "GET",
        "/",
        {"acl": ""},
        {"host": "examplebucket-1250000000.cos.ap-beijing.myqcloud.com"},
        now=1557989211,
    )

    # Assert
    assert authorization == (
        "q-sign-algorithm=sha1"
        "&q-ak=test-secret-id"
        "&q-sign-time=1557989151;1557989811"
        "&q-key-time=1557989151;1557989811"
        "&q-header-list=host"
        "&q-url-param-list=acl"
        "&q-signature=6fded13faf98275264999d9b2d77ead416a2f4b0"
    )


def _xml_response(body: str) -> Mock:
    response = Mock()
    response.status_code = 200
    response.content = body.encode()
    return response


def test_get_buckets_follows_the_next_marker_while_truncated():
    # Arrange
    first_page = _xml_response(
        "<ListAllMyBucketsResult><Buckets><Bucket><Name>a-1250000000</Name>"
        "<Location>ap-guangzhou</Location></Bucket></Buckets>"
        "<IsTruncated>true</IsTruncated><NextMarker>a-1250000000</NextMarker>"
        "</ListAllMyBucketsResult>",
    )
    second_page = _xml_response(
        "<ListAllMyBucketsResult><Buckets><Bucket><Name>b-1250000000</Name>"
        "<Location>ap-singapore</Location></Bucket></Buckets>"
        "<IsTruncated>false</IsTruncated></ListAllMyBucketsResult>",
    )

    # Act
    with patch(
        "cartography.intel.tencentcloud.cos.requests.get",
        side_effect=[first_page, second_page],
    ):
        buckets = cos.get_buckets(TEST_CREDENTIAL)

    # Assert
    assert [bucket["Name"] for bucket in buckets] == ["a-1250000000", "b-1250000000"]


def test_get_buckets_returns_nothing_for_an_account_without_buckets():
    # Arrange
    response = _xml_response(
        "<ListAllMyBucketsResult><Owner><ID>qcs::cam::uin/1:uin/1</ID></Owner>"
        "<Buckets/></ListAllMyBucketsResult>",
    )

    # Act
    with patch(
        "cartography.intel.tencentcloud.cos.requests.get", return_value=response
    ):
        buckets = cos.get_buckets(TEST_CREDENTIAL)

    # Assert
    assert buckets == []
