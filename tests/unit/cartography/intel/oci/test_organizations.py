from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import mock_open

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
    assert profiles[0] == 'DEFAULT'


def test_get_oci_accounts_from_config():
    organizations.test_get_oci_profile_names_from_config = MagicMock()
    organizations.test_get_oci_profile_names_from_config.return_value = ['DEFAULT']
    x = organizations.get_oci_accounts_from_config()
    assert x == {}