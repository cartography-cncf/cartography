from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

import neo4j

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
    cmd = " ".join(cmd.split()).strip()
    if not cmd:
        return ""

    copy_add_match = re.match(r"^(copy|add)\s+(.+)$", cmd)
    if copy_add_match:
        instruction = copy_add_match.group(1)
        remainder = copy_add_match.group(2)

        # OCI history often looks like:
        #   copy file:<hash> in /dest/
        #   add dir:<hash> in /dest/
        oci_copy_add = re.match(r"^(?:file|dir):\S+\s+in\s+(.+)$", remainder)
        if oci_copy_add:
            destination = oci_copy_add.group(1).strip()
            return f"{instruction}_in {destination}"

        # Dockerfile shell form: COPY src dest
        # Keep only the destination so it becomes comparable to OCI history.
        parts = remainder.split()
        if parts:
            destination = parts[-1]
            return f"{instruction}_in {destination}"

    # Remove Dockerfile RUN prefix after shell/buildkit cleanup so shell-wrapped
    # history and raw Dockerfile instructions normalize the same way.
    cmd = re.sub(r"^run\s+", "", cmd)
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
    """Parse Dockerfile instructions using a lightweight in-repo parser.

    This parser intentionally focuses on extracting instruction/value pairs needed
    for supply-chain matching instead of fully implementing Dockerfile grammar.
    """
    lines = content.splitlines()
    instructions: list[DockerfileInstruction] = []
    i = 0

    while i < len(lines):
        current_line = lines[i]
        stripped = current_line.strip()

        # Ignore empty lines and full-line comments (including parser directives).
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        start_line = i + 1
        logical_line = stripped

        # Join continued lines ending with an unescaped backslash.
        while _has_line_continuation(logical_line) and i + 1 < len(lines):
            logical_line = logical_line.rstrip()[:-1].strip()
            i += 1
            # NOTE: We currently keep comment-only continuation lines in the value.
            # This is a known simplification vs Docker's full parser behavior.
            logical_line = f"{logical_line} {lines[i].strip()}"

        cmd, value = _split_instruction(logical_line)
        if cmd is None:
            i += 1
            continue

        heredoc_delimiter = _extract_heredoc_delimiter(value)
        if heredoc_delimiter:
            i += 1
            found_terminator = False
            while i < len(lines):
                line = lines[i]
                if line.strip() == heredoc_delimiter:
                    found_terminator = True
                    break
                value = f"{value}\n{line}"
                i += 1
            if not found_terminator:
                logger.warning(
                    "Unterminated Dockerfile heredoc delimiter '%s' while parsing.",
                    heredoc_delimiter,
                )

        instructions.append(
            DockerfileInstruction(
                cmd=cmd,
                value=value,
                line_number=start_line,
            )
        )
        i += 1

    return instructions


def _has_line_continuation(line: str) -> bool:
    stripped = line.rstrip()
    trailing_backslashes = len(stripped) - len(stripped.rstrip("\\"))
    return trailing_backslashes % 2 == 1


def _split_instruction(line: str) -> tuple[str | None, str]:
    match = re.match(r"^([A-Za-z]+)(?:\s+(.*))?$", line.strip())
    if not match:
        return None, ""
    cmd = match.group(1).upper()
    value = (match.group(2) or "").strip()
    return cmd, value


def _extract_heredoc_delimiter(value: str) -> str | None:
    # Docker heredoc form: <<EOF or <<-EOF (including quoted delimiters).
    match = re.search(r"<<-?\s*([\"']?)([A-Za-z_][A-Za-z0-9_]*)\1", value)
    if match:
        return match.group(2)
    return None


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

    df_commands = [
        normalize_command(f"{instr.cmd} {instr.value}") for instr in df_instructions
    ]

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
    scope_keys: dict[str, str] | None = None


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
    parsed_dockerfiles: list[tuple[ParsedDockerfile, dict[str, Any]]] = []

    for df_info in dockerfiles:
        try:
            parsed = parse(df_info["content"])
            parsed_dockerfiles.append((parsed, df_info))
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

        candidate_dockerfiles = parsed_dockerfiles
        if image.scope_keys:
            candidate_dockerfiles = [
                (parsed, df_info)
                for parsed, df_info in parsed_dockerfiles
                if all(
                    df_info.get("scope_keys", {}).get(scope_name) == scope_value
                    for scope_name, scope_value in image.scope_keys.items()
                )
            ]
            if not candidate_dockerfiles:
                logger.debug(
                    "No Dockerfiles scoped to %s for image %s:%s",
                    image.scope_keys,
                    image.display_name,
                    image.tag,
                )
                continue

        df_matches = find_best_dockerfile_matches(
            image_commands,
            [parsed for parsed, _ in candidate_dockerfiles],
            min_confidence,
        )

        if df_matches:
            best_match = df_matches[0]
            df_info = next(
                (
                    candidate_info
                    for parsed, candidate_info in candidate_dockerfiles
                    if parsed is best_match.dockerfile
                ),
                {},
            )

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


