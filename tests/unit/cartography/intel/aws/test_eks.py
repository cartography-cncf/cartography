import base64
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from cartography.intel.aws.eks import transform


def _build_cert_base64(include_ski: bool, include_aki: bool) -> str:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "cartography-test-ca"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Cartography"),
        ]
    )
    now = datetime.now(timezone.utc)
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
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
    cert_der = cert.public_bytes(serialization.Encoding.DER)
    return base64.b64encode(cert_der).decode("utf-8")


def test_transform_eks_clusters_valid_certificate_authority_data():
    ca_data = _build_cert_base64(include_ski=True, include_aki=True)
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

    transformed = transform(cluster_data)

    assert len(transformed) == 1
    cluster = transformed[0]
    assert cluster["certificate_authority_data_present"] is True
    assert cluster["certificate_authority_sha256_fingerprint"] is not None
    assert cluster["certificate_authority_subject"] is not None
    assert cluster["certificate_authority_issuer"] is not None
    assert cluster["certificate_authority_not_before"] is not None
    assert cluster["certificate_authority_not_after"] is not None
    assert cluster["certificate_authority_subject_key_identifier"] is not None
    assert cluster["certificate_authority_authority_key_identifier"] is not None


def test_transform_eks_clusters_missing_certificate_authority_data():
    cluster_data = {
        "dev-cluster": {
            "name": "dev-cluster",
            "arn": "arn:aws:eks:us-east-1:123456789012:cluster/dev-cluster",
            "resourcesVpcConfig": {"endpointPublicAccess": False},
            "logging": {"clusterLogging": []},
        },
    }

    transformed = transform(cluster_data)

    assert len(transformed) == 1
    cluster = transformed[0]
    assert cluster["certificate_authority_data_present"] is False
    assert cluster["certificate_authority_sha256_fingerprint"] is None
    assert cluster["certificate_authority_subject"] is None
    assert cluster["certificate_authority_issuer"] is None
    assert cluster["certificate_authority_not_before"] is None
    assert cluster["certificate_authority_not_after"] is None
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
        transformed = transform(cluster_data)

    assert len(transformed) == 1
    cluster = transformed[0]
    assert cluster["certificate_authority_data_present"] is True
    assert cluster["certificate_authority_sha256_fingerprint"] is None
    assert "beta-cluster" in caplog.text
    assert "Failed to decode EKS cluster certificate authority data" in caplog.text


def test_transform_eks_clusters_certificate_without_aki_ski():
    ca_data = _build_cert_base64(include_ski=False, include_aki=False)
    cluster_data = {
        "staging-cluster": {
            "name": "staging-cluster",
            "arn": "arn:aws:eks:us-east-1:123456789012:cluster/staging-cluster",
            "resourcesVpcConfig": {"endpointPublicAccess": True},
            "logging": {"clusterLogging": []},
            "certificateAuthority": {"data": ca_data},
        },
    }

    transformed = transform(cluster_data)

    assert len(transformed) == 1
    cluster = transformed[0]
    assert cluster["certificate_authority_data_present"] is True
    assert cluster["certificate_authority_sha256_fingerprint"] is not None
    assert cluster["certificate_authority_subject_key_identifier"] is None
    assert cluster["certificate_authority_authority_key_identifier"] is None
