"""Shape returned by cartography.intel.modal.util.get_workspace().

Values mirror a real response captured from modal 1.5.3.
"""

MODAL_WORKSPACE = {
    "id": "ac-DyLbE2VtEfgvSEhzMQAOcP",
    "name": "example-workspace",
    "slug": "example-workspace",
    "synced_with_token_id": "ak-4pE5t96YiNM0svmOjIet7z",
    "synced_with_token_name": "cartography",
    "synced_with_principal_type": "user",
    "synced_with_principal_id": "us-ydIZVCWluEtzFTbpJvjHcK",
    "synced_with_principal_name": "example-workspace",
    # Modal API tokens do not expire, so this is None in practice.
    "synced_with_token_expires_at": None,
}
