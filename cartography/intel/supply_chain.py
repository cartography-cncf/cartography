from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

import dockerfile as dockerfile_pkg

logger = logging.getLogger(__name__)


@dataclass
class DockerfileInstruction:
    """Represents a single Dockerfile instruction."""

    cmd: str
    value: str
    line_number: int
    stage_name: str | None = None
    normalized_value: str = ""

    def __post_init__(self) -> None:
        if not self.normalized_value:
            self.normalized_value = normalize_command(self.value)

    @property
    def creates_layer(self) -> bool:
        """Returns True if this instruction creates a filesystem layer."""
        return self.cmd in ("RUN", "COPY", "ADD")


@dataclass
class DockerfileStage:
    """Represents a stage in a multi-stage Dockerfile."""

    name: str | None
    base_image: str
    base_image_tag: str | None
    base_image_digest: str | None
    instructions: list[DockerfileInstruction] = field(default_factory=list)

    @property
    def layer_creating_instructions(self) -> list[DockerfileInstruction]:
        """Get instructions that create filesystem layers (RUN, COPY, ADD)."""
        return [i for i in self.instructions if i.creates_layer]

    @property
    def layer_count(self) -> int:
        """Number of layers this stage creates."""
        return len(self.layer_creating_instructions)


@dataclass
class ParsedDockerfile:
    """Represents a fully parsed Dockerfile."""

    path: str | None
    content: str
    content_hash: str
    stages: list[DockerfileStage] = field(default_factory=list)

    @property
    def is_multistage(self) -> bool:
        """Returns True if this is a multi-stage Dockerfile."""
        return len(self.stages) > 1

    @property
    def stage_count(self) -> int:
        """Number of stages in the Dockerfile."""
        return len(self.stages)

    @property
    def final_stage(self) -> DockerfileStage | None:
        """Get the final stage (the one that produces the output image)."""
        return self.stages[-1] if self.stages else None

    @property
    def all_base_images(self) -> list[str]:
        """Get all base images referenced in the Dockerfile."""
        return [stage.base_image for stage in self.stages if stage.base_image]

    @property
    def final_base_image(self) -> str | None:
        """Get the base image of the final stage."""
        return self.final_stage.base_image if self.final_stage else None

    def get_final_stage_layer_instructions(self) -> list[DockerfileInstruction]:
        """Get only the instructions from the final stage that create layers."""
        if not self.final_stage:
            return []
        return self.final_stage.layer_creating_instructions

    @property
    def layer_creating_instruction_count(self) -> int:
        """Count of RUN/COPY/ADD instructions in the final stage."""
        return len(self.get_final_stage_layer_instructions())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "path": self.path,
            "content_hash": self.content_hash,
            "is_multistage": self.is_multistage,
            "stage_count": self.stage_count,
            "final_base_image": self.final_base_image,
            "layer_count": self.layer_creating_instruction_count,
            "all_base_images": self.all_base_images,
            "stages": [
                {
                    "name": stage.name,
                    "base_image": stage.base_image,
                    "base_image_tag": stage.base_image_tag,
                    "base_image_digest": stage.base_image_digest,
                    "layer_count": stage.layer_count,
                }
                for stage in self.stages
            ],
        }


def parse(content: str) -> ParsedDockerfile:
    """
    Parse Dockerfile content and return a structured representation.

    :param content: Raw Dockerfile content as string
    :return: ParsedDockerfile object with all extracted information
    """
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    stages = _parse_stages(content)

    return ParsedDockerfile(
        path=None,
        content=content,
        content_hash=content_hash,
        stages=stages,
    )


def parse_file(path: str | Path) -> ParsedDockerfile:
    """
    Parse a Dockerfile from a file path.

    :param path: Path to the Dockerfile (string or Path object)
    :return: ParsedDockerfile object with all extracted information
    :raises FileNotFoundError: If the file does not exist
    :raises IOError: If the file cannot be read
    """
    path = Path(path)
    content = path.read_text(encoding="utf-8")
    result = parse(content)
    result.path = str(path)
    return result


