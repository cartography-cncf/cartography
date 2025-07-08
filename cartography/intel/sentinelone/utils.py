def get_application_id(name: str, vendor: str) -> str:
    # Normalize by replacing spaces with underscores and converting to lowercase
    vendor_normalized = vendor.replace(" ", "_").lower()
    name_normalized = name.replace(" ", "_").lower()
    return f"{vendor_normalized}:{name_normalized}"
