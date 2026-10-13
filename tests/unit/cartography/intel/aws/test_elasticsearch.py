import cartography.intel.aws.elasticsearch


def test_transform_es_domains_calculates_internet_exposure():
    domains = [
        {
            "DomainId": "public-domain",
            "Endpoint": "search-public.example.com",
            "AccessPolicies": (
                '{"Version":"2012-10-17","Statement":[{"Effect":"Allow",'
                '"Principal":"*","Action":"es:*","Resource":"*"}]}'
            ),
        },
        {
            "DomainId": "private-domain",
            "Endpoint": "search-private.example.com",
            "AccessPolicies": '{"Version":"2012-10-17","Statement":[]}',
        },
    ]

    transformed = cartography.intel.aws.elasticsearch._transform_es_domains(domains)

    assert {
        domain["DomainId"]: domain["exposed_internet"] for domain in transformed
    } == {
        "public-domain": True,
        "private-domain": False,
    }
