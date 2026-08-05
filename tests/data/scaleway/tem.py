from scaleway.tem.v1alpha1 import Domain
from scaleway.tem.v1alpha1.types import DomainStatus

SCALEWAY_TEM_DOMAINS = [
    Domain(
        id="d0e1f2a3-0001-4000-8000-000000000001",
        organization_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        project_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        name="alerts.example.com",
        status=DomainStatus.CHECKED,
        region="fr-par",
        spf_config="",
        dkim_config="",
        autoconfig=False,
    ),
    Domain(
        id="d0e1f2a3-0002-4000-8000-000000000002",
        organization_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        project_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        name="news.example.com",
        status=DomainStatus.PENDING,
        region="nl-ams",
        spf_config="",
        dkim_config="",
        autoconfig=False,
    ),
]
