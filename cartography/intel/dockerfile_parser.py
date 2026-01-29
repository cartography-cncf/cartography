"""
Dockerfile Parser Utility Module

Simple API for parsing Dockerfiles:
- parse(content) - parse from string content
- parse_file(path) - parse from file path

Example:
    from cartography.utils.dockerfile_parser import parse, parse_file

    # From content
    df = parse("FROM python:3.11\\nRUN pip install flask")
    print(df.final_stage.base_image)  # "python"

    # From file
    df = parse_file("/path/to/Dockerfile")
    print(df.is_multistage)  # True/False
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Try to import optional dockerfile parser package for better parsing
try:
    import dockerfile as dockerfile_pkg

    _HAS_DOCKERFILE_PARSER = True
except ImportError:
    _HAS_DOCKERFILE_PARSER = False
    logger.debug("dockerfile package not installed. Using basic parser.")


# =============================================================================
# Data Classes
# =============================================================================


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

    path: str
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


# =============================================================================
# Public API
# =============================================================================


def parse(content: str) -> ParsedDockerfile:
    """
    Parse Dockerfile content and return a structured representation.

    Args:
        content: Raw Dockerfile content as string

    Returns:
        ParsedDockerfile object with all extracted information

    Example:
        df = parse("FROM python:3.11\\nRUN pip install flask")
        print(df.final_stage.base_image)  # "python"
        print(df.layer_creating_instruction_count)  # 1
    """
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    stages = _parse_stages(content)

    return ParsedDockerfile(
        path="",
        content=content,
        content_hash=content_hash,
        stages=stages,
    )


def parse_file(path: str | Path) -> ParsedDockerfile:
    """
    Parse a Dockerfile from a file path.

    Args:
        path: Path to the Dockerfile (string or Path object)

    Returns:
        ParsedDockerfile object with all extracted information

    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read

    Example:
        df = parse_file("/path/to/Dockerfile")
        print(df.is_multistage)
        for stage in df.stages:
            print(f"  {stage.name}: FROM {stage.base_image}")
    """
    path = Path(path)
    content = path.read_text(encoding="utf-8")
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    stages = _parse_stages(content)

    return ParsedDockerfile(
        path=str(path),
        content=content,
        content_hash=content_hash,
        stages=stages,
    )


# =============================================================================
# Command Normalization
# =============================================================================


def normalize_command(cmd: str | None) -> str:
    """
    Normalize a Docker command for comparison.

    Handles:
    - Dockerfile instruction prefix (RUN, COPY, ADD)
    - Shell prefix removal (/bin/sh -c)
    - BuildKit prefixes (|1 VAR=value)
    - Whitespace normalization
    - Inline comment removal
    - BuildKit mount options (--mount=type=cache...)

    Args:
        cmd: The raw command string from Dockerfile or image history

    Returns:
        Normalized command string suitable for comparison
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

    Args:
        history: List of history entries from image config
                 (each with 'created_by' and optionally 'empty_layer')
        added_layer_count: If provided, only return the last N commands (the added layers)

    Returns:
        List of normalized commands that created actual layers
    """
    commands = []
    for entry in history:
        # Skip metadata-only layers (ENV, LABEL, WORKDIR, etc.)
        if entry.get("empty_layer", False):
            continue

        created_by = entry.get("created_by", "")
        if created_by:
            normalized = normalize_command(created_by)
            commands.append(normalized)

    # If we know how many layers were added, only return those (they're at the end)
    if added_layer_count is not None and added_layer_count < len(commands):
        commands = commands[-added_layer_count:]

    return commands


# =============================================================================
# Command Matching
# =============================================================================


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

    Args:
        cmd1: First normalized command
        cmd2: Second normalized command

    Returns:
        Similarity score between 0.0 and 1.0
    """
    if cmd1 == cmd2:
        return 1.0

    # Check containment
    if cmd1 in cmd2 or cmd2 in cmd1:
        return 0.8

    # Check for common patterns
    if _commands_share_pattern(cmd1, cmd2):
        return 0.7

    # Simple token overlap (Jaccard similarity)
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

    Args:
        image_commands: List of normalized commands from image history
        dockerfiles: List of parsed Dockerfiles to compare against
        min_confidence: Minimum confidence threshold for returned matches

    Returns:
        List of DockerfileMatch objects sorted by confidence (highest first)
    """
    matches = []

    for dockerfile in dockerfiles:
        match = _match_commands_to_dockerfile(image_commands, dockerfile)
        if match.confidence >= min_confidence:
            matches.append(match)

    matches.sort(key=lambda m: -m.confidence)
    return matches


# =============================================================================
# Internal Functions
# =============================================================================


def _parse_base_image_reference(from_value: str) -> tuple[str, str | None, str | None]:
    """Parse FROM value to extract image, tag, and digest."""
    # Remove AS alias if present
    from_value = re.sub(r"\s+[Aa][Ss]\s+\w+.*$", "", from_value).strip()

    # Handle --platform and other flags
    from_value = re.sub(r"^--\w+=\S+\s+", "", from_value).strip()

    digest = None
    tag = None

    # Check for digest
    if "@" in from_value:
        base_image, digest = from_value.rsplit("@", 1)
    else:
        base_image = from_value

    # Check for tag
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
    if _HAS_DOCKERFILE_PARSER:
        return _parse_with_dockerfile_package(content)
    else:
        return _parse_basic(content)


def _parse_with_dockerfile_package(content: str) -> list[DockerfileInstruction]:
    """Parse using the dockerfile package for more accurate parsing."""
    instructions = []
    try:
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
    except Exception as e:
        logger.warning(f"Failed to parse Dockerfile with dockerfile package: {e}")
        return _parse_basic(content)
    return instructions


def _parse_basic(content: str) -> list[DockerfileInstruction]:
    """Basic Dockerfile parser as fallback."""
    instructions = []
    current_cmd = None
    current_value_lines: list[str] = []
    current_line_num = 0

    for line_num, line in enumerate(content.split("\n"), 1):
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if current_cmd and current_value_lines:
            if current_value_lines[-1].endswith("\\"):
                current_value_lines[-1] = current_value_lines[-1][:-1]
                current_value_lines.append(stripped)
                continue
            else:
                value = " ".join(current_value_lines)
                instructions.append(
                    DockerfileInstruction(
                        cmd=current_cmd,
                        value=value,
                        line_number=current_line_num,
                    )
                )
                current_cmd = None
                current_value_lines = []

        match = re.match(r"^(\w+)\s*(.*)", stripped)
        if match:
            current_cmd = match.group(1).upper()
            current_value_lines = [match.group(2)] if match.group(2) else []
            current_line_num = line_num

    if current_cmd and current_value_lines:
        value = " ".join(current_value_lines)
        instructions.append(
            DockerfileInstruction(
                cmd=current_cmd,
                value=value,
                line_number=current_line_num,
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
    """Compare normalized commands from image history with Dockerfile instructions."""
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
    total = max(len(image_commands), len(df_commands))
    similarities = []

    for img_cmd, df_cmd in zip(image_commands, df_commands):
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
