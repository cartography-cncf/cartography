WIF_PRINCIPAL_PREFIXES = (
    "principal://iam.googleapis.com/",
    "principalSet://iam.googleapis.com/",
)


def is_wif_external_principal(principal: str) -> bool:
    return principal.startswith(WIF_PRINCIPAL_PREFIXES)
