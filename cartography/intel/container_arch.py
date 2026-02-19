from __future__ import annotations

import re

# Canonical architecture source values for runtime containers.
ARCH_SOURCE_RUNTIME_API_EXACT = "runtime_api_exact"
ARCH_SOURCE_IMAGE_DIGEST_EXACT = "image_digest_exact"
ARCH_SOURCE_TASK_DEFINITION_HINT = "task_definition_hint"
ARCH_SOURCE_CLUSTER_HINT = "cluster_hint"
ARCH_SOURCE_IMAGE_REF_HINT = "image_ref_hint"


_CANONICAL_BY_ALIAS = {
    "amd64": "amd64",
    "x86_64": "amd64",
    "x64": "amd64",
    "x86-64": "amd64",
    "arm64": "arm64",
    "aarch64": "arm64",
    "arm64/v8": "arm64",
    "arm": "arm",
    "arm/v7": "arm",
    "armv7": "arm",
    "armv7l": "arm",
    "386": "386",
    "i386": "386",
    "x86": "386",
    "ppc64le": "ppc64le",
    "s390x": "s390x",
    "riscv64": "riscv64",
}

_CANONICAL_VALUES = {
    "amd64",
    "arm64",
    "arm",
    "386",
    "ppc64le",
    "s390x",
    "riscv64",
    "unknown",
}

_ARMV7_PATTERN = re.compile(r"armv7[a-z0-9]*", re.IGNORECASE)


def normalize_architecture(raw: str | None) -> str:
    if raw is None:
        return "unknown"
    value = raw.strip()
    if not value:
        return "unknown"

    lowered = value.lower()
    if lowered in _CANONICAL_BY_ALIAS:
        return _CANONICAL_BY_ALIAS[lowered]
    if lowered in _CANONICAL_VALUES:
        return lowered
    if _ARMV7_PATTERN.fullmatch(lowered):
        return "arm"
    return "unknown"


def normalize_architecture_with_raw(raw: str | None) -> tuple[str, str | None]:
    if raw is None:
        return "unknown", None
    return normalize_architecture(raw), raw


def guess_architecture_from_image_ref(ref: str | None) -> str:
    if not ref:
        return "unknown"
    lowered = ref.lower()

    # Handle common explicit platform forms first.
    if "linux/arm64/v8" in lowered or "arm64/v8" in lowered:
        return "arm64"
    if "linux/amd64" in lowered:
        return "amd64"
    if "linux/arm/v7" in lowered or "arm/v7" in lowered:
        return "arm"

    # Tokenized checks for registry/repo naming hints.
    tokens = re.split(r"[^a-z0-9_./-]+", lowered)
    for token in tokens:
        arch = normalize_architecture(token)
        if arch != "unknown":
            return arch

    if "armv7" in lowered:
        return "arm"
    return "unknown"
