"""
AWS ACM Certificate Hygiene

Certificate lifecycle and algorithm checks that the CIS benchmark rules do not
cover. ``cis_aws_iam`` already reports certificates that have already expired;
these rules look at the window before expiry and at the key algorithm.

Both are single-property checks over ``AWSACMCertificate`` and need no data the
AWS sync does not already collect.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AcmCertificateExpiringOutput(Finding):
    """Output model for the certificate expiry check."""

    account_id: str | None = None
    account: str | None = None
    certificate_arn: str | None = None
    domain_name: str | None = None
    status: str | None = None
    expiry_date: str | None = None


# A certificate that has already expired is covered by
# aws_expired_ssl_tls_certificates; this is the 30-day warning window. The
# threshold is fixed rather than configurable because rules carry no
# configuration channel: a per-environment number would have to live in the
# graph, and it does not.
_aws_acm_certificate_expiring_soon_fact = Fact(
    id="aws_acm_certificate_expiring_soon_fact",
    name="ACM certificate near expiry",
    description=(
        "Certificates whose not_after is within 30 days of today or already past. "
        "Non-ISSUED certificates are not excluded; status is returned so callers "
        "can filter them."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(cert:AWSACMCertificate)
    WHERE cert.not_after IS NOT NULL
      AND date(cert.not_after) <= date() + duration({days: 30})
    RETURN a.id AS account_id, a.name AS account, cert.arn AS certificate_arn,
           cert.domainname AS domain_name, cert.status AS status,
           toString(cert.not_after) AS expiry_date
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(cert:AWSACMCertificate)
    WHERE cert.not_after IS NOT NULL
      AND date(cert.not_after) <= date() + duration({days: 30})
    RETURN *
    """,
    cypher_count_query="""
    MATCH (cert:AWSACMCertificate)
    WHERE cert.not_after IS NOT NULL
    RETURN COUNT(cert) AS count
    """,
    asset_label="AWSACMCertificate",
    asset_id_field="certificate_arn",
    identity_fields=("certificate_arn",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_acm_certificate_expiring_soon = Rule(
    id="aws_acm_certificate_expiring_soon",
    name="ACM Certificate Expiring Soon",
    description=(
        "An ACM certificate expires within 30 days or is already expired. An expired "
        "certificate on an internet-facing listener or distribution fails every TLS "
        "handshake, so the service goes dark with no configuration change."
    ),
    output_model=AcmCertificateExpiringOutput,
    facts=(_aws_acm_certificate_expiring_soon_fact,),
    tags=("aws", "certificates", "acm", "availability"),
    version="0.1.0",
)


class AcmCertificateWeakKeyOutput(Finding):
    """Output model for the certificate key algorithm check."""

    account_id: str | None = None
    account: str | None = None
    certificate_arn: str | None = None
    domain_name: str | None = None
    key_algorithm: str | None = None


# ACM reports these as RSA_1024 / EC_prime192v1. Hyphenated spellings are
# matched too so the rule keeps working if the stored form ever changes.
_aws_acm_certificate_weak_key_fact = Fact(
    id="aws_acm_certificate_weak_key_fact",
    name="ACM weak key algorithm",
    description=(
        "Certificates whose key_algorithm is RSA-1024 or an ECDSA P-192 curve. The "
        "secure baseline is RSA-2048+ or ECDSA P-256+."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(cert:AWSACMCertificate)
    WHERE cert.key_algorithm IN [
        'RSA_1024', 'RSA-1024',
        'EC_prime192v1', 'EC_secp192r1', 'EC-prime192v1', 'EC-secp192r1'
    ]
    RETURN a.id AS account_id, a.name AS account, cert.arn AS certificate_arn,
           cert.domainname AS domain_name, cert.key_algorithm AS key_algorithm
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(cert:AWSACMCertificate)
    WHERE cert.key_algorithm IN [
        'RSA_1024', 'RSA-1024',
        'EC_prime192v1', 'EC_secp192r1', 'EC-prime192v1', 'EC-secp192r1'
    ]
    RETURN *
    """,
    cypher_count_query="""
    MATCH (cert:AWSACMCertificate)
    WHERE cert.key_algorithm IS NOT NULL
    RETURN COUNT(cert) AS count
    """,
    asset_label="AWSACMCertificate",
    asset_id_field="certificate_arn",
    identity_fields=("certificate_arn",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_acm_certificate_weak_key = Rule(
    id="aws_acm_certificate_weak_key",
    name="ACM Certificate Weak Key Algorithm",
    description=(
        "An ACM certificate uses a key algorithm below the current baseline: "
        "RSA-1024 or ECDSA P-192. Both are considered deprecated by NIST and are "
        "rejected by modern clients."
    ),
    output_model=AcmCertificateWeakKeyOutput,
    facts=(_aws_acm_certificate_weak_key_fact,),
    tags=("aws", "certificates", "acm", "cryptography"),
    version="0.1.0",
)