def normalize_command(cmd: str | None) -> str:
    """
    Normalize a Docker command for comparison.

    Handles Dockerfile instruction prefixes, shell prefixes, BuildKit prefixes,
    whitespace normalization, inline comment removal, and mount options.

    :param cmd: The raw command string from Dockerfile or image history
    :return: Normalized command string suitable for comparison
    """
    if not cmd:
        return ""

    # Lowercase first for consistent matching
    cmd = cmd.lower()

    # Remove Dockerfile instruction prefixes
    cmd = re.sub(r"^(run|copy|add)\s+", "", cmd)

    # Remove shell prefix added by Docker
    cmd = re.sub(r"^/bin/sh -c\s+", "", cmd)
    cmd = re.sub(r"^#\(nop\)\s+", "", cmd)  # BuildKit nop marker

    # Remove BuildKit prefixes like "|1 VAR=value "
    cmd = re.sub(r"^\|\d+\s+(\w+=\S+\s+)*", "", cmd)

    # Remove BuildKit mount options
    cmd = re.sub(r"--mount=\S+\s*", "", cmd)

    # Remove inline comments
    cmd = re.sub(r"\s*#.*$", "", cmd)

    # Normalize whitespace
    cmd = " ".join(cmd.split())

    return cmd.strip()


def extract_layer_commands_from_history(
    history: list[dict[str, Any]],
    added_layer_count: int | None = None,
) -> list[str]:
    """
    Extract the actual commands from image history, filtering out metadata-only entries.

    :param history: List of history entries from image config
                    (each with 'created_by' and optionally 'empty_layer')
    :param added_layer_count: If provided, only return the last N commands (the added layers)
    :return: List of normalized commands that created actual layers
    """
    commands = []
    for entry in history:
        if entry.get("empty_layer", False):
            continue

        created_by = entry.get("created_by", "")
        if created_by:
            normalized = normalize_command(created_by)
            commands.append(normalized)

    if added_layer_count is not None and added_layer_count < len(commands):
        commands = commands[-added_layer_count:]

    return commands


@dataclass
class DockerfileMatch:
    """Represents a match between container image commands and a Dockerfile."""

    dockerfile: ParsedDockerfile
    confidence: float
    matched_commands: int
    total_commands: int
    command_similarity: float


def compute_command_similarity(cmd1: str, cmd2: str) -> float:
    """
    Compute similarity between two normalized commands.

    :param cmd1: First normalized command
    :param cmd2: Second normalized command
    :return: Similarity score between 0.0 and 1.0
    """
    if cmd1 == cmd2:
        return 1.0

    if cmd1 in cmd2 or cmd2 in cmd1:
        return 0.8

    if _commands_share_pattern(cmd1, cmd2):
        return 0.7

    tokens1 = set(cmd1.split())
    tokens2 = set(cmd2.split())
    if tokens1 and tokens2:
        overlap = len(tokens1 & tokens2) / len(tokens1 | tokens2)
        return overlap * 0.6

    return 0.0


def find_best_dockerfile_matches(
    image_commands: list[str],
    dockerfiles: list[ParsedDockerfile],
    min_confidence: float = 0.0,
) -> list[DockerfileMatch]:
    """
    Find the best matching Dockerfiles for the given image commands.

    :param image_commands: List of normalized commands from image history
    :param dockerfiles: List of parsed Dockerfiles to compare against
    :param min_confidence: Minimum confidence threshold for returned matches
    :return: List of DockerfileMatch objects sorted by confidence (highest first)
    """
    matches = []

    for dockerfile in dockerfiles:
        match = _match_commands_to_dockerfile(image_commands, dockerfile)
        if match.confidence >= min_confidence:
            matches.append(match)

    matches.sort(key=lambda m: -m.confidence)
    return matches


