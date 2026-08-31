from cartography.intel.unikraft.account import transform
from cartography.intel.unikraft.account import used_counts

QUOTAS_RESPONSE = {
    "status": "success",
    "data": {
        "quotas": [
            {
                "uuid": "acct-0001",
                "status": "success",
                "message": "",
                "used": {
                    "instances": 4,
                    "volumes": 2,
                    "service_groups": 1,
                },
            },
        ],
    },
}


def test_used_counts_extracts_the_used_dict():
    assert used_counts(QUOTAS_RESPONSE) == {
        "instances": 4,
        "volumes": 2,
        "service_groups": 1,
    }


def test_used_counts_defaults_to_empty_dict_when_missing():
    response = {"status": "success", "data": {"quotas": [{"uuid": "acct-0001"}]}}

    assert used_counts(response) == {}


def test_used_counts_defaults_to_empty_dict_when_no_quotas():
    response = {"status": "success", "data": {"quotas": []}}

    assert used_counts(response) == {}


def test_transform_is_unaffected_by_the_used_field():
    assert transform(QUOTAS_RESPONSE) == {
        "id": "acct-0001",
        "status": "success",
        "message": "",
    }
