import pytest
from msgraph.generated.models.domain import Domain

from cartography.intel.microsoft.entra.domains import domain_name_of
from cartography.intel.microsoft.entra.domains import transform_domains


@pytest.mark.parametrize(  # type: ignore[misc]
    ("user_principal_name", "expected"),
    [
        pytest.param("Alice@Contoso.COM", "contoso.com", id="lowercased"),
        pytest.param(
            "vendor_example.com#EXT#@contoso.onmicrosoft.com",
            "contoso.onmicrosoft.com",
            id="guest-uses-the-tenant-domain-after-the-last-at",
        ),
        pytest.param("no-domain", None, id="no-at-sign"),
        pytest.param("", None, id="empty"),
        pytest.param(None, None, id="missing"),
    ],
)
def test_domain_name_of(user_principal_name: str | None, expected: str | None) -> None:
    # Act and assert
    assert domain_name_of(user_principal_name) == expected


def test_transform_domains_rejects_a_domain_without_an_id() -> None:
    """A dropped record would let cleanup delete a domain that still exists."""
    # Act and assert
    with pytest.raises(ValueError, match="domain without an id"):
        transform_domains([Domain(id="contoso.com"), Domain()], "tenant")
