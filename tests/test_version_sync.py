"""Every place that states the version must agree with VERSION. Run: python tests/test_version_sync.py"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def versions():
    canonical = (ROOT / "VERSION").read_text("utf-8").strip()
    hook = re.search(r'^__version__ = "([^"]+)"', (ROOT / "hooks" / "reply_shape.py").read_text("utf-8"), re.M)
    style = re.search(r"<!-- ConciseClaude ([^ ]+) -->", (ROOT / "output-styles" / "concise.md").read_text("utf-8"))
    changelog = re.search(r"^## \[?([0-9][^\]\s]*)", (ROOT / "CHANGELOG.md").read_text("utf-8"), re.M)
    return canonical, {
        "hooks/reply_shape.py __version__": hook and hook.group(1),
        "output-styles/concise.md marker": style and style.group(1),
        "CHANGELOG.md newest entry": changelog and changelog.group(1),
    }


def test_version_sites_match():
    canonical, sites = versions()
    assert re.fullmatch(r"\d+\.\d+\.\d+", canonical), f"VERSION is not semver: {canonical!r}"
    drift = {k: v for k, v in sites.items() if v != canonical}
    assert not drift, f"VERSION is {canonical} but: {drift}"


if __name__ == "__main__":
    try:
        test_version_sites_match()
        print("PASS test_version_sites_match")
    except AssertionError as exc:
        print(f"FAIL test_version_sites_match: {exc}")
        sys.exit(1)
