import re


def get_application_id(name: str, vendor: str) -> str:
    name_normalized = name.strip().lower().replace(" ", "_")
    vendor_normalized = vendor.strip().lower().replace(" ", "_")
    name_normalized = re.sub(r"[^\w]", "", name_normalized)
    vendor_normalized = re.sub(r"[^\w\s]", "", vendor_normalized)
    return f"{vendor_normalized}:{name_normalized}"
