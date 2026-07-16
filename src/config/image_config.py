"""Image configuration for OpenRAG container images."""

import os
import platform

# ---------------------------------------------------------------------------
# Architecture detection
# ---------------------------------------------------------------------------

def _detect_arch() -> str:
    """Return the normalised architecture string for the current machine.

    Maps ``platform.machine()`` values to the identifiers used in image tags:
    - ``x86_64``  -> ``""``   (no suffix — Docker Hub fat manifests cover amd64)
    - ``aarch64`` -> ``""``   (no suffix — Docker Hub fat manifests cover arm64)
    - ``ppc64le`` -> ``"ppc64le"``
    """
    machine = platform.machine().lower()
    if machine == "ppc64le":
        return "ppc64le"
    return ""

#: Recognised architecture identifiers.
SUPPORTED_ARCHITECTURES: tuple[str, ...] = ("amd64", "arm64", "ppc64le")

#: Target architecture suffix.  Set IMAGE_ARCH to override auto-detection.
#: Leave empty for a fat-manifest / architecture-agnostic reference.
IMAGE_ARCH: str = os.getenv("IMAGE_ARCH", _detect_arch())

# ---------------------------------------------------------------------------
# Registry & organisation
# ---------------------------------------------------------------------------

#: Base Artifactory URL for ppc64le images.  Set via ARTIFACTORY_IMAGE_URL env var.
#: On non-ppc64le platforms this is empty and unused.
_ARTIFACTORY_BASE = "docker-na-public.artifactory.swg-devops.com/hyc-cpd-skywalker-team-lakehouse-on-prem-docker-local/power"
ARTIFACTORY_IMAGE_URL: str = os.getenv(
    "ARTIFACTORY_IMAGE_URL",
    _ARTIFACTORY_BASE if IMAGE_ARCH == "ppc64le" else "",
)

# ---------------------------------------------------------------------------
# Registry & organisation (derived from ARTIFACTORY_IMAGE_URL on ppc64le)
# ---------------------------------------------------------------------------

if IMAGE_ARCH == "ppc64le" and ARTIFACTORY_IMAGE_URL:
    _default_registry = ARTIFACTORY_IMAGE_URL.split("/")[0]
    _default_org = "/".join(ARTIFACTORY_IMAGE_URL.split("/")[1:]) + "/langflowai"
else:
    _default_registry = "docker.io"
    _default_org = "langflowai"

#: Container registry host.  Override via IMAGE_REGISTRY env var.
IMAGE_REGISTRY: str = os.getenv("IMAGE_REGISTRY", _default_registry)

#: Organisation / namespace within the registry.  Override via IMAGE_ORG.
IMAGE_ORG: str = os.getenv("IMAGE_ORG", _default_org)

# ---------------------------------------------------------------------------
# Per-service image overrides for ppc64le
# ---------------------------------------------------------------------------
# On ppc64le each service lives at a different path/tag in Artifactory.
# These are written to .env so docker-compose resolves them correctly.

_ppc64le_image_overrides: dict[str, str] = {
    "OPENSEARCH_IMAGE": f"{_ARTIFACTORY_BASE}/opensearch/cnos:3.6.0-052826",
    "OPENSEARCH_DASHBOARDS_IMAGE": f"{_ARTIFACTORY_BASE}/opensearch-dashboards/cnos-dashboards:3.6.0-052726",
    "LANGFLOW_IMAGE": f"{_ARTIFACTORY_BASE}/langflowai/openrag-langflow:1.9.0-070826",
} if IMAGE_ARCH == "ppc64le" else {}

