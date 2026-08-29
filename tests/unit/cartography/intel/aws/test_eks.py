import base64
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from unittest.mock import MagicMock
from unittest.mock import patch

from botocore.exceptions import ClientError
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtensionOID
from cryptography.x509.oid import NameOID

from cartography.intel.aws import eks


def _build_cert_base64(
    include_ski: bool,
    include_aki: bool,
    encoding: serialization.Encoding,
    not_valid_after: datetime,
    include_basic_constraints: bool = True,
) -> str:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "cartography-test-ca"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Cartography"),
        ]
    )
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=30))
        .not_valid_after(not_valid_after)
    )
    if include_basic_constraints:
        builder = builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
    if include_ski:
        builder = builder.add_extension(
            x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()),
            critical=False,
        )
    if include_aki:
        builder = builder.add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(
                private_key.public_key()
            ),
            critical=False,
        )

    cert = builder.sign(private_key=private_key, algorithm=hashes.SHA256())
    cert_bytes = cert.public_bytes(encoding)
    return base64.b64encode(cert_bytes).decode("utf-8")


def test_transform_eks_clusters_valid_der_certificate_authority_data():
    fake_now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    ca_data = _build_cert_base64(
        include_ski=True,
        include_aki=True,
        encoding=serialization.Encoding.DER,
        not_valid_after=fake_now + timedelta(days=365),
    )

    cluster_data = {
        "prod-cluster": {
            "name": "prod-cluster",
            "arn": "arn:aws:eks:us-east-1:123456789012:cluster/prod-cluster",
            "createdAt": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "resourcesVpcConfig": {"endpointPublicAccess": True},
            "logging": {"clusterLogging": [{"types": ["audit"], "enabled": True}]},
            "certificateAuthority": {"data": ca_data},
        },
    }

    transformed = eks.transform(cluster_data)

    assert len(transformed) == 1
    cluster = transformed[0]
    cert = x509.load_der_x509_certificate(base64.b64decode(ca_data))
    expected_ski = cert.extensions.get_extension_for_oid(
        ExtensionOID.SUBJECT_KEY_IDENTIFIER
    ).value.digest.hex()
    expected_aki = cert.extensions.get_extension_for_oid(
        ExtensionOID.AUTHORITY_KEY_IDENTIFIER
    ).value.key_identifier.hex()
    assert cluster["certificate_authority_data_present"] is True
    assert cluster["certificate_authority_parse_status"] == "parsed"
    assert cluster["certificate_authority_parse_error"] is None
    assert cluster["certificate_authority_sha256_fingerprint"] is not None
    assert cluster["certificate_authority_subject"] is not None
    assert cluster["certificate_authority_issuer"] is not None
    assert isinstance(cluster["certificate_authority_not_before"], datetime)
    assert isinstance(cluster["certificate_authority_not_after"], datetime)
    assert cluster["certificate_authority_not_before"].tzinfo == timezone.utc
    assert cluster["certificate_authority_not_after"].tzinfo == timezone.utc
    assert cluster["certificate_authority_subject_key_identifier"] == expected_ski
    assert cluster["certificate_authority_authority_key_identifier"] == expected_aki


def test_transform_eks_clusters_access_config_authentication_mode():
    cluster_data = {
        "prod-cluster": {
            "name": "prod-cluster",
            "arn": "arn:aws:eks:us-east-1:123456789012:cluster/prod-cluster",
            "resourcesVpcConfig": {"endpointPublicAccess": True},
            "logging": {"clusterLogging": []},
            "accessConfig": {"authenticationMode": "API_AND_CONFIG_MAP"},
        },
    }

    transformed = eks.transform(cluster_data)

    assert transformed[0]["AuthenticationMode"] == "API_AND_CONFIG_MAP"


def test_transform_access_entries_adds_id_and_cluster_arn():
    # Arrange
    access_entries = [
        {
            "clusterName": "prod-cluster",
            "principalArn": "arn:aws:iam::123456789012:role/EKSAdmin",
            "accessEntryArn": (
                "arn:aws:eks:us-east-1:123456789012:access-entry/"
                "prod-cluster/role/123456789012/EKSAdmin/ae-12345"
            ),
            "username": "eks-admin",
            "type": "STANDARD",
            "kubernetesGroups": ["system:masters"],
        },
    ]

    # Act
    transformed = eks.transform_access_entries(
        access_entries,
        "arn:aws:eks:us-east-1:123456789012:cluster/prod-cluster",
    )

    # Assert
    assert transformed == [
        {
            "id": (
                "arn:aws:eks:us-east-1:123456789012:cluster/prod-cluster/"
                "access-entry/arn:aws:iam::123456789012:role/EKSAdmin"
            ),
            "cluster_arn": "arn:aws:eks:us-east-1:123456789012:cluster/prod-cluster",
            "clusterName": "prod-cluster",
            "principalArn": "arn:aws:iam::123456789012:role/EKSAdmin",
            "accessEntryArn": (
                "arn:aws:eks:us-east-1:123456789012:access-entry/"
                "prod-cluster/role/123456789012/EKSAdmin/ae-12345"
            ),
            "username": "eks-admin",
            "type": "STANDARD",
            "kubernetesGroups": ["system:masters"],
        },
    ]


