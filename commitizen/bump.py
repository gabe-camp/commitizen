import re
from collections import defaultdict
from itertools import zip_longest
from packaging.version import Version
from typing import List, Optional

MAJOR = "MAJOR"
MINOR = "MINOR"
PATCH = "PATCH"
conventional_commits_pattern = r"^(BREAKING CHANGE|feat)"
conventional_commits_map = {"BREAKING CHANGE": MAJOR, "feat": MINOR}


def find_increment(
    messages: List[str],
    regex: str = conventional_commits_pattern,
    increments_map: dict = conventional_commits_map,
) -> str:

    # Most important cases are major and minor.
    # Everything else will be considered patch.
    increments_map_default = defaultdict(lambda: PATCH, increments_map)
    pattern = re.compile(regex)
    increment = PATCH

    for message in messages:
        result = pattern.search(message)
        if not result:
            continue
        found_keyword = result.group(0)
        increment = increments_map_default[found_keyword]

    return increment


def prerelease_generator(current_version: str, prerelease: Optional[str] = None) -> str:
    """
    X.YaN   # Alpha release
    X.YbN   # Beta release
    X.YrcN  # Release Candidate
    X.Y  # Final

    This function might return something like 'alpha1'
    but it will be handled by Version.
    """
    if not prerelease:
        return ""

    version = Version(current_version)
    new_prerelease: int = 0
    if version.is_prerelease and prerelease.startswith(version.pre[0]):
        prev_prerelease: int = list(version.pre)[1]
        new_prerelease = prev_prerelease + 1
    pre_version = f"{prerelease}{new_prerelease}"
    return pre_version


def semver_generator(current_version: str, increment: str = None) -> str:
    version = Version(current_version)
    prev_release = list(version.release)
    increments = [MAJOR, MINOR, PATCH]
    increments_version = dict(zip_longest(increments, prev_release, fillvalue=0))

    # This flag means that current version
    # must remove its prerelease tag,
    # so it doesn't matter the increment.
    # Example: 1.0.0a0 with PATCH/MINOR -> 1.0.0
    if not version.is_prerelease:

        if increment == MAJOR:
            increments_version[MAJOR] += 1
            increments_version[MINOR] = 0
            increments_version[PATCH] = 0
        elif increment == MINOR:
            increments_version[MINOR] += 1
            increments_version[PATCH] = 0
        elif increment == PATCH:
            increments_version[PATCH] += 1

    return str(
        f"{increments_version['MAJOR']}."
        f"{increments_version['MINOR']}."
        f"{increments_version['PATCH']}"
    )


def generate_version(
    current_version: str, increment: str = None, prerelease: Optional[str] = None
) -> Version:
    """Based on the given increment a proper semver will be generated.

    For now the rules and versioning scheme is based on
    python's PEP 0440.
    More info: https://www.python.org/dev/peps/pep-0440/

    Example:
        PATCH 1.0.0 -> 1.0.1
        MINOR 1.0.0 -> 1.1.0
        MAJOR 1.0.0 -> 2.0.0
    """
    pre_version = prerelease_generator(current_version, prerelease=prerelease)
    semver = semver_generator(current_version, increment=increment)
    # TODO: post version
    # TODO: dev version
    return Version(f"{semver}{pre_version}")
