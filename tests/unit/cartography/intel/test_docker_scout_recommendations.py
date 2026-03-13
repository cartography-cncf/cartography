from cartography.intel.docker_scout.scanner import _digests_match
from cartography.intel.docker_scout.scanner import parse_recommendation_raw
from cartography.intel.docker_scout.scanner import transform_base_images
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


def test_transform_base_images_returns_built_from_and_recommendation_rows() -> None:
    parsed = parse_recommendation_raw(MOCK_ECR_RECOMMENDATION_RAW)

    transformed = transform_base_images(parsed, "python:3.12-slim")
    rows_by_id = {row["id"]: row for row in transformed if "built_from_public_image_id" in row}
    recommendation_rows = {
        row["id"]: row for row in transformed if "recommended_for_public_image_id" in row
    }

    assert rows_by_id["node:25-alpine"]["built_from_public_image_id"] == "python:3.12-slim"
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
    assert recommendation_rows["node:25-alpine"]["fix"] == '{"H": 2}'
    assert recommendation_rows["node:slim"]["is_slim"] is True


def test_digests_match_accepts_short_and_full_sha256() -> None:
    assert _digests_match(
        "ecr000000000000",
        "sha256:ecr0000000000000000000000000000000000000000000000000000000000000",
    )
