"""
AWS CloudFront viewer TLS configuration

Distributions served on the default cloudfront.net certificate, custom
certificates on dedicated IPs instead of SNI, and minimum protocol versions
below TLS 1.3.

The TLS 1.3 rule is a post-quantum control. AWS supports X25519MLKEM768 and
SecP256r1MLKEM768 hybrid key exchange, and quantum-safe key exchange is only
available with TLS 1.3 - TLS 1.2 and earlier do not support it. A minimum
below TLS 1.3 therefore permits a classical-only handshake. Distributions on
the default certificate cannot select TLS-1.3-only policies, so
cloudfront_default_certificate is returned for those rows to be filtered.
Note TLSv1.2_2025 exists and is not TLS 1.3: it satisfies neither.

No collector change is required: every property and relationship used
here is synced by the existing CloudFront module. All rules are
EXPERIMENTAL until validated against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsCloudfrontCustomSslCertificateOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    distribution_id: str | None = None
    distribution_arn: str | None = None
    cloudfront_default_certificate: bool | None = None
    acm_certificate_arn: str | None = None
    iam_certificate_id: str | None = None


_aws_cloudfront_custom_ssl_certificate_fact = Fact(
    id="aws_cloudfront_custom_ssl_certificate_fact",
    name="CloudFront default certificate",
    description="Distributions with cloudfront_default_certificate=true.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true AND d.cloudfront_default_certificate = true
        RETURN a.id AS account_id, a.name AS account, d.distribution_id AS distribution_id,
               d.arn AS distribution_arn,
               d.cloudfront_default_certificate AS cloudfront_default_certificate,
               d.acm_certificate_arn AS acm_certificate_arn,
               d.iam_certificate_id AS iam_certificate_id

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true AND d.cloudfront_default_certificate = true
        RETURN a.id AS account_id, a.name AS account, d.distribution_id AS distribution_id,
               d.arn AS distribution_arn,
               d.cloudfront_default_certificate AS cloudfront_default_certificate,
               d.acm_certificate_arn AS acm_certificate_arn,
               d.iam_certificate_id AS iam_certificate_id

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true AND d.cloudfront_default_certificate = true
        RETURN a.id AS account_id, a.name AS account, d.distribution_id AS distribution_id,
               d.arn AS distribution_arn,
               d.cloudfront_default_certificate AS cloudfront_default_certificate,
               d.acm_certificate_arn AS acm_certificate_arn,
               d.iam_certificate_id AS iam_certificate_id

    """,
    asset_label="AWSCloudFrontDistribution",
    asset_id_field="distribution_id",
    identity_fields=("account_id", "account", "distribution_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudfront_custom_ssl_certificate = Rule(
    id="aws_cloudfront_custom_ssl_certificate",
    name="CloudFront Custom SSL Certificate",
    description="CloudFront distribution uses the default *.cloudfront.net certificate (cloudfront_default_certificate=true) for viewer connections instead of a custom ACM/IAM certificate. Enabled distributions only.",
    output_model=AwsCloudfrontCustomSslCertificateOutput,
    facts=(_aws_cloudfront_custom_ssl_certificate_fact,),
    tags=("security", "cloudfront", "encryption", "cspm"),
    version="0.1.0",
)


class AwsCloudfrontHttpsSniOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    distribution_id: str | None = None
    domain_name: str | None = None
    ssl_support_method: str | None = None
    cloudfront_default_certificate: bool | None = None


