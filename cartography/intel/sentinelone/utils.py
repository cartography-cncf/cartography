import re


def get_application_id(name: str, vendor: str) -> str:
    name_normalized = name.strip().lower().replace(" ", "_")
    vendor_normalized = vendor.strip().lower().replace(" ", "_")
    name_normalized = re.sub(r"[^\w]", "", name_normalized)
    vendor_normalized = re.sub(r"[^\w\s]", "", vendor_normalized)
    return f"{vendor_normalized}:{name_normalized}"


def get_application_version_id(name: str, vendor: str, version: str) -> str:
    """
    Generate a unique identifier for an application version
    :param name: Application name
    :param vendor: Application vendor
    :param version: Application version
    :return: Unique identifier for the application version
    """
    app_id = get_application_id(name, vendor)
    version_normalized = version.strip().lower().replace(" ", "_")
    version_normalized = re.sub(r"[^\w.-]", "", version_normalized)
    return f"{app_id}:{version_normalized}"
