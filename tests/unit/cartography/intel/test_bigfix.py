from unittest.mock import call

import pytest
from pytest_mock import MockerFixture

from cartography.intel.bigfix import computers
from tests.data.bigfix.computers import BF_COMPUTER_DETAILS
from tests.data.bigfix.computers import BF_COMPUTER_LIST


@pytest.mark.parametrize(  # type: ignore[misc]
    ("list_xml", "expected_ids"),
    [
        pytest.param(
            '<BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:noNamespaceSchemaLocation="BESAPI.xsd"/>',
            [],
            id="empty-with-attributes",
        ),
        pytest.param("<BESAPI/>", [], id="empty-without-attributes"),
        pytest.param(
            "<BESAPI><Computer><ID>223212</ID></Computer></BESAPI>",
            ["223212"],
            id="single-computer",
        ),
        pytest.param(BF_COMPUTER_LIST, ["223212", "302143", "540385"], id="multiple"),
    ],
)
def test_get_computers(
    mocker: MockerFixture, list_xml: str, expected_ids: list[str]
) -> None:
    # Arrange
    api_url = "https://bigfixroot.example.com"
    headers: dict[str, str] = {}
    mocker.patch.object(computers, "_get_computer_list_raw_xml", return_value=list_xml)
    get_details_xml = mocker.patch.object(
        computers, "_get_computer_details_raw_xml", side_effect=BF_COMPUTER_DETAILS
    )

    # Act
    result = computers.get(api_url, headers, computers.DEFAULT_SUPPORTED_KEYS)

    # Assert
    assert [computer["ID"] for computer in result] == expected_ids
    assert get_details_xml.call_args_list == [
        call(api_url, headers, computer_id) for computer_id in expected_ids
    ]


def test_get_computer_list_rejects_unexpected_response(mocker: MockerFixture) -> None:
    # Arrange
    mocker.patch.object(
        computers,
        "_get_computer_list_raw_xml",
        return_value="<BESAPI><Error>Unexpected response</Error></BESAPI>",
    )

    # Act and assert
    with pytest.raises(KeyError, match="Computer"):
        computers.get_computer_list("https://bigfixroot.example.com", {})
