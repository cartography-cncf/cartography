# flake8: noqa
MOCK_LOCATIONS = [
    {"locationId": "global"},
    {"locationId": "us-central1"},
]

MOCK_KEY_RINGS = [
    {
        "name": "projects/test-project/locations/global/keyRings/my-global-keyring",
        # Other potential fields omitted for brevity
    },
    {
        "name": "projects/test-project/locations/us-central1/keyRings/my-regional-keyring",
    },
]

# Keys for the 'global' keyring
MOCK_CRYPTO_KEYS_GLOBAL = [
    {
        "name": "projects/test-project/locations/global/keyRings/my-global-keyring/cryptoKeys/key-one",
        "primary": {"state": "ENABLED"},
        "purpose": "ENCRYPT_DECRYPT",
        "rotationPeriod": "7776000s",  # 90 days
    },
]

# Keys for the 'us-central1' keyring
MOCK_CRYPTO_KEYS_REGIONAL = [
    {
        "name": "projects/test-project/locations/us-central1/keyRings/my-regional-keyring/cryptoKeys/key-two",
        "primary": {"state": "ENABLED"},
        "purpose": "ASYMMETRIC_SIGN",
        "rotationPeriod": None,
    },
    {
        "name": "projects/test-project/locations/us-central1/keyRings/my-regional-keyring/cryptoKeys/key-three",
        "primary": {"state": "DISABLED"},
        "purpose": "ENCRYPT_DECRYPT",
    },
]

# Define a helper mapping for the test to easily return the correct keys per ring
MOCK_KEYS_BY_RING = {
    "projects/test-project/locations/global/keyRings/my-global-keyring": MOCK_CRYPTO_KEYS_GLOBAL,
    "projects/test-project/locations/us-central1/keyRings/my-regional-keyring": MOCK_CRYPTO_KEYS_REGIONAL,
}
