from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# Facts
_missing_mfa_ontology = Fact(
    id="missing-mfa-ontology",
    name="UserAccount nodes with MFA explicitly disabled",
    description=(
        "Active user accounts whose `_ont_has_mfa` ontology field is "
        "explicitly false. Built on the cross-cloud `UserAccount` "
        "semantic label so it covers every provider that maps the "
        "`has_mfa` ontology field, including AWS (derived from the "
        "`:MFA_DEVICE` edge by the ontology AWS-user projection job). "
        "Providers that do not expose an MFA flag are intentionally "
        "skipped (NULL means unknown, not missing)."
    ),
    module=Module.CROSS_CLOUD,
    cypher_query="""
    MATCH (a:UserAccount)
    WHERE a._ont_has_mfa = false
      AND COALESCE(a._ont_active, true)
      AND NOT COALESCE(a._ont_inactive, false)
    RETURN
        a.id AS id,
        a._ont_email AS email,
        a._ont_firstname AS firstname,
        a._ont_lastname AS lastname,
        a._ont_source AS status
    ORDER BY id
    """,
    cypher_visual_query="""
    MATCH (a:UserAccount)
    WHERE a._ont_has_mfa = false
      AND COALESCE(a._ont_active, true)
      AND NOT COALESCE(a._ont_inactive, false)
    RETURN a
    """,
    cypher_count_query="""
    MATCH (a:UserAccount)
    WHERE a._ont_has_mfa IS NOT NULL
      AND COALESCE(a._ont_active, true)
      AND NOT COALESCE(a._ont_inactive, false)
    RETURN COUNT(a) AS count
    """,
    asset_id_field="id",
    maturity=Maturity.EXPERIMENTAL,
)


# Rule
class MFARuleOutput(Finding):
    email: str | None = None
    id: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    status: str | None = None


missing_mfa_rule = Rule(
    id="mfa-missing",
    name="User accounts missing MFA",
    description=(
        "Detects user accounts that do not have Multi-Factor Authentication "
        "enabled, using the cross-cloud `_ont_has_mfa` ontology field on "
        "`UserAccount` nodes."
    ),
    output_model=MFARuleOutput,
    tags=("identity",),
    facts=(_missing_mfa_ontology,),
    version="0.3.0",
    frameworks=(iso27001_annex_a("8.5"),),
)
