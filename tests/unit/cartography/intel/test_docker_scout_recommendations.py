from cartography.intel.docker_scout.scanner import parse_recommendation_raw
from cartography.intel.docker_scout.scanner import sync_from_file
from cartography.intel.docker_scout.scanner import transform_public_image_tags
from tests.data.docker_scout.mock_data import MOCK_ECR_RECOMMENDATION_RAW


def test_parse_recommendation_raw_parses_short_target_digest() -> None:
    parsed = parse_recommendation_raw(MOCK_ECR_RECOMMENDATION_RAW)

    assert parsed["target"] == {
        "image": "registry.example.test/example/app:1.2.3",
        "digest": "ecr000000000000",
    }
    assert parsed["base_image"]["name"] == "node"
    assert parsed["base_image"]["tag"] == "25-alpine"
    assert parsed["base_image"]["alternative_tags"] == [
        "25-alpine3.23",
        "alpine",
        "alpine3.23",
        "current-alpine",
        "current-alpine3.23",
    ]
    assert "current-alpine3.23" in parsed["recommendations"]


def test_transform_public_image_tags_returns_built_from_and_recommendation_rows() -> (
    None
):
    parsed = parse_recommendation_raw(MOCK_ECR_RECOMMENDATION_RAW)

    transformed = transform_public_image_tags(parsed, "python:3.12-slim")
    rows_by_id = {
        row["id"]: row for row in transformed if "built_from_public_image_id" in row
    }
    recommendation_rows = {
        row["id"]: row
        for row in transformed
        if "recommended_for_public_image_id" in row
    }

    assert (
        rows_by_id["node:25-alpine"]["built_from_public_image_id"] == "python:3.12-slim"
    )
    assert recommendation_rows["node:25-alpine"]["recommended_for_public_image_id"] == (
        "python:3.12-slim"
    )
    assert recommendation_rows["node:25-alpine"]["benefits"] == [
        "Same OS detected",
        "Minor runtime version update",
        "Newer image for same tag",
        "Image contains 9 fewer packages",
        "Tag was pushed more recently",
        "Image has similar size",
        "Image introduces no new vulnerability but removes 2",
    ]
    assert recommendation_rows["node:25-alpine"]["fix_critical"] is None
    assert recommendation_rows["node:25-alpine"]["fix_high"] == 2
    assert recommendation_rows["node:25-alpine"]["fix_medium"] is None
    assert recommendation_rows["node:25-alpine"]["fix_low"] is None
    assert recommendation_rows["node:slim"]["is_slim"] is True
    assert "digest" not in rows_by_id["node:25-alpine"]
    assert "digest" not in recommendation_rows["node:25-alpine"]


def test_parse_recommendation_raw_supports_crlf_and_registry_ports() -> None:
    raw_report = (
        MOCK_ECR_RECOMMENDATION_RAW.replace(
            "registry.example.test/example/app:1.2.3",
            "registry.example.test:5000/example/app:1.2.3",
        )
        .replace(
            "Base image is  node:25-alpine",
            "Base image is  registry.example.test:5000/node:25-alpine",
        )
        .replace("\n", "\r\n")
    )

    parsed = parse_recommendation_raw(raw_report)

    assert parsed["target"]["image"] == "registry.example.test:5000/example/app:1.2.3"
    assert parsed["base_image"]["name"] == "registry.example.test:5000/node"
    assert parsed["base_image"]["tag"] == "25-alpine"


def test_parse_recommendation_raw_normalizes_wrapped_supported_tags() -> None:
    wrapped_report = MOCK_ECR_RECOMMENDATION_RAW.replace(
        "supported tag(s) `25-alpine3.23`, `alpine`, `alpine3.23`, `current-alpine`, `current-alpine3.23`. If you want to display recommendations",
        "\n".join(
            [
                "      │ This image version is available for the following supported tag(s) `25-alpine3.23`,",
                "      │ `alpine`, `alpine3.23`,",
                "      │ `current-alpine`, `current-alpine3.23`. If you want to display recommendations",
            ]
        ),
    )

    parsed = parse_recommendation_raw(wrapped_report)

    assert parsed["base_image"]["alternative_tags"] == [
        "25-alpine3.23",
        "alpine",
        "alpine3.23",
        "current-alpine",
        "current-alpine3.23",
    ]


def test_sync_from_file_skips_invalid_reports(mocker) -> None:
    neo4j_session = mocker.Mock()

    assert (
        sync_from_file(neo4j_session, "not a docker scout report", "invalid.txt", 1)
        is False
    )
    neo4j_session.run.assert_not_called()
