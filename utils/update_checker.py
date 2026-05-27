from dataclasses import dataclass
import json
from typing import Callable, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

from packaging.version import InvalidVersion, Version


GITHUB_LATEST_RELEASE_URL = (
    "https://api.github.com/repos/matiasrmb/estacionamiento-central/releases/latest"
)


@dataclass(frozen=True)
class UpdateCheckResult:
    update_available: bool
    current_version: str
    latest_version: Optional[str] = None
    release_url: Optional[str] = None
    error: Optional[str] = None


def normalize_version(version: str) -> str:
    return version.strip().lstrip("vV")


def is_newer_version(latest_version: str, current_version: str) -> bool:
    try:
        return Version(normalize_version(latest_version)) > Version(
            normalize_version(current_version)
        )
    except InvalidVersion:
        return False


def fetch_latest_release() -> dict:
    request = Request(
        GITHUB_LATEST_RELEASE_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "EstacionamientoCentral-UpdateChecker",
        },
    )

    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def check_for_update(
    current_version: str,
    fetch_release: Callable[[], dict] = fetch_latest_release,
) -> UpdateCheckResult:
    try:
        release = fetch_release()
        if not isinstance(release, dict):
            return UpdateCheckResult(False, current_version)

        if release.get("prerelease"):
            return UpdateCheckResult(False, current_version)

        tag_name = release.get("tag_name", "")
        latest_version = normalize_version(tag_name)
        release_url = release.get("html_url")

        if not latest_version or not release_url:
            return UpdateCheckResult(False, current_version)

        if is_newer_version(latest_version, current_version):
            return UpdateCheckResult(
                True,
                current_version,
                latest_version=latest_version,
                release_url=release_url,
            )

        return UpdateCheckResult(
            False,
            current_version,
            latest_version=latest_version,
            release_url=release_url,
        )
    except Exception as exc:
        return UpdateCheckResult(False, current_version, error=str(exc))