# Expose as module-level constants (env var override always wins)
OPENSEARCH_IMAGE: str = os.getenv(
    "OPENSEARCH_IMAGE",
    _ppc64le_image_overrides.get("OPENSEARCH_IMAGE", ""),
)
OPENSEARCH_DASHBOARDS_IMAGE: str = os.getenv(
    "OPENSEARCH_DASHBOARDS_IMAGE",
    _ppc64le_image_overrides.get(
        "OPENSEARCH_DASHBOARDS_IMAGE",
        "docker.io/opensearchproject/opensearch-dashboards:3.0.0",
    ),
)
LANGFLOW_IMAGE: str = os.getenv(
    "LANGFLOW_IMAGE",
    _ppc64le_image_overrides.get("LANGFLOW_IMAGE", ""),
)

# ---------------------------------------------------------------------------
# Image names
# ---------------------------------------------------------------------------

IMAGE_NAME_BACKEND: str = "openrag-backend"
IMAGE_NAME_FRONTEND: str = "openrag-frontend"
IMAGE_NAME_LANGFLOW: str = "openrag-langflow"
IMAGE_NAME_OPENSEARCH: str = "openrag-opensearch"
IMAGE_NAME_DASHBOARDS: str = "openrag-dashboards"

#: All OpenRAG-owned image short names.
OPENRAG_IMAGE_NAMES: tuple[str, ...] = (
    IMAGE_NAME_BACKEND,
    IMAGE_NAME_FRONTEND,
    IMAGE_NAME_LANGFLOW,
    IMAGE_NAME_OPENSEARCH,
    IMAGE_NAME_DASHBOARDS,
)

#: Third-party images referenced in the compose stack (used for cleanup
#: allow-listing).
THIRD_PARTY_IMAGE_REPOS: tuple[str, ...] = (
    "langflow/langflow",
    "opensearchproject/opensearch",
    "opensearchproject/opensearch-dashboards",
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def image_repo(name: str) -> str:
    """Return the fully-qualified repository path (without tag) for *name*.

    Example::

        image_repo("openrag-backend")
        # -> "docker.io/langflowai/openrag-backend"
    """
    return f"{IMAGE_REGISTRY}/{IMAGE_ORG}/{name}"


def image_tag(version: str, arch: str = IMAGE_ARCH) -> str:
    """Return the image tag for *version*, optionally suffixed with *arch*.

    If *arch* is empty or ``"multi"``, no suffix is added and the plain
    version string is returned (suitable for a fat-manifest reference).

    Examples::

        image_tag("0.5.1")             # -> "0.5.1"
        image_tag("0.5.1", "ppc64le") # -> "0.5.1-ppc64le"
        image_tag("0.5.1", "arm64")   # -> "0.5.1-arm64"
    """
    if arch and arch != "multi":
        return f"{version}-{arch}"
    return version


def image_ref(name: str, version: str = "latest", arch: str = IMAGE_ARCH) -> str:
    """Return the fully-qualified image reference including tag.

    Args:
        name:    Short image name (e.g. ``"openrag-backend"``).
        version: Version / tag string (e.g. ``"0.5.1"`` or ``"latest"``).
        arch:    Architecture suffix.  Defaults to :data:`IMAGE_ARCH`.

    Example::

        image_ref("openrag-backend", "0.5.1", "ppc64le")
        # -> "docker.io/langflowai/openrag-backend:0.5.1-ppc64le"

        image_ref("openrag-backend", "0.5.1")
        # -> "docker.io/langflowai/openrag-backend:0.5.1"
    """
    return f"{image_repo(name)}:{image_tag(version, arch)}"


def all_openrag_repos() -> tuple[str, ...]:
    """Return the set of all OpenRAG-owned repository paths (no tag).

    Includes both the standard path and the legacy path without a registry
    prefix so that callers can match images already present locally under
    either form.
    """
    standard = tuple(image_repo(n) for n in OPENRAG_IMAGE_NAMES)
    # Short form (e.g. "langflowai/openrag-backend") for matching locally-
    # pulled images that may omit the registry prefix.
    short = tuple(f"{IMAGE_ORG}/{n}" for n in OPENRAG_IMAGE_NAMES)
    return standard + short + THIRD_PARTY_IMAGE_REPOS
