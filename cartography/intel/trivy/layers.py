"""
Registry-based layer extraction for container images using docker buildx imagetools.
"""

import json
import logging
import subprocess
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

logger = logging.getLogger(__name__)


def check_docker_buildx_available() -> bool:
    """Check if docker buildx imagetools is available."""
    try:
        result = subprocess.run(
            ["docker", "buildx", "imagetools", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def get_registry_auth_for_ecr(registry: str, region: str) -> bool:
    """
    Authenticate with ECR registry using AWS CLI.

    Args:
        registry: ECR registry URL (e.g., "123456789.dkr.ecr.us-east-1.amazonaws.com")
        region: AWS region

    Returns:
        True if authentication succeeded, False otherwise
    """
    try:
        # Get ECR login password
        get_password_cmd = ["aws", "ecr", "get-login-password", "--region", region]
        password_result = subprocess.run(
            get_password_cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if password_result.returncode != 0:
            logger.warning(
                f"Failed to get ECR login password: {password_result.stderr}"
            )
            return False

        # Login to docker
        login_cmd = [
            "docker",
            "login",
            "--username",
            "AWS",
            "--password-stdin",
            registry,
        ]
        login_result = subprocess.run(
            login_cmd,
            input=password_result.stdout,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if login_result.returncode != 0:
            logger.warning(f"Failed to login to ECR: {login_result.stderr}")
            return False

        return True
    except subprocess.SubprocessError as e:
        logger.warning(f"Error authenticating with ECR: {e}")
        return False


def extract_ecr_info(image_ref: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract ECR registry and region from image reference.

    Args:
        image_ref: Full image reference (e.g., "123456789.dkr.ecr.us-east-1.amazonaws.com/repo:tag")

    Returns:
        Tuple of (registry, region) or (None, None) if not an ECR image
    """
    if ".dkr.ecr." not in image_ref or ".amazonaws.com" not in image_ref:
        return None, None

    try:
        # Extract registry (everything before first /)
        registry = image_ref.split("/")[0]
        # Extract region from registry URL
        # Format: {account}.dkr.ecr.{region}.amazonaws.com
        parts = registry.split(".")
        if len(parts) >= 5 and parts[1] == "dkr" and parts[2] == "ecr":
            region = parts[3]
            return registry, region
    except (IndexError, ValueError):
        pass

    return None, None


def get_image_platforms(image_ref: str) -> List[str]:
    """
    Get available platforms for a multi-arch image.

    Args:
        image_ref: Full image reference

    Returns:
        List of platform strings (e.g., ["linux/amd64", "linux/arm64"])
    """
    platforms = []

    try:
        # First, check if this is a multi-arch image by inspecting the index
        cmd = [
            "docker",
            "buildx",
            "imagetools",
            "inspect",
            image_ref,
            "--format",
            "{{json .Index}}",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0 and result.stdout.strip():
            try:
                index_data = json.loads(result.stdout)
                if index_data and "manifests" in index_data:
                    for manifest in index_data["manifests"]:
                        platform = manifest.get("platform", {})
                        os = platform.get("os", "")
                        arch = platform.get("architecture", "")
                        if os and arch:
                            platform_str = f"{os}/{arch}"
                            variant = platform.get("variant")
                            if variant:
                                platform_str += f"/{variant}"
                            platforms.append(platform_str)
            except json.JSONDecodeError:
                # Not a multi-arch image, likely single platform
                pass

        # If no platforms found from index, assume single platform linux/amd64
        if not platforms:
            platforms = ["linux/amd64"]

    except subprocess.SubprocessError as e:
        logger.warning(f"Error getting platforms for {image_ref}: {e}")
        platforms = ["linux/amd64"]  # Default fallback

    return platforms


def get_image_layers_from_registry(
    image_ref: str,
    platform: Optional[str] = None,
    auth_ecr: bool = True,
) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Get image layer diff IDs from registry using docker buildx imagetools.

    Args:
        image_ref: Full image reference (e.g., "registry.example.com/repo:tag")
        platform: Target platform (e.g., "linux/amd64"). If None, uses default.
        auth_ecr: Whether to attempt ECR authentication if it's an ECR image

    Returns:
        Tuple of (diff_ids, image_digest) or (None, None) on failure
    """
    # Check if docker buildx is available
    if not check_docker_buildx_available():
        logger.warning(
            "docker buildx imagetools not available. Please install Docker with buildx support."
        )
        return None, None

    # Handle ECR authentication if needed
    if auth_ecr:
        registry, region = extract_ecr_info(image_ref)
        if registry and region:
            if not get_registry_auth_for_ecr(registry, region):
                logger.warning(f"ECR authentication failed for {registry}")
                # Continue anyway, might have cached credentials

    try:
        # Build the command
        cmd = [
            "docker",
            "buildx",
            "imagetools",
            "inspect",
            image_ref,
            "--format",
            "{{json .}}",
        ]

        if platform:
            cmd.extend(["--platform", platform])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            logger.warning(f"Failed to inspect image {image_ref}: {result.stderr}")
            return None, None

        # Parse the JSON output
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse imagetools output for {image_ref}: {e}")
            return None, None

        # Extract diff IDs from Image.RootFS.DiffIDs
        diff_ids = []
        image_data = data.get("Image", {})
        rootfs = image_data.get("RootFS", {})

        if "DiffIDs" in rootfs:
            diff_ids = rootfs["DiffIDs"]
        elif "diff_ids" in rootfs:
            diff_ids = rootfs["diff_ids"]

        # Extract image digest from manifest
        manifest = data.get("Manifest", {})
        config = manifest.get("config", {})
        image_digest = config.get("digest", "")

        if not image_digest:
            # Try to get digest from image data
            repo_digests = image_data.get("RepoDigests", [])
            if repo_digests:
                # Extract digest from first repo digest
                first_digest = repo_digests[0]
                if "@" in first_digest:
                    image_digest = first_digest.split("@")[1]

        if diff_ids:
            logger.info(f"Retrieved {len(diff_ids)} layer diff IDs for {image_ref}")
            return diff_ids, image_digest
        else:
            logger.warning(f"No diff IDs found for {image_ref}")
            return None, None

    except subprocess.SubprocessError as e:
        logger.warning(f"Error inspecting image {image_ref}: {e}")
        return None, None


def get_image_layers_multi_platform(
    image_ref: str,
    auth_ecr: bool = True,
) -> Dict[str, Tuple[List[str], Optional[str]]]:
    """
    Get image layers for all available platforms.

    Args:
        image_ref: Full image reference
        auth_ecr: Whether to attempt ECR authentication

    Returns:
        Dictionary mapping platform to (diff_ids, image_digest)
    """
    results = {}

    # Get available platforms
    platforms = get_image_platforms(image_ref)
    logger.info(f"Found platforms for {image_ref}: {platforms}")

    # Get layers for each platform
    for platform in platforms:
        diff_ids, digest = get_image_layers_from_registry(
            image_ref, platform=platform, auth_ecr=auth_ecr
        )
        if diff_ids:
            results[platform] = (diff_ids, digest)

    return results


def compute_image_lineage(
    parent_diff_ids: List[str],
    child_diff_ids: List[str],
) -> bool:
    """
    Determine if child image is built from parent image based on shared layers.

    Args:
        parent_diff_ids: Ordered list of parent image layer diff IDs
        child_diff_ids: Ordered list of child image layer diff IDs

    Returns:
        True if child is built from parent (parent layers are prefix of child)
    """
    if not parent_diff_ids or not child_diff_ids:
        return False

    if len(parent_diff_ids) > len(child_diff_ids):
        return False

    # Check if parent layers are a prefix of child layers
    return child_diff_ids[: len(parent_diff_ids)] == parent_diff_ids
