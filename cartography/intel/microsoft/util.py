from cartography.config import Config
from cartography.intel.microsoft.resources import RESOURCE_FUNCTIONS


def parse_and_validate_microsoft_requested_syncs(
    microsoft_requested_syncs: str,
) -> list[str]:
    validated_resources: list[str] = []
    for resource in microsoft_requested_syncs.split(","):
        resource = resource.strip()

        if resource in RESOURCE_FUNCTIONS:
            validated_resources.append(resource)
        else:
            valid_syncs = ", ".join(RESOURCE_FUNCTIONS)
            raise ValueError(
                "Error parsing `microsoft-requested-syncs`. You specified "
                f'"{microsoft_requested_syncs}". Please check that your string is '
                'formatted properly. Example valid input looks like "users,groups" '
                'or "groups, intune". Our full list of valid values is: '
                f"{valid_syncs}.",
            )
    return validated_resources


def requested_microsoft_syncs(config: Config) -> set[str] | None:
    """Return the requested Microsoft resources, or None to sync everything."""
    if not config.microsoft_requested_syncs:
        return None
    return set(
        parse_and_validate_microsoft_requested_syncs(config.microsoft_requested_syncs)
    )


def normalize_azure_ad_device_id(value: str | None) -> str | None:
    """Normalize the Entra device join key; empty and zero IDs cannot identify a device."""
    normalized = (value or "").lower() or None
    return normalized if normalized != "00000000-0000-0000-0000-000000000000" else None