def _parse_base_image_reference(from_value: str) -> tuple[str, str | None, str | None]:
    """Parse FROM value to extract image, tag, and digest."""
    from_value = re.sub(r"\s+[Aa][Ss]\s+\w+.*$", "", from_value).strip()
    from_value = re.sub(r"^--\w+=\S+\s+", "", from_value).strip()

    digest = None
    tag = None

    if "@" in from_value:
        base_image, digest = from_value.rsplit("@", 1)
    else:
        base_image = from_value

    if ":" in base_image:
        parts = base_image.split(":")
        if len(parts) >= 2:
            potential_tag = parts[-1]
            if "/" not in potential_tag:
                tag = potential_tag
                base_image = ":".join(parts[:-1])

    return base_image, tag, digest


def _parse_instructions(content: str) -> list[DockerfileInstruction]:
    """Parse Dockerfile content into a list of instructions."""
    return _parse_with_dockerfile_package(content)


def _parse_with_dockerfile_package(content: str) -> list[DockerfileInstruction]:
    """Parse using the dockerfile package for accurate parsing.

    :raises Exception: If parsing fails (e.g., invalid Dockerfile syntax)
    """
    instructions = []
    parsed = dockerfile_pkg.parse_string(content)
    for cmd in parsed:
        value = " ".join(cmd.value) if cmd.value else ""
        instructions.append(
            DockerfileInstruction(
                cmd=cmd.cmd,
                value=value,
                line_number=cmd.start_line,
            )
        )
    return instructions


def _parse_stages(content: str) -> list[DockerfileStage]:
    """Parse Dockerfile content into stages."""
    stages = []
    current_stage = None
    instructions = _parse_instructions(content)

    for instruction in instructions:
        if instruction.cmd == "FROM":
            if current_stage:
                stages.append(current_stage)

            match = re.search(r"\b[Aa][Ss]\s+(\w+)", instruction.value)
            stage_name = match.group(1) if match else None
            base_image, tag, digest = _parse_base_image_reference(instruction.value)

            current_stage = DockerfileStage(
                name=stage_name,
                base_image=base_image,
                base_image_tag=tag,
                base_image_digest=digest,
                instructions=[],
            )
        elif current_stage:
            instruction.stage_name = current_stage.name
            current_stage.instructions.append(instruction)

    if current_stage:
        stages.append(current_stage)

    return stages


def _commands_share_pattern(cmd1: str, cmd2: str) -> bool:
    """Check if commands share common patterns (same type of operation)."""
    pkg_patterns = [
        "apt-get install",
        "apk add",
        "pip install",
        "npm install",
        "yarn add",
    ]
    for pattern in pkg_patterns:
        if pattern in cmd1 and pattern in cmd2:
            return True

    if "copy" in cmd1 and "copy" in cmd2:
        return True

    return False


def _match_commands_to_dockerfile(
    image_commands: list[str],
    dockerfile: ParsedDockerfile,
) -> DockerfileMatch:
    """Compare normalized commands from image history with Dockerfile instructions.

    For images built from multi-stage Dockerfiles, the added layers appear at the
    END of the image history (after base image layers). We compare the LAST N
    image commands against the Dockerfile commands, where N = number of Dockerfile
    layer-creating instructions.
    """
    df_instructions = dockerfile.get_final_stage_layer_instructions()

    if not df_instructions or not image_commands:
        return DockerfileMatch(
            dockerfile=dockerfile,
            confidence=0.0,
            matched_commands=0,
            total_commands=max(len(image_commands), len(df_instructions)),
            command_similarity=0.0,
        )

    df_commands = [instr.normalized_value for instr in df_instructions]

    n_df_commands = len(df_commands)
    if len(image_commands) > n_df_commands:
        image_commands_to_compare = image_commands[-n_df_commands:]
    else:
        image_commands_to_compare = image_commands

    total = max(len(image_commands_to_compare), len(df_commands))
    similarities = []

    for img_cmd, df_cmd in zip(image_commands_to_compare, df_commands):
        sim = compute_command_similarity(img_cmd, df_cmd)
        similarities.append(sim)

    similarity_score = sum(similarities) / total if total > 0 else 0.0
    matched_count = sum(1 for s in similarities if s >= 0.7)

    if similarity_score >= 0.9:
        confidence = 0.98
    elif similarity_score >= 0.7:
        confidence = 0.90
    elif similarity_score >= 0.5:
        confidence = 0.75
    elif similarity_score >= 0.3:
        confidence = 0.50
    else:
        confidence = similarity_score * 0.5

    return DockerfileMatch(
        dockerfile=dockerfile,
        confidence=confidence,
        matched_commands=matched_count,
        total_commands=total,
        command_similarity=similarity_score,
    )


