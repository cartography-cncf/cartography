"""
Tests for the Dockerfile parser utility module.
"""

import tempfile
from pathlib import Path

from cartography.intel.supply_chain import compute_command_similarity
from cartography.intel.supply_chain import extract_layer_commands_from_history
from cartography.intel.supply_chain import find_best_dockerfile_matches
from cartography.intel.supply_chain import normalize_command
from cartography.intel.supply_chain import parse
from cartography.intel.supply_chain import parse_file

# =============================================================================
# normalize_command tests
# =============================================================================


def test_normalize_empty_command():
    assert normalize_command("") == ""
    assert normalize_command(None) == ""


def test_normalize_removes_shell_prefix():
    cmd = "/bin/sh -c pip install flask"
    assert normalize_command(cmd) == "pip install flask"


def test_normalize_removes_instruction_prefix():
    assert normalize_command("RUN pip install flask") == "pip install flask"
    assert normalize_command("COPY . /app") == ". /app"
    assert normalize_command("ADD file.tar /opt") == "file.tar /opt"


def test_normalize_removes_buildkit_prefix():
    cmd = "|1 VAR=value pip install flask"
    assert normalize_command(cmd) == "pip install flask"


def test_normalize_removes_buildkit_mount():
    cmd = "--mount=type=cache,target=/root/.cache pip install flask"
    assert normalize_command(cmd) == "pip install flask"


def test_normalize_removes_nop_marker():
    cmd = "#(nop) WORKDIR /app"
    assert normalize_command(cmd) == "workdir /app"


def test_normalize_removes_inline_comments():
    cmd = "apt-get install -y python3 # install python"
    assert normalize_command(cmd) == "apt-get install -y python3"


def test_normalize_whitespace():
    cmd = "pip   install    flask   gunicorn"
    assert normalize_command(cmd) == "pip install flask gunicorn"


# =============================================================================
# parse tests
# =============================================================================


def test_parse_simple_dockerfile():
    content = """
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
"""
    df = parse(content)

    assert df.is_multistage is False
    assert df.stage_count == 1
    assert df.layer_creating_instruction_count == 3  # 2 COPY + 1 RUN
    assert df.final_base_image == "python"


def test_parse_multistage():
    content = """
FROM node:18 AS frontend
WORKDIR /frontend
COPY package.json .
RUN npm install

FROM python:3.11 AS backend
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:3.11-slim
COPY --from=frontend /frontend/dist /app/static
COPY --from=backend /app /app
CMD ["gunicorn", "app:app"]
"""
    df = parse(content)

    assert df.is_multistage is True
    assert df.stage_count == 3
    assert df.final_stage.base_image == "python"
    assert df.final_stage.base_image_tag == "3.11-slim"
    assert df.layer_creating_instruction_count == 2  # 2 COPY in final stage


def test_parse_extracts_base_image_info():
    df = parse("FROM python:3.11-slim@sha256:abc123 AS builder\nRUN echo hello")

    assert df.final_stage.name == "builder"
    assert df.final_stage.base_image == "python"
    assert df.final_stage.base_image_tag == "3.11-slim"
    assert df.final_stage.base_image_digest == "sha256:abc123"


def test_parse_registry_with_port():
    df = parse("FROM registry.example.com:5000/myimage:v1")

    assert df.final_stage.base_image == "registry.example.com:5000/myimage"
    assert df.final_stage.base_image_tag == "v1"


def test_parse_to_dict():
    df = parse("FROM python:3.11\nRUN pip install flask")
    data = df.to_dict()

    assert data["is_multistage"] is False
    assert data["stage_count"] == 1
    assert data["layer_count"] == 1
    assert data["final_base_image"] == "python"


# =============================================================================
# parse_file tests
# =============================================================================


def test_parse_file_basic():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".dockerfile", delete=False) as f:
        f.write("FROM python:3.11\nRUN pip install flask")
        f.flush()

        df = parse_file(f.name)

        assert df.path == f.name
        assert df.final_base_image == "python"
        assert df.layer_creating_instruction_count == 1

    Path(f.name).unlink()


def test_parse_file_with_path_object():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".dockerfile", delete=False) as f:
        f.write("FROM alpine:latest")
        f.flush()

        df = parse_file(Path(f.name))

        assert df.final_base_image == "alpine"

    Path(f.name).unlink()


# =============================================================================
# extract_layer_commands_from_history tests
# =============================================================================


def test_extract_all_commands():
    history = [
        {"created_by": "/bin/sh -c apt-get update", "empty_layer": False},
        {"created_by": "/bin/sh -c pip install flask", "empty_layer": False},
    ]
    commands = extract_layer_commands_from_history(history)
    assert len(commands) == 2
    assert commands[0] == "apt-get update"
    assert commands[1] == "pip install flask"


def test_extract_skip_empty_layers():
    history = [
        {"created_by": "/bin/sh -c apt-get update", "empty_layer": False},
        {"created_by": "/bin/sh -c #(nop) ENV PATH=/app", "empty_layer": True},
        {"created_by": "/bin/sh -c pip install flask", "empty_layer": False},
    ]
    commands = extract_layer_commands_from_history(history)
    assert len(commands) == 2


def test_extract_last_n_commands():
    history = [
        {"created_by": "base layer 1", "empty_layer": False},
        {"created_by": "base layer 2", "empty_layer": False},
        {"created_by": "added layer 1", "empty_layer": False},
        {"created_by": "added layer 2", "empty_layer": False},
    ]
    commands = extract_layer_commands_from_history(history, added_layer_count=2)
    assert len(commands) == 2
    assert commands[0] == "added layer 1"
    assert commands[1] == "added layer 2"


# =============================================================================
# compute_command_similarity tests
# =============================================================================


def test_similarity_identical_commands():
    assert compute_command_similarity("pip install flask", "pip install flask") == 1.0


def test_similarity_containment():
    sim = compute_command_similarity("pip install flask", "pip install flask gunicorn")
    assert sim == 0.8


def test_similarity_pattern():
    sim = compute_command_similarity(
        "apt-get install -y python3", "apt-get install -y curl"
    )
    assert sim == 0.7


def test_similarity_token_overlap():
    # Both share "pip install" pattern, so they get pattern similarity of 0.7
    sim = compute_command_similarity("pip install flask", "pip install django")
    assert sim == 0.7


def test_similarity_no_match():
    sim = compute_command_similarity("completely different", "nothing in common")
    assert sim < 0.3


# =============================================================================
# find_best_dockerfile_matches tests
# =============================================================================


def test_find_exact_match():
    df = parse("FROM python:3.11\nRUN pip install flask\nRUN pip install gunicorn")

    image_commands = [
        "pip install flask",
        "pip install gunicorn",
    ]

    matches = find_best_dockerfile_matches(image_commands, [df])

    assert len(matches) == 1
    assert matches[0].confidence >= 0.9
    assert matches[0].matched_commands == 2


def test_find_best_among_multiple():
    df_node = parse("FROM node:18\nRUN npm install")
    df_python = parse("FROM python:3.11\nRUN pip install flask")

    image_commands = ["pip install flask"]

    matches = find_best_dockerfile_matches(image_commands, [df_node, df_python])

    # The Python Dockerfile should match best
    assert matches[0].dockerfile.final_base_image == "python"


def test_find_filter_by_min_confidence():
    df = parse("FROM python:3.11\nRUN completely different command")

    image_commands = ["pip install flask"]

    matches = find_best_dockerfile_matches(image_commands, [df], min_confidence=0.5)
    assert len(matches) == 0