def unwrap_attestation_predicate(predicate: Any) -> dict[str, Any] | None:
    """
    Normalize a predicate payload into the actual SLSA predicate object.

    Attestation blobs can contain:
    - an in-toto statement where `predicate` is already the predicate dict
    - a DSSE/cosign envelope where `predicate.Data` contains a serialized statement
    """
    if not isinstance(predicate, dict):
        return None

    dsse_data = predicate.get("Data")
    if isinstance(dsse_data, str):
        try:
            decoded = json.loads(dsse_data)
        except ValueError:
            logger.debug("Failed to decode nested attestation predicate Data")
            return None

        if isinstance(decoded, dict):
            nested_predicate = decoded.get("predicate")
            return nested_predicate if isinstance(nested_predicate, dict) else None

    return predicate


def decode_attestation_blob_to_predicate(
    blob: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Extract an in-toto SLSA predicate from an attestation blob.

    Supports two common shapes:
    - DSSE/cosign envelopes where the blob contains a base64-encoded `payload`
      that decodes to an in-toto statement
    - Raw in-toto statements where the blob already has `predicate` directly
    """
    payload_b64 = blob.get("payload")
    if payload_b64:
        try:
            payload = json.loads(base64.b64decode(str(payload_b64)).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            logger.debug("Failed to decode DSSE attestation payload")
            return None
        if isinstance(payload, dict) and "predicate" in payload:
            return unwrap_attestation_predicate(payload.get("predicate"))
        return None

    if "predicate" in blob:
        return unwrap_attestation_predicate(blob.get("predicate"))

    return None


def get_slsa_dependency_list(predicate: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Return the dependency list across supported SLSA predicate shapes.

    Supports:
    - SLSA v0.2: predicate.materials
    - SLSA v1: predicate.buildDefinition.resolvedDependencies
    """
    dependency_list = predicate.get("materials", [])
    if dependency_list:
        return dependency_list

    build_def = predicate.get("buildDefinition", {})
    return build_def.get("resolvedDependencies", [])


def extract_container_parent_image(predicate: dict[str, Any]) -> dict[str, str]:
    """
    Extract the parent/base container image reference from SLSA dependencies.

    Supports both SLSA v0.2 `materials` and SLSA v1 `resolvedDependencies`.
    Returns the first container image dependency that is not the Dockerfile frontend.
    """
    for dependency in get_slsa_dependency_list(predicate):
        if not isinstance(dependency, dict):
            continue

        uri = str(dependency.get("uri", ""))
        uri_l = uri.lower()
        is_container_ref = (
            uri_l.startswith("pkg:docker/")
            or uri_l.startswith("pkg:oci/")
            or uri_l.startswith("oci://")
        )
        if not is_container_ref or "dockerfile" in uri_l:
            continue

        digest = dependency.get("digest", {})
        if not isinstance(digest, dict):
            continue

        sha256_digest = digest.get("sha256")
        if sha256_digest:
            return {
                "parent_image_uri": uri,
                "parent_image_digest": f"sha256:{sha256_digest}",
            }

    return {}


def extract_image_source_provenance(predicate: dict[str, Any]) -> dict[str, str]:
    """
    Extract provider-agnostic image provenance source fields from a SLSA predicate.

    Returns any of:
    - source_uri
    - source_revision
    - source_file
    """
    result: dict[str, str] = {}

    metadata = predicate.get("metadata", {})
    buildkit_metadata = metadata.get("https://mobyproject.org/buildkit@v1#metadata", {})
    vcs = buildkit_metadata.get("vcs", {})
    if not vcs:
        run_details = predicate.get("runDetails", {})
        run_metadata = run_details.get("metadata", {})
        vcs = run_metadata.get("buildkit_metadata", {}).get("vcs", {})

    build_def = predicate.get("buildDefinition", {})
    external_parameters = build_def.get("externalParameters", {})
    resolved_dependencies = get_slsa_dependency_list(predicate)

    source_uri = vcs.get("source") or external_parameters.get("source")
    if source_uri:
        result["source_uri"] = normalize_vcs_url(str(source_uri))

    source_revision = vcs.get("revision")
    if not source_revision:
        for dependency in resolved_dependencies:
            if not isinstance(dependency, dict):
                continue
            digest = dependency.get("digest", {})
            if not isinstance(digest, dict):
                continue
            git_commit = digest.get("gitCommit")
            if git_commit:
                source_revision = git_commit
                break
    if source_revision:
        result["source_revision"] = str(source_revision)

    invocation = predicate.get("invocation", {})
    config_source = invocation.get("configSource", {})
    entry_point = config_source.get("entryPoint", "")
    if not entry_point:
        entry_point = external_parameters.get("entryPoint", "")
    if not entry_point:
        entry_point = external_parameters.get("configSource", {}).get("path", "")
    if not entry_point:
        entry_point = "Dockerfile"

    if "source_uri" in result:
        dockerfile_dir = (
            str(vcs.get("localdir:dockerfile") or "").removeprefix("./").rstrip("/")
        )
        result["source_file"] = (
            f"{dockerfile_dir}/{entry_point}" if dockerfile_dir else str(entry_point)
        )

    return result


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


# Standard OCI annotation keys for source provenance
_OCI_SOURCE_LABELS = [
    "org.opencontainers.image.source",
    "vcs.source",
]
_OCI_REVISION_LABELS = [
    "org.opencontainers.image.revision",
    "vcs.revision",
]


def extract_provenance_from_oci_config(
    config: dict[str, Any],
) -> dict[str, str]:
    """
    Extract source provenance from an OCI image config's labels and annotations.

    Checks standard OCI annotation keys (org.opencontainers.image.source) and
    BuildKit VCS metadata (vcs.source, vcs.revision).

    :param config: The parsed OCI image config JSON
    :return: Dict with any of: source_uri, source_revision
    """
    result: dict[str, str] = {}

    labels = config.get("config", {}).get("Labels") or {}

    for key in _OCI_SOURCE_LABELS:
        value = labels.get(key)
        if value:
            result["source_uri"] = normalize_vcs_url(value)
            break

    for key in _OCI_REVISION_LABELS:
        value = labels.get(key)
        if value:
            result["source_revision"] = str(value)
            break

    return result


def extract_layers_from_oci_config(
    config: dict[str, Any],
) -> tuple[list[str], list[dict[str, Any]]]:
    """
    Extract layer diff_ids and history from an OCI image config.

    :param config: The parsed OCI image config JSON
    :return: Tuple of (layer_diff_ids, layer_history) where layer_history
             entries have 'created_by' and 'empty_layer' keys.
    """
    diff_ids: list[str] = config.get("rootfs", {}).get("diff_ids", [])

    raw_history: list[dict[str, Any]] = config.get("history", [])
    layer_history: list[dict[str, Any]] = [
        {
            "created_by": entry.get("created_by", ""),
            "empty_layer": entry.get("empty_layer", False),
        }
        for entry in raw_history
    ]

    return diff_ids, layer_history


def get_unmatched_gcp_images_with_history(
    neo4j_session: neo4j.Session,
    sub_resource_label: str,
    sub_resource_id: str | int,
    update_tag: int,
    limit: int | None = None,
) -> list[ContainerImage]:
    """
    Query GCP Artifact Registry images not yet matched by provenance.

    Shared helper used by GitHub and GitLab supply chain modules to include
    GCP images in Dockerfile analysis alongside ECR/GitLab registry images.

    :param neo4j_session: Neo4j session
    :param sub_resource_label: The sub-resource label for scoping (e.g., 'GitHubOrganization')
    :param sub_resource_id: The sub-resource ID for scoping (e.g., org name or ID)
    :param update_tag: The current sync update tag
    :param limit: Optional limit on number of images to return
    :return: List of ContainerImage objects with layer history populated
    """
    query = """
        MATCH (img:Image:GCPArtifactRegistryContainerImage)
        WHERE img.layer_diff_ids IS NOT NULL
          AND size(img.layer_diff_ids) > 0
          AND NOT exists((img)-[:PACKAGED_FROM {lastupdated: $update_tag}]->())
          AND (
              NOT exists((img)-[:PACKAGED_FROM {_sub_resource_label: $sub_resource_label}]->())
              OR exists((img)-[:PACKAGED_FROM {_sub_resource_id: $sub_resource_id}]->())
          )
        OPTIONAL MATCH (img)<-[:CONTAINS]-(gcpRepo:GCPArtifactRegistryRepository)
        WITH coalesce(gcpRepo.id, img.id) AS group_key, img
        ORDER BY img.upload_time DESC
        WITH group_key, collect(img)[0] AS img
        WITH img
        UNWIND range(0, size(img.layer_diff_ids) - 1) AS idx
        WITH img, img.layer_diff_ids[idx] AS diff_id, idx
        OPTIONAL MATCH (layer:ImageLayer {diff_id: diff_id})
        WITH img, idx, {
            diff_id: diff_id,
            history: layer.history,
            is_empty: layer.is_empty
        } AS layer_info
        ORDER BY idx
        WITH img, collect(layer_info) AS layer_history
        RETURN
            img.digest AS digest,
            img.uri AS uri,
            img.repository_id AS repository_id,
            img.name AS name,
            img.layer_diff_ids AS layer_diff_ids,
            layer_history
    """

    if limit is not None:
        query += f" LIMIT {int(limit)}"

    result = neo4j_session.run(
        query,
        update_tag=update_tag,
        sub_resource_label=sub_resource_label,
        sub_resource_id=sub_resource_id,
    )
    images = []

    for record in result:
        layer_history = convert_layer_history_records(record["layer_history"])
        images.append(
            ContainerImage(
                digest=record["digest"],
                uri=record["uri"] or "",
                registry_id=record["repository_id"] or None,
                display_name=record["name"] or None,
                tag=None,
                layer_diff_ids=record["layer_diff_ids"] or [],
                image_type=None,
                architecture=None,
                os=None,
                layer_history=layer_history,
            ),
        )

    if images:
        logger.info(
            "Found %d GCP Artifact Registry images with layer history for dockerfile analysis",
            len(images),
        )
    return images