@dataclass
class ContainerImage:
    """Represents a container image from the graph (ECR, GCR, GitLab, etc.)."""

    digest: str
    uri: str
    registry_id: str | None
    display_name: str | None
    tag: str | None
    layer_diff_ids: list[str]
    image_type: str | None
    architecture: str | None
    os: str | None
    layer_history: list[dict[str, Any]]


@dataclass
class ImageDockerfileMatch:
    """Represents a match between a container image and a Dockerfile."""

    image_digest: str
    source_repo_id: str
    dockerfile_path: str | None
    confidence: float
    matched_commands: int
    total_commands: int
    command_similarity: float


def match_images_to_dockerfiles(
    images: list[ContainerImage],
    dockerfiles: list[dict[str, Any]],
    min_confidence: float = 0.5,
) -> list[ImageDockerfileMatch]:
    """
    Match container images to Dockerfiles based on layer history commands.

    :param images: List of container images to match (with layer_history already populated)
    :param dockerfiles: List of dockerfile dictionaries (from provider-specific get_dockerfiles)
    :param min_confidence: Minimum confidence threshold for matches
    :return: List of ImageDockerfileMatch objects
    """
    parsed_dockerfiles: list[ParsedDockerfile] = []
    dockerfile_info_map: dict[str, dict[str, Any]] = {}

    for df_info in dockerfiles:
        try:
            parsed = parse(df_info["content"])
            dockerfile_info_map[parsed.content_hash] = df_info
            parsed_dockerfiles.append(parsed)
        except Exception as e:
            logger.warning("Failed to parse dockerfile %s: %s", df_info.get("path"), e)

    if not parsed_dockerfiles:
        logger.warning("No valid Dockerfiles to match against")
        return []

    matches: list[ImageDockerfileMatch] = []

    for image in images:
        if not image.digest:
            logger.debug(
                "No digest for image %s:%s, skipping",
                image.display_name,
                image.tag,
            )
            continue
        if not image.layer_history:
            logger.debug(
                "No layer history for image %s:%s", image.display_name, image.tag
            )
            continue

        image_commands = extract_layer_commands_from_history(image.layer_history)
        if not image_commands:
            logger.debug(
                "No commands extracted for image %s:%s",
                image.display_name,
                image.tag,
            )
            continue

        df_matches = find_best_dockerfile_matches(
            image_commands, parsed_dockerfiles, min_confidence
        )

        if df_matches:
            best_match = df_matches[0]
            df_info = dockerfile_info_map.get(best_match.dockerfile.content_hash, {})

            matches.append(
                ImageDockerfileMatch(
                    image_digest=image.digest,
                    source_repo_id=df_info.get("source_repo_id", ""),
                    dockerfile_path=df_info.get("path"),
                    confidence=best_match.confidence,
                    matched_commands=best_match.matched_commands,
                    total_commands=best_match.total_commands,
                    command_similarity=best_match.command_similarity,
                )
            )
            logger.debug(
                "Matched %s:%s -> %s (confidence: %.2f)",
                image.display_name,
                image.tag,
                df_info.get("path"),
                best_match.confidence,
            )
        else:
            logger.debug(
                "No match found for image %s:%s", image.display_name, image.tag
            )

    logger.info(
        "Matched %d images to Dockerfiles (out of %d images, %d Dockerfiles)",
        len(matches),
        len(images),
        len(parsed_dockerfiles),
    )
    return matches


