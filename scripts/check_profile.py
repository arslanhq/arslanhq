#!/usr/bin/env python3
"""Read-only checks for Mohammad Arslan's personal GitHub profile.

Protects public portfolio identity. Never reads secrets or private project files.
"""
from pathlib import Path
from urllib.parse import urlsplit
import os
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
EXPECTED_ENV = {
    "GITHUB_REPOSITORY": "arslanhq/arslanhq",
    "GITHUB_REPOSITORY_ID": "698426651",
    "GITHUB_REPOSITORY_OWNER_ID": "135918375",
}


def verify_workflows_are_read_only(problems):
    """Check simple CI safety invariants, not a substitute for human review."""
    workflow_dir = ROOT / ".github" / "workflows"
    files = sorted((*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")))
    if not files:
        problems.append("missing GitHub Actions workflows")
    for workflow in files:
        source = workflow.read_text(encoding="utf-8")
        if not re.search(r"(?m)^permissions:\s*\n\s+contents:\s*read\s*$", source):
            problems.append(f"{workflow.name}: missing explicit read-only token scope")
        if re.search(r"(?m)^\s*(?:pull_request_target|workflow_run)\s*:", source):
            problems.append(f"{workflow.name}: privileged workflow trigger")
        if re.search(r"(?m)^\s*permissions:\s*write-all\s*$", source):
            problems.append(f"{workflow.name}: overly broad write permissions")
        if re.search(
            r"(?m)^\s*(?:actions|attestations|checks|contents|deployments|discussions|id-token|issues|models|packages|pages|pull-requests|security-events|statuses):\s*write\s*(?:#.*)?$",
            source,
        ):
            problems.append(f"{workflow.name}: write-scoped GITHUB_TOKEN is not permitted")
        if re.search(r"(?m)^\s*runs-on:\s*.*self-hosted", source):
            problems.append(f"{workflow.name}: unexpected self-hosted runner")
        for action in re.findall(r"(?m)^\s*uses:\s*([^\s#]+)", source):
            if not re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", action):
                problems.append(f"{workflow.name}: unpinned action {action}")
        if "actions/checkout@" in source and "persist-credentials: false" not in source:
            problems.append(f"{workflow.name}: checkout must not persist credentials")


def main():
    errors = []
    verify_workflows_are_read_only(errors)
    for key, expected in EXPECTED_ENV.items():
        actual = os.environ.get(key)
        if actual and actual != expected:
            errors.append(f"wrong GitHub identity: {key} does not match the intended personal account")
    body = README.read_text(encoding="utf-8")
    if not body.startswith('<div align="center">\n\n# Mohammad Arslan'):
        errors.append("incorrect founder name or missing profile header")
    if "Mohammed Arslan" in body or "ZoroTV" in body:
        errors.append("outdated founder identity visible")
    required = [
        "https://github.com/DataVistaStudio",
        "https://github.com/DataVistaStudio/DataVistaStudio",
        "NEWSROOM",
        "Market.961.MENU",
        "https://market.961.menu/",
        "https://github.com/DataVistaStudio/DataVistaStudio/blob/main/portfolio/observatories.md",
        "https://github.com/DataVistaStudio/DataVistaStudio/blob/main/docs/COLLABORATION.md",
    ]
    for item in required:
        if item not in body:
            errors.append(f"missing required portfolio reference: {item}")
    images = re.findall(r'<img\s+src="([^"]+)"', body)
    expected_art = "https://datavista.studio/assets/portfolio-20261122/cards/"
    names = {x.rsplit("/", 1)[-1] for x in images if x.startswith(expected_art)}
    expected_jpg = {"newsroom.jpg", "market-961-menu.jpg", "people-report.jpg", "experts2.jpg", "cr-multiview.jpg", "satr-academy.jpg", "ebook.jpg", "stock.jpg", "961-menu.jpg", "talk.jpg"}
    if names != expected_jpg:
        errors.append("ten approved image-based project cards have changed unexpectedly")
    editorial_prefix = "https://raw.githubusercontent.com/DataVistaStudio/DataVistaStudio/main/media/cards/"
    expected_vectors = {"observatories.svg", "flashnews.svg", "economy-desk.svg", "news-map.svg", "aparat.svg", "jobvista.svg"}
    vectors = {url.rsplit("/", 1)[-1] for url in images if url.startswith(editorial_prefix)}
    if vectors != expected_vectors:
        errors.append("six curated founder editorial artworks are incomplete")
    if len(images) != 16:
        errors.append("unexpected image count in founder profile")
    if any(urlsplit(x).scheme != "https" for x in images):
        errors.append("non-HTTPS project image")
    # Prevent a public profile edit from overstating a product launch or access.
    expected_access = {
        "Market.961.MENU": "Preparing for launch",
        "CR Multiview": "Restricted",
        "Al Mayadeen Talk": "Restricted",
        "DataVista Stock": "Preview",
        "JOBVISTA": "Concept",
        "SATR Academy": "Public catalogue",
        "EBOOK Library": "Public catalogue",
    }
    for project, label in expected_access.items():
        marker = f"<strong>{project}</strong> · {label}"
        if marker not in body:
            errors.append(f"incorrect or missing launch/access label: {project}")
    for expected in (
        "https://market.961.menu/",
        "https://datavista.studio/cr/",
        "https://meet.almayadeen.online/",
        "https://datavista.studio/stock/",
    ):
        if expected not in body:
            errors.append(f"missing canonical public destination: {expected}")
    if "not screenshots or promises of production functionality" not in body:
        errors.append("portfolio illustration disclaimer missing")
    if errors:
        print("FOUNDER_PROFILE_FAIL", len(errors))
        for problem in errors:
            print("-", problem)
        return 1
    print("FOUNDER_PROFILE_PASS | correct account ID | 16 approved project images | company links")
    return 0


if __name__ == "__main__":
    sys.exit(main())
