from unittest.mock import mock_open
from unittest.mock import patch

from cartography.intel.oci import organizations

CRED_DATA = """[DEFAULT]
user=ocid1.user.oc1..123
fingerprint=12:34
tenancy=ocid1.tenancy.oc1..1234
region=us-phoenix-1
key_file=/path/to/file.pem
"""


@patch("builtins.open", new_callable=mock_open, read_data=CRED_DATA)
def test_get_oci_profile_names_from_config(mock_file):
    profiles = organizations.get_oci_profile_names_from_config()
    assert isinstance(profiles, list)
    assert profiles[0] == "DEFAULT"


def test_get_oci_accounts_from_config():
    patch_func = "cartography.intel.oci.organizations.get_oci_profile_names_from_config"
    with patch(patch_func, return_value=["DEFAULT"]) as profile_names:
        oci_results = organizations.get_oci_accounts_from_config()
        profile_names.assert_called_once()
        assert oci_results == {}
