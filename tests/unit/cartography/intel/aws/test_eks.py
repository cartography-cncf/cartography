import base64
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from cartography.intel.aws import eks


def _build_cert_base64(
    include_ski: bool,
    include_aki: bool,
    encoding: serialization.Encoding,
    not_valid_after: datetime,
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
    cert_bytes = cert.public_bytes(encoding)
    return base64.b64encode(cert_bytes).decode("utf-8")


def test_transform_eks_clusters_valid_der_certificate_authority_data(monkeypatch):
    fake_now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(eks, "_now_utc", lambda: fake_now)
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
    assert cluster["certificate_authority_data_present"] is True
    assert cluster["certificate_authority_parse_status"] == "parsed"
    assert cluster["certificate_authority_parse_error"] is None
    assert cluster["certificate_authority_sha256_fingerprint"] is not None
    assert cluster["certificate_authority_subject"] is not None
    assert cluster["certificate_authority_issuer"] is not None
    assert cluster["certificate_authority_not_before"] is not None
    assert cluster["certificate_authority_not_after"] is not None
    assert cluster["certificate_authority_subject_key_identifier"] is not None
    assert cluster["certificate_authority_authority_key_identifier"] is not None
    assert cluster["certificate_authority_expired"] is False
    assert cluster["certificate_authority_days_until_expiry"] == 365


def test_transform_eks_clusters_valid_pem_certificate_authority_data(monkeypatch):
    fake_now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(eks, "_now_utc", lambda: fake_now)
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
    assert cluster["certificate_authority_expired"] is True
    assert cluster["certificate_authority_days_until_expiry"] == -2


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
    assert cluster["certificate_authority_expired"] is None
    assert cluster["certificate_authority_days_until_expiry"] is None


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
    assert "invalid-cert-cluster" in caplog.text
    assert "status=invalid_certificate" in caplog.text