def test_transform_access_entries_uses_stable_id_when_detail_is_missing():
    # Arrange
    access_entries = [
        {
            "clusterName": "prod-cluster",
            "principalArn": "arn:aws:iam::123456789012:role/EKSAdmin",
        },
    ]

    # Act
    transformed = eks.transform_access_entries(
        access_entries,
        "arn:aws:eks:us-east-1:123456789012:cluster/prod-cluster",
    )

    # Assert
    assert transformed == [
        {
            "id": (
                "arn:aws:eks:us-east-1:123456789012:cluster/prod-cluster/"
                "access-entry/arn:aws:iam::123456789012:role/EKSAdmin"
            ),
            "cluster_arn": "arn:aws:eks:us-east-1:123456789012:cluster/prod-cluster",
            "clusterName": "prod-cluster",
            "principalArn": "arn:aws:iam::123456789012:role/EKSAdmin",
        },
    ]


@patch("cartography.intel.aws.eks.create_boto3_client")
def test_get_eks_access_entries_skips_config_map_auth_mode(mock_create_client):
    result = eks.get_eks_access_entries(
        MagicMock(),
        "us-east-1",
        "prod-cluster",
        "CONFIG_MAP",
    )

    assert result == []
    mock_create_client.assert_not_called()


@patch("cartography.intel.aws.eks.create_boto3_client")
def test_get_eks_access_entries_uses_list_output_when_describe_is_denied(
    mock_create_client,
    caplog,
):
    client = MagicMock()
    paginator = MagicMock()
    paginator.paginate.return_value = [
        {
            "accessEntries": [
                "arn:aws:iam::123456789012:role/EKSAdmin",
                "arn:aws:iam::123456789012:role/EKSDeveloper",
            ]
        }
    ]
    client.get_paginator.return_value = paginator
    client.describe_access_entry.side_effect = ClientError(
        {
            "Error": {
                "Code": "AccessDeniedException",
                "Message": "not authorized",
            }
        },
        "DescribeAccessEntry",
    )
    mock_create_client.return_value = client

    with caplog.at_level("WARNING"):
        result = eks.get_eks_access_entries(
            MagicMock(),
            "us-east-1",
            "prod-cluster",
            "API_AND_CONFIG_MAP",
        )

    assert result == [
        {
            "clusterName": "prod-cluster",
            "principalArn": "arn:aws:iam::123456789012:role/EKSAdmin",
        },
        {
            "clusterName": "prod-cluster",
            "principalArn": "arn:aws:iam::123456789012:role/EKSDeveloper",
        },
    ]
    assert client.describe_access_entry.call_count == 1
    assert "loading minimal access entry data" in caplog.text


@patch("cartography.intel.aws.eks.create_boto3_client")
def test_get_eks_access_entries_skips_regional_access_error(
    mock_create_client,
    caplog,
):
    # Arrange
    client = MagicMock()
    paginator = MagicMock()
    paginator.paginate.side_effect = ClientError(
        {
            "Error": {
                "Code": "AuthFailure",
                "Message": "AWS was not able to validate the provided credentials",
            }
        },
        "ListAccessEntries",
    )
    client.get_paginator.return_value = paginator
    mock_create_client.return_value = client

    # Act
    with caplog.at_level("WARNING"):
        result = eks.get_eks_access_entries(
            MagicMock(),
            "us-east-1",
            "prod-cluster",
            "API_AND_CONFIG_MAP",
        )

    # Assert
    assert result == []
    assert "Skipping" in caplog.text


def test_transform_eks_clusters_valid_pem_certificate_authority_data():
    fake_now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    ca_data = _build_cert_base64(
        include_ski=False,
        include_aki=False,
        encoding=serialization.Encoding.PEM,
        not_valid_after=fake_now - timedelta(days=2),
    )
    cluster_data = {
        "staging-cluster": {
            "name": "staging-cluster",
            "arn": "arn:aws:eks:us-east-1:123456789012:cluster/staging-cluster",
            "resourcesVpcConfig": {"endpointPublicAccess": True},
            "logging": {"clusterLogging": []},
            "certificateAuthority": {"data": ca_data},
        },
    }

    transformed = eks.transform(cluster_data)

    assert len(transformed) == 1
    cluster = transformed[0]
    assert cluster["certificate_authority_data_present"] is True
    assert cluster["certificate_authority_parse_status"] == "parsed"
    assert cluster["certificate_authority_parse_error"] is None
    assert cluster["certificate_authority_sha256_fingerprint"] is not None
    assert cluster["certificate_authority_subject_key_identifier"] is None
    assert cluster["certificate_authority_authority_key_identifier"] is None


