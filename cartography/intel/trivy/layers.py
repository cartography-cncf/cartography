"""
Registry-based layer extraction for container images using docker buildx imagetools.
"""

import json
import logging
import subprocess
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


def extract_ecr_info(image_uri: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract ECR registry and region from image reference.

    Args:
        image_uri: Full image URI (e.g., "123456789.dkr.ecr.us-east-1.amazonaws.com/repo:tag")

    Returns:
        Tuple of (registry, region) or (None, None) if not an ECR image
    """
    if ".dkr.ecr." not in image_uri or ".amazonaws.com" not in image_uri:
        return None, None

    try:
        # Extract registry (everything before first /)
        registry = image_uri.split("/")[0]
        # Extract region from registry URL
        # Format: {account}.dkr.ecr.{region}.amazonaws.com
        parts = registry.split(".")
        if len(parts) >= 5 and parts[1] == "dkr" and parts[2] == "ecr":
            region = parts[3]
            return registry, region
    except (IndexError, ValueError):
        pass

    return None, None


def get_image_platforms(image_uri: str) -> List[str]:
    """
    Get available platforms for a multi-arch image.

    Args:
        image_uri: Full image URI

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
            image_uri,
            "--format",
            "{{json .Manifest}}",
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
                        # Skip attestation manifests
                        if (
                            manifest.get("annotations", {}).get(
                                "vnd.docker.reference.type"
                            )
                            == "attestation-manifest"
                        ):
                            continue
                        platform = manifest.get("platform", {})
                        os = platform.get("os", "")
                        arch = platform.get("architecture", "")
                        # Skip unknown platforms (attestations, etc)
                        if os and arch and os != "unknown" and arch != "unknown":
                            platform_str = f"{os}/{arch}"
                            variant = platform.get("variant")
                            if variant:
                                platform_str += f"/{variant}"
                            platforms.append(platform_str)
            except json.JSONDecodeError:
                # Not a multi-arch image, likely single platform
                pass

        # If no platforms found from manifest, assume single platform linux/amd64
        if not platforms:
            platforms = ["linux/amd64"]

    except subprocess.SubprocessError as e:
        logger.warning(f"Error getting platforms for {image_uri}: {e}")
        platforms = ["linux/amd64"]  # Default fallback

    return platforms


def get_image_layers_from_registry(
    image_uri: str,
    platform: Optional[str] = None,
    auth_ecr: bool = True,
) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Get image layer diff IDs from registry using docker buildx imagetools.

    Args:
        image_uri: Full image URI (e.g., "registry.example.com/repo:tag")
        platform: Target platform (e.g., "linux/amd64"). If None, uses default.
        auth_ecr: Whether to attempt ECR authentication if it's an ECR image

    Returns:
        Tuple of (diff_ids, image_digest) or (None, None) on failure
    """
    if not check_docker_buildx_available():
        logger.warning(
            "docker buildx imagetools not available. Please install Docker with buildx support."
        )
        return None, None

    if auth_ecr:
        registry, region = extract_ecr_info(image_uri)
        if registry and region:
            if not get_registry_auth_for_ecr(registry, region):
                logger.warning(f"ECR authentication failed for {registry}")
                # Continue anyway, might have cached credentials

    try:
        cmd = [
            "docker",
            "buildx",
            "imagetools",
            "inspect",
            image_uri,
            "--format",
            "{{json .}}",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            logger.warning(f"Failed to inspect image {image_uri}: {result.stderr}")
            return None, None

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse imagetools output for {image_uri}: {e}")
            return None, None

        # docker buildx imagetools inspect output structure:
        # - .Manifest: Contains the manifest (single platform) or index (multi-platform)
        # - .Image: Contains image config data
        #   - For multi-platform: keyed by platform like {"linux/amd64": {...}, "linux/arm64": {...}}
        #   - For single-platform: direct image data {...}

        image_data = data.get("Image", {})
        manifest_data = data.get("Manifest", {})

        # Check if this is a multi-platform image by looking at the Image field structure
        if image_data and isinstance(image_data, dict):
            platform_keys = [k for k in image_data.keys() if "/" in k]

            if platform_keys:
                # Multi-platform image - Image field has platform keys
                if platform and platform in image_data:
                    # Use requested platform
                    image_data = image_data[platform]
                    logger.debug(f"Using requested platform {platform} for {image_uri}")
                elif platform_keys:
                    # Use first available platform (prefer linux/amd64 if available)
                    default_platform = (
                        "linux/amd64"
                        if "linux/amd64" in platform_keys
                        else platform_keys[0]
                    )
                    image_data = image_data[default_platform]
                    logger.debug(
                        f"Using default platform {default_platform} for {image_uri}"
                    )
                else:
                    logger.warning(
                        f"No valid platform found in multi-platform image {image_uri}"
                    )
                    return None, None
            # else: single-platform image, image_data is already the image config

        if not isinstance(image_data, dict):
            logger.warning(f"Invalid image data structure for {image_uri}")
            return None, None

        # Extract diff IDs from the selected platform's image data
        diff_ids = []
        rootfs = image_data.get("rootfs", {})
        if not rootfs:
            rootfs = image_data.get("RootFS", {})

        if "diff_ids" in rootfs:
            diff_ids = rootfs["diff_ids"]
        elif "DiffIDs" in rootfs:
            diff_ids = rootfs["DiffIDs"]

        # For image digest, we need the config digest from the manifest
        # For multi-platform images, we should look at the specific platform's manifest entry
        image_digest = ""

        # Check if manifest_data is an index (multi-platform)
        if "manifests" in manifest_data:
            # This is an index, find the matching platform manifest
            for m in manifest_data.get("manifests", []):
                m_platform = m.get("platform", {})
                platform_str = (
                    f"{m_platform.get('os', '')}/{m_platform.get('architecture', '')}"
                )
                if m_platform.get("variant"):
                    platform_str += f"/{m_platform['variant']}"

                # Match the platform we selected
                if platform and platform_str == platform:
                    image_digest = m.get("digest", "")
                    break
                elif not platform and platform_str == "linux/amd64":
                    # Default to linux/amd64
                    image_digest = m.get("digest", "")
                    break

            # If still no digest, use the first non-attestation manifest
            if not image_digest:
                for m in manifest_data.get("manifests", []):
                    if (
                        m.get("annotations", {}).get("vnd.docker.reference.type")
                        != "attestation-manifest"
                    ):
                        image_digest = m.get("digest", "")
                        break
        else:
            # Single platform manifest - get config digest directly
            config = manifest_data.get("config", {})
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
            logger.info(f"Retrieved {len(diff_ids)} layer diff IDs for {image_uri}")
            return diff_ids, image_digest
        else:
            logger.warning(f"No diff IDs found for {image_uri}")
            return None, None

    except subprocess.SubprocessError as e:
        logger.warning(f"Error inspecting image {image_uri}: {e}")
        return None, None


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
