import base64
import ssl
from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.kubernetes import util


def _fake_boto3_session(presigned_url="https://sts.example/presigned"):
    session = MagicMock()
    sts = MagicMock()
    sts.generate_presigned_url.return_value = presigned_url
    session.client.return_value = sts
    return session, sts


def test_get_eks_token_format():
    # The EKS token is "k8s-aws-v1." + base64url(presigned STS URL), unpadded,
    # and the cluster-id header is registered on the GetCallerIdentity request.
    presigned = "https://sts.us-east-1.amazonaws.com/?Action=GetCallerIdentity&X-Amz=x"
    session, sts = _fake_boto3_session(presigned)

    token = util._get_eks_token("my-cluster", session)

    sts.generate_presigned_url.assert_called_once()
    assert sts.generate_presigned_url.call_args.args[0] == "get_caller_identity"
    sts.meta.events.register.assert_called_once()
    assert (
        sts.meta.events.register.call_args.args[0]
        == "before-sign.sts.GetCallerIdentity"
    )
    assert token.startswith("k8s-aws-v1.")
    assert "=" not in token  # base64url padding stripped
    decoded = base64.urlsafe_b64decode(token[len("k8s-aws-v1.") :] + "==").decode()
    assert decoded == presigned


def _self_signed_ca_pem():
    import datetime

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test-ca")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime(2020, 1, 1))
        .not_valid_after(datetime.datetime(2040, 1, 1))
        .sign(key, hashes.SHA256())
    )
    return cert.public_bytes(serialization.Encoding.PEM).decode()


def test_build_eks_api_client_clears_strict_but_keeps_verification():
    api_client = util._build_eks_api_client(
        "https://eks.example", _self_signed_ca_pem(), "tok"
    )

    ctx = api_client.rest_client.pool_manager.connection_pool_kw["ssl_context"]
    # strict subflag cleared...
    assert not (ctx.verify_flags & ssl.VERIFY_X509_STRICT)
    # ...but full verification stays ON (this is not InsecureSkipVerify)
    assert ctx.verify_mode == ssl.CERT_REQUIRED


@patch("cartography.intel.kubernetes.util.K8sClient")
@patch("cartography.intel.kubernetes.util._build_eks_api_client")
@patch("cartography.intel.kubernetes.util._get_eks_token", return_value="tok")
def test_get_eks_k8s_clients_uses_boto3_describe(
    mock_token, mock_build, mock_client_cls
):
    session = MagicMock()
    session.region_name = "us-east-1"
    eks = MagicMock()
    eks.describe_cluster.return_value = {
        "cluster": {
            "endpoint": "https://eks.example",
            "certificateAuthority": {"data": base64.b64encode(b"ca").decode()},
            "arn": "arn:aws:eks:us-east-1:123:cluster/c1",
        }
    }
    session.client.return_value = eks

    util.get_eks_k8s_clients(["c1"], session)

    eks.describe_cluster.assert_called_once_with(name="c1")
    mock_token.assert_called_once_with("c1", session)
    # client built with the boto3-derived api_client, external_id = cluster ARN
    _, kwargs = mock_client_cls.call_args
    assert kwargs["external_id"] == "arn:aws:eks:us-east-1:123:cluster/c1"
    assert kwargs["api_client"] is mock_build.return_value