_aws_cloudfront_https_sni_fact = Fact(
    id="aws_cloudfront_https_sni_fact",
    name="Custom certificate not served via SNI",
    description="Custom-certificate distributions whose ssl_support_method is not 'sni-only'.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true
          AND d.cloudfront_default_certificate = false
          AND (d.ssl_support_method IS NULL OR d.ssl_support_method <> 'sni-only')
        RETURN a.id AS account_id, a.name AS account,
               d.distribution_id AS distribution_id, d.domain_name AS domain_name,
               d.ssl_support_method AS ssl_support_method,
               d.cloudfront_default_certificate AS cloudfront_default_certificate

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true
          AND d.cloudfront_default_certificate = false
          AND (d.ssl_support_method IS NULL OR d.ssl_support_method <> 'sni-only')
        RETURN a.id AS account_id, a.name AS account,
               d.distribution_id AS distribution_id, d.domain_name AS domain_name,
               d.ssl_support_method AS ssl_support_method,
               d.cloudfront_default_certificate AS cloudfront_default_certificate

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true
          AND d.cloudfront_default_certificate = false
          AND (d.ssl_support_method IS NULL OR d.ssl_support_method <> 'sni-only')
        RETURN a.id AS account_id, a.name AS account,
               d.distribution_id AS distribution_id, d.domain_name AS domain_name,
               d.ssl_support_method AS ssl_support_method,
               d.cloudfront_default_certificate AS cloudfront_default_certificate

    """,
    asset_label="AWSCloudFrontDistribution",
    asset_id_field="distribution_id",
    identity_fields=("account_id", "account", "distribution_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudfront_https_sni = Rule(
    id="aws_cloudfront_https_sni",
    name="CloudFront Custom Certificate Without SNI",
    description="CloudFront distribution using a custom certificate (cloudfront_default_certificate=false) but ssl_support_method is not 'sni-only' (dedicated-IP 'vip' instead of SNI). Dedicated-IP SSL incurs extra cost and is unnecessary for modern clients. Enabled distributions only.",
    output_model=AwsCloudfrontHttpsSniOutput,
    facts=(_aws_cloudfront_https_sni_fact,),
    tags=("cloudfront", "hygiene", "cspm", "low"),
    version="0.1.0",
)


class AwsCloudfrontPqcTlsPolicyOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    distribution_id: str | None = None
    domain_name: str | None = None
    minimum_protocol_version: str | None = None
    cloudfront_default_certificate: bool | None = None


_aws_cloudfront_pqc_tls_policy_fact = Fact(
    id="aws_cloudfront_pqc_tls_policy_fact",
    name="Distribution without TLSv1.3_2025 policy",
    description="Distributions whose minimum_protocol_version is not 'TLSv1.3_2025'.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true
          AND (d.minimum_protocol_version IS NULL
               OR d.minimum_protocol_version <> 'TLSv1.3_2025')
        RETURN a.id AS account_id, a.name AS account,
               d.distribution_id AS distribution_id, d.domain_name AS domain_name,
               d.minimum_protocol_version AS minimum_protocol_version,
               d.cloudfront_default_certificate AS cloudfront_default_certificate

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true
          AND (d.minimum_protocol_version IS NULL
               OR d.minimum_protocol_version <> 'TLSv1.3_2025')
        RETURN a.id AS account_id, a.name AS account,
               d.distribution_id AS distribution_id, d.domain_name AS domain_name,
               d.minimum_protocol_version AS minimum_protocol_version,
               d.cloudfront_default_certificate AS cloudfront_default_certificate

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSCloudFrontDistribution)
        WHERE d.enabled = true
          AND (d.minimum_protocol_version IS NULL
               OR d.minimum_protocol_version <> 'TLSv1.3_2025')
        RETURN a.id AS account_id, a.name AS account,
               d.distribution_id AS distribution_id, d.domain_name AS domain_name,
               d.minimum_protocol_version AS minimum_protocol_version,
               d.cloudfront_default_certificate AS cloudfront_default_certificate

    """,
    asset_label="AWSCloudFrontDistribution",
    asset_id_field="distribution_id",
    identity_fields=("account_id", "account", "distribution_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudfront_pqc_tls_policy = Rule(
    id="aws_cloudfront_pqc_tls_policy",
    name="CloudFront Without Post-Quantum TLS Policy",
    description="CloudFront distribution whose minimum_protocol_version is not 'TLSv1.3_2025', allowing TLS 1.2 fallback to classical (non-post-quantum) key exchange. NOTE: distributions using the default CloudFront certificate cannot select this policy; cloudfront_default_certificate is returned so those rows can be filtered downstream. Enabled distributions only.",
    output_model=AwsCloudfrontPqcTlsPolicyOutput,
    facts=(_aws_cloudfront_pqc_tls_policy_fact,),
    tags=("cloudfront", "hygiene", "cspm", "low"),
    version="0.1.0",
)
