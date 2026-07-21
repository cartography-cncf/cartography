from cartography.intel.scaleway.tem.tem import transform_domains
from tests.data.scaleway.tem import SCALEWAY_TEM_DOMAINS

PROJECT = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


def test_transform_domains():
    result = transform_domains(SCALEWAY_TEM_DOMAINS)
    assert PROJECT in result
    domains = result[PROJECT]
    assert len(domains) == 2


def test_transform_domains_fields():
    result = transform_domains(SCALEWAY_TEM_DOMAINS)
    domain = result[PROJECT][0]
    assert domain["id"] == "d0e1f2a3-0001-4000-8000-000000000001"
    assert domain["name"] == "alerts.example.com"
    assert domain["status"] == "checked"
    assert domain["project_id"] == PROJECT


def test_transform_domains_skips_missing_project():
    # Simulate a domain with no project_id.
    from scaleway.tem.v1alpha1 import Domain
    from scaleway.tem.v1alpha1.types import DomainStatus

    no_project = Domain(
        id="orphan",
        organization_id=PROJECT,
        project_id=None,
        name="orphan.example.com",
        status=DomainStatus.PENDING,
        region="fr-par",
        spf_config="",
        dkim_config="",
        autoconfig=False,
    )
    result = transform_domains([no_project])
    assert result == {}
