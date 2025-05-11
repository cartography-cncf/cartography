from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.oci import iam

JSON_OCI_OBJECT = {
    "capabilities": {
        "can_use_api_keys": True,
        "can_use_auth_tokens": True,
    },
    "compartment_id": "ocid1.tenancy.oc1..123",
}

USER_OCI_OBJECT = """[{
  "capabilities": {
    "can_use_api_keys": true
  },
  "id": "ocid1.user.oc1..1234",
  "lifecycle_state": "ACTIVE",
  "name": "none@none.com"
}]"""

GROUP_OCI_OBJECT = """[{
  "lifecycle_state": "ACTIVE",
  "name": "Administrators"
}]"""


GROUP_MEMBER_OCI_OBJECT = """[{
  "group_id": "ocid1.group.oc1..123",
  "user_id": "ocid1.user.oc1..1234"
}]"""

POLICY_OCI_OBJECT = """[{
  "name": "dev_storage_use",
  "statements": [
    "Allow group Administrators to read buckets in compartment dev"
  ]
}]"""

REGION_OCI_OBJECT = """[{
  "is_home_region": true,
  "region_key": "PHX",
  "region_name": "us-phoenix-1",
  "status": "READY"
}]"""


def test_get_compartment_list_data_recurse():
    list_call_get_all_results = MagicMock()
    list_call_get_all_results.data = None
    iam_obj = MagicMock()
    iam_obj.list_compartments.return_value = []
    with patch(
        "oci.pagination.list_call_get_all_results",
        return_value=list_call_get_all_results,
    ) as page_results:
        compartment_list = {"Compartments": ""}
        compartment_id = "ocid1.compartment.oc1..aaaaaaaakl52gpiymzh46mx5gjrtqgdnzpbhwflj2il5h5r7awj5qlpo2vra"
        iam.get_compartment_list_data_recurse(iam_obj, compartment_list, compartment_id)
        page_results.assert_called_once()


def test_get_compartment_list_data():
    iam_obj = MagicMock()
    iam_obj.list_compartments.return_value = []
    patch_func = "cartography.intel.oci.iam.get_compartment_list_data_recurse"
    with patch(patch_func, return_value=JSON_OCI_OBJECT) as page_results:
        output = iam.get_compartment_list_data(iam_obj, None)
        page_results.assert_called_once()
        assert output == {"Compartments": ""}


def test_get_user_list_data():
    iam_obj = MagicMock()
    iam_obj.list_users.return_value = []
    resp_obj = MagicMock()
    resp_obj.data = USER_OCI_OBJECT
    with patch(
        "oci.pagination.list_call_get_all_results",
        return_value=resp_obj,
    ) as page_results:
        user_list = iam.get_user_list_data(iam_obj, "")
        page_results.assert_called_once()
        assert "Users" in user_list.keys()
        assert user_list["Users"][0]["name"] == "none@none.com"


def test_get_group_list_data():
    iam_obj = MagicMock()
    iam_obj.list_groups.return_value = []
    resp_obj = MagicMock()
    resp_obj.data = GROUP_OCI_OBJECT
    with patch(
        "oci.pagination.list_call_get_all_results",
        return_value=resp_obj,
    ) as page_results:
        group_list = iam.get_group_list_data(iam_obj, "")
        page_results.assert_called_once()
        assert "Groups" in group_list.keys()
        assert group_list["Groups"][0]["name"] == "Administrators"


def test_get_group_membership_data():
    iam_obj = MagicMock()
    iam_obj.list_groups.return_value = []
    resp_obj = MagicMock()
    resp_obj.data = GROUP_MEMBER_OCI_OBJECT
    with patch(
        "oci.pagination.list_call_get_all_results",
        return_value=resp_obj,
    ) as page_results:
        group_member_list = iam.get_group_membership_data(iam_obj, "", "")
        page_results.assert_called_once()
        assert "GroupMemberships" in group_member_list.keys()
        assert (
            group_member_list["GroupMemberships"][0]["user-id"]
            == "ocid1.user.oc1..1234"
        )


def test_get_policy_list_data():
    iam_obj = MagicMock()
    iam_obj.list_groups.return_value = []
    resp_obj = MagicMock()
    resp_obj.data = POLICY_OCI_OBJECT
    with patch(
        "oci.pagination.list_call_get_all_results",
        return_value=resp_obj,
    ) as page_results:
        policy_list = iam.get_policy_list_data(iam_obj, "")
        page_results.assert_called_once()
        assert "Policies" in policy_list.keys()
        assert policy_list["Policies"][0]["name"] == "dev_storage_use"


def test_get_region_subscriptions_list_data():
    iam_obj = MagicMock()
    iam_obj.list_groups.return_value = []
    resp_obj = MagicMock()
    resp_obj.data = REGION_OCI_OBJECT
    with patch(
        "oci.pagination.list_call_get_all_results",
        return_value=resp_obj,
    ) as page_results:
        region_subscribe_list = iam.get_region_subscriptions_list_data(iam_obj, "")
        page_results.assert_called_once()
        assert "RegionSubscriptions" in region_subscribe_list.keys()
        assert region_subscribe_list["RegionSubscriptions"][0]["region-key"] == "PHX"