def transform_matches_for_matchlink(
    matches: list[ImageDockerfileMatch],
    source_repo_field: str,
) -> list[dict[str, Any]]:
    """
    Transform ImageDockerfileMatch objects into dictionaries for load_matchlinks.

    :param matches: List of ImageDockerfileMatch objects
    :param source_repo_field: Field name for the source repo ID (e.g. "repo_url" or "project_url")
    :return: List of dictionaries with fields matching the MatchLink schema
    """
    return [
        {
            "image_digest": m.image_digest,
            source_repo_field: m.source_repo_id,
            "match_method": "dockerfile_analysis",
            "dockerfile_path": m.dockerfile_path,
            "confidence": m.confidence,
            "matched_commands": m.matched_commands,
            "total_commands": m.total_commands,
            "command_similarity": m.command_similarity,
        }
        for m in matches
        if m.source_repo_id
    ]


def parse_dockerfile_info(
    content: str,
    path: str,
    display_name: str,
) -> dict[str, Any] | None:
    """
    Parse a Dockerfile and return structured info, or None on failure.

    Provider modules call this and then add their own identifier fields
    (repo_url/project_url, repo_name/project_name, sha, html_url, etc.).

    :param content: Raw Dockerfile content
    :param path: File path within the repository
    :param display_name: Human-readable repo/project name (for logging)
    :return: Dict with parsed fields, or None if parsing fails
    """
    try:
        parsed = parse(content)
        return {
            "path": path,
            "content": content,
            "is_multistage": parsed.is_multistage,
            "stage_count": parsed.stage_count,
            "final_base_image": parsed.final_base_image,
            "all_base_images": parsed.all_base_images,
            "layer_count": parsed.layer_creating_instruction_count,
            "stages": [
                {
                    "name": stage.name,
                    "base_image": stage.base_image,
                    "base_image_tag": stage.base_image_tag,
                    "layer_count": stage.layer_count,
                }
                for stage in parsed.stages
            ],
        }
    except Exception as e:
        logger.warning("Failed to parse Dockerfile %s/%s: %s", display_name, path, e)
        return None


def convert_layer_history_records(
    raw_records: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """
    Convert raw layer history records from Neo4j query results into the format
    expected by the matching algorithm.

    :param raw_records: Raw layer records from Neo4j (with 'history', 'is_empty', 'diff_id')
    :return: List of dicts with 'created_by', 'empty_layer', 'diff_id' keys
    """
    return [
        {
            "created_by": layer.get("history") or "",
            "empty_layer": layer.get("is_empty") or False,
            "diff_id": layer.get("diff_id"),
        }
        for layer in (raw_records or [])
    ]


def normalize_vcs_url(url: str) -> str:
    """
    Normalize a VCS URL from BuildKit provenance to a canonical HTTPS repo URL.

    BuildKit vcs.source can report URLs in various formats:
    - https://github.com/org/repo.git
    - git@github.com:org/repo.git
    - https://github.com/org/repo

    Downstream matching compares source_uri against GitHubRepository.id / GitLabProject.id,
    which use the canonical HTTPS URL without .git suffix (e.g., https://github.com/org/repo).

    :param url: The raw VCS URL from provenance
    :return: Normalized HTTPS URL without .git suffix
    """
    normalized = url.strip()

    ssh_match = re.match(r"git@([^:]+):(.+)", normalized)
    if ssh_match:
        host, path = ssh_match.groups()
        normalized = f"https://{host}/{path}"

    if normalized.endswith(".git"):
        normalized = normalized[:-4]

    return normalized


def extract_workflow_path_from_ref(workflow_ref: str | None) -> str | None:
    """
    Extract the workflow file path from a GitHub workflow ref.

    The workflow ref format is: {owner}/{repo}/{path}@{ref}
    Example: "subimagesec/subimage/.github/workflows/docker-push.yaml@refs/pull/1042/merge"
    Returns: ".github/workflows/docker-push.yaml"

    :param workflow_ref: The full workflow reference string
    :return: The workflow file path, or None if parsing fails
    """
    if not workflow_ref:
        return None

    path_part = workflow_ref.split("@")[0]

    parts = path_part.split("/", 2)
    if len(parts) >= 3:
        return parts[2]

    return None