def test_transform_eks_clusters_certificate_without_extensions_has_null_ski_aki():
    fake_now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    ca_data = _build_cert_base64(
        include_ski=False,
        include_aki=False,
        include_basic_constraints=False,
        encoding=serialization.Encoding.DER,
        not_valid_after=fake_now + timedelta(days=365),
    )
    cluster_data = {
        "test-cluster": {
            "name": "test-cluster",
            "arn": "arn:aws:eks:us-east-1:123456789012:cluster/test-cluster",
            "resourcesVpcConfig": {"endpointPublicAccess": True},
            "logging": {"clusterLogging": []},
            "certificateAuthority": {"data": ca_data},
        },
    }

    transformed = eks.transform(cluster_data)

    assert len(transformed) == 1
    cluster = transformed[0]
    assert cluster["certificate_authority_parse_status"] == "parsed"
    assert cluster["certificate_authority_subject_key_identifier"] is None
    assert cluster["certificate_authority_authority_key_identifier"] is None


def test_transform_eks_clusters_missing_certificate_authority_data():
    cluster_data = {
        "dev-cluster": {
            "name": "dev-cluster",
            "arn": "arn:aws:eks:us-east-1:123456789012:cluster/dev-cluster",
            "resourcesVpcConfig": {"endpointPublicAccess": False},
            "logging": {"clusterLogging": []},
        },
    }

    transformed = eks.transform(cluster_data)

    assert len(transformed) == 1
    cluster = transformed[0]
    assert cluster["certificate_authority_data_present"] is False
    assert cluster["certificate_authority_parse_status"] == "missing"
    assert cluster["certificate_authority_parse_error"] is None
    assert cluster["certificate_authority_sha256_fingerprint"] is None
    assert cluster["certificate_authority_subject_key_identifier"] is None
    assert cluster["certificate_authority_authority_key_identifier"] is None


def test_transform_eks_clusters_invalid_base64_logs_warning(caplog):
    cluster_data = {
        "beta-cluster": {
            "name": "beta-cluster",
            "arn": "arn:aws:eks:us-east-1:123456789012:cluster/beta-cluster",
            "resourcesVpcConfig": {"endpointPublicAccess": True},
            "logging": {"clusterLogging": []},
            "certificateAuthority": {"data": "not-valid-base64$$$"},
        },
    }

    with caplog.at_level("WARNING"):
        transformed = eks.transform(cluster_data)

    assert len(transformed) == 1
    cluster = transformed[0]
    assert cluster["certificate_authority_data_present"] is True
    assert cluster["certificate_authority_parse_status"] == "invalid_base64"
    assert cluster["certificate_authority_parse_error"] is not None
    assert cluster["certificate_authority_sha256_fingerprint"] is None
    assert cluster["certificate_authority_subject_key_identifier"] is None
    assert cluster["certificate_authority_authority_key_identifier"] is None
    assert "beta-cluster" in caplog.text
    assert "status=invalid_base64" in caplog.text


def test_transform_eks_clusters_invalid_certificate_logs_warning(caplog):
    invalid_cert_bytes = b"this-is-not-a-certificate"
    cluster_data = {
        "invalid-cert-cluster": {
            "name": "invalid-cert-cluster",
            "arn": "arn:aws:eks:us-east-1:123456789012:cluster/invalid-cert-cluster",
            "resourcesVpcConfig": {"endpointPublicAccess": True},
            "logging": {"clusterLogging": []},
            "certificateAuthority": {
                "data": base64.b64encode(invalid_cert_bytes).decode("utf-8")
            },
        },
    }

    with caplog.at_level("WARNING"):
        transformed = eks.transform(cluster_data)

    assert len(transformed) == 1
    cluster = transformed[0]
    assert cluster["certificate_authority_data_present"] is True
    assert cluster["certificate_authority_parse_status"] == "invalid_certificate"
    assert cluster["certificate_authority_parse_error"] is not None
    assert cluster["certificate_authority_sha256_fingerprint"] is None
    assert cluster["certificate_authority_subject_key_identifier"] is None
    assert cluster["certificate_authority_authority_key_identifier"] is None
    assert "invalid-cert-cluster" in caplog.text
    assert "status=invalid_certificate" in caplog.text
