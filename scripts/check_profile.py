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


def main():
    errors = []
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
