import pytest

from cartography.intel.microsoft.entra.domains import domain_name_of


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
