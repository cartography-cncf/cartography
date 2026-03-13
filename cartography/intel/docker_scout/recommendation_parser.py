import re
from typing import Any

SEVERITIES = ("C", "H", "M", "L")
TARGET_PATTERN = re.compile(
    r"^\s*Target\s*│\s*(.*?)\s*$\r?\n^\s*digest\s*│\s*(.*?)\s*$",
    flags=re.MULTILINE,
)


def extract_section(text: str, title: str, next_titles: tuple[str, ...]) -> str:
    start = text.find(title)
    if start == -1:
        return ""

    end_candidates = [
        text.find(next_title, start + len(title)) for next_title in next_titles
    ]
    end_candidates = [candidate for candidate in end_candidates if candidate != -1]
    end = min(end_candidates) if end_candidates else len(text)
    return text[start:end]


def parse_vulnerabilities(value: str) -> dict[str, int]:
    matches = re.findall(r"(\d+)([CHML])", value)
    return {severity: 0 for severity in SEVERITIES} | {
        severity: int(count) for count, severity in matches
    }


def infer_image_os(tag: str, image_flavor: str | None) -> str | None:
    if image_flavor:
        normalized = image_flavor.strip().lower()
        if normalized in {"alpine", "debian", "ubuntu", "wolfi", "distroless"}:
            return normalized

    lowered_tag = tag.lower()
    if "alpine" in lowered_tag:
        return "alpine"
    if any(
        name in lowered_tag for name in ("bookworm", "bullseye", "buster", "trixie")
    ):
        return "debian"
    if "ubuntu" in lowered_tag or any(
        name in lowered_tag for name in ("jammy", "focal", "noble")
    ):
        return "ubuntu"
    return image_flavor.lower() if image_flavor else None


def parse_target(text: str) -> dict[str, str]:
    target_match = TARGET_PATTERN.search(text)
    if not target_match:
        raise ValueError("Failed to find the Docker Scout 'Target' section.")

    image, digest = target_match.groups()
    return {"image": image.strip(), "digest": digest.strip()}


def drop_none(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item is not None and item != {}}


def parse_alternative_tags(text: str) -> list[str]:
    lines = text.splitlines()
    supported_tags_lines: list[str] = []
    collecting = False

    for line in lines:
        if "│" not in line:
            if collecting:
                break
            continue

        _, right_column = line.split("│", 1)
        normalized = right_column.strip()
        if not collecting and "supported tag(s)" in normalized:
            collecting = True

        if not collecting:
            continue

        supported_tags_lines.append(normalized)
        if "If you want to display recommendations" in normalized:
            break

    supported_tags_text = " ".join(supported_tags_lines)
    match = re.search(
        r"supported tag\(s\)\s+(.+?)\.\s+If you want to display recommendations",
        supported_tags_text,
    )
    if not match:
        return []

    return re.findall(r"`([^`]+)`", match.group(1))


def parse_base_image(text: str) -> tuple[dict[str, Any], dict[str, int]]:
    base_match = re.search(r"Base image is\s+(\S+)", text)
    if not base_match:
        raise ValueError("Failed to find the 'Base image is ...' line.")

    image_ref = base_match.group(1)
    if ":" not in image_ref:
        raise ValueError("Failed to split the Docker Scout base image reference.")

    image_name, tag = image_ref.rsplit(":", 1)
    section = extract_section(text, "## Recommended fixes", ("Refresh base image",))

    field_matches = re.findall(
        r"^\s*([A-Za-z]+)\s*│\s*(.*?)\s*$", section, flags=re.MULTILINE
    )
    fields = {key: value.strip() for key, value in field_matches}

    vulnerabilities = parse_vulnerabilities(fields.get("Vulnerabilities", ""))
    flavor = fields.get("Flavor")
    alternative_tags = parse_alternative_tags(text)

    base_image = {
        "name": image_name,
        "tag": fields.get("Name", tag),
        "digest": fields.get("Digest"),
        "size": fields.get("Size"),
        "flavor": flavor.lower() if flavor else None,
        "os": infer_image_os(tag, flavor),
        "runtime": fields.get("Runtime"),
        "is_slim": fields.get("Slim", "").strip() == "✓" or "slim" in tag.lower(),
        "alternative_tags": alternative_tags,
    }

    return drop_none(base_image), vulnerabilities


def split_recommendation_blocks(section: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current_block: list[str] | None = None

    for line in section.splitlines():
        if "│" not in line:
            continue

        parts = [part.strip() for part in line.split("│")]
        if len(parts) < 4:
            continue

        left, detail = parts[0], parts[1]
        if detail == "Benefits:" and left and not left.startswith("• "):
            if current_block:
                blocks.append(current_block)
            current_block = [line]
            continue

        if current_block is not None:
            current_block.append(line)

    if current_block:
        blocks.append(current_block)

    return blocks


def parse_recommendation_block(
    block: list[str],
    image_name: str,
    current_vulnerabilities: dict[str, int],
) -> dict[str, Any]:
    first_columns = [part.strip() for part in block[0].split("│")]
    tag = first_columns[0]
    vulnerabilities = parse_vulnerabilities(first_columns[3])

    details_started = False
    detail_fields: dict[str, str] = {}
    benefits: list[str] = []
    alternative_tags: list[str] = []

    for line in block:
        parts = [part.strip() for part in line.split("│")]
        if len(parts) < 4:
            continue

        left_column, detail_column = parts[0], parts[1]

        if left_column.startswith("• "):
            alternative_tags.append(left_column[2:].strip())

        if detail_column == "Image details:":
            details_started = True
            continue

        if not detail_column.startswith("• "):
            continue

        detail_text = detail_column[2:]
        if details_started:
            if ":" not in detail_text:
                continue

            key, value = detail_text.split(":", 1)
            detail_fields[key.strip().lower()] = value.strip()
            continue

        benefits.append(detail_text)

    flavor = detail_fields.get("flavor")
    recommendation = {
        "name": image_name,
        "tag": tag,
        "alternative_tags": alternative_tags,
        "size": detail_fields.get("size"),
        "flavor": flavor.lower() if flavor else None,
        "os": infer_image_os(tag, flavor),
        "runtime": detail_fields.get("runtime"),
        "is_slim": detail_fields.get("slim", "") == "✓" or "slim" in tag.lower(),
        "benefits": benefits,
        "fix": {
            severity: max(
                current_vulnerabilities.get(severity, 0)
                - vulnerabilities.get(severity, 0),
                0,
            )
            for severity in SEVERITIES
            if current_vulnerabilities.get(severity, 0)
            - vulnerabilities.get(severity, 0)
            > 0
        },
    }

    return drop_none(recommendation)


def parse_recommendations(
    text: str,
    section_name: str,
    next_titles: tuple[str, ...],
    image_name: str,
    vulnerabilities: dict[str, int],
) -> dict[str, dict[str, Any]]:
    section = extract_section(text, section_name, next_titles)
    blocks = split_recommendation_blocks(section)
    recommendations = [
        parse_recommendation_block(block, image_name, vulnerabilities)
        for block in blocks
    ]
    return {
        str(recommendation["tag"]): recommendation for recommendation in recommendations
    }


def merge_recommendation_maps(
    *maps: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for recommendation_map in maps:
        for tag, recommendation in recommendation_map.items():
            if tag not in merged:
                merged[tag] = recommendation
                continue

            current = merged[tag]
            merged[tag] = (
                recommendation if len(recommendation) > len(current) else current
            )

    return merged


def parse_recommendation_text(text: str) -> dict[str, Any]:
    target = parse_target(text)
    try:
        base_image, vulnerabilities = parse_base_image(text)
    except ValueError as exc:
        if "Base image is" not in text:
            raise
        raise ValueError(
            "Failed to parse the Docker Scout base image section."
        ) from exc
    image_name = str(base_image["name"])

    refresh_recommendations = parse_recommendations(
        text,
        "Refresh base image",
        ("Change base image",),
        image_name,
        vulnerabilities,
    )
    change_recommendations = parse_recommendations(
        text,
        "Change base image",
        (),
        image_name,
        vulnerabilities,
    )

    return {
        "target": target,
        "base_image": base_image,
        "recommendations": merge_recommendation_maps(
            refresh_recommendations,
            change_recommendations,
        ),
    }
