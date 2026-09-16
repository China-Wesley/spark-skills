#!/usr/bin/env python3
"""Validate a daily-app-concept output directory using only the Python stdlib."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any


REQUIRED_DOCS = ("research.md", "concept.md", "visual-system.md", "manifest.json")
REQUIRED_ROLES = {"problem", "solution", "core-screen", "state-change", "outcome"}
CONCEPT_TEXT_FIELDS = (
    "name",
    "one_sentence",
    "target_user",
    "trigger",
    "core_action",
    "result",
    "core_screen",
    "monetization_hypothesis",
    "competition_risk",
)


def add_missing_text(container: dict[str, Any], fields: tuple[str, ...], prefix: str, errors: list[str]) -> None:
    for field in fields:
        value = container.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{prefix}.{field} must be a non-empty string")


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("invalid PNG signature or IHDR")
    width, height = struct.unpack(">II", header[16:24])
    if width <= 0 or height <= 0:
        raise ValueError("invalid PNG dimensions")
    return width, height


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_source(item: Any, label: str, errors: list[str], require_scope: bool = False) -> None:
    if not isinstance(item, dict):
        errors.append(f"{label} must be an object")
        return
    required = ["url", "accessed", "summary"]
    if require_scope:
        required.append("scope")
    for field in required:
        value = item.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{label}.{field} must be a non-empty string")
    url = item.get("url")
    if isinstance(url, str) and url and not re.match(r"^https?://", url):
        errors.append(f"{label}.url must start with http:// or https://")


def validate(output_dir: Path) -> dict[str, Any]:
    root = output_dir.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if not root.is_dir():
        return {"ok": False, "output_dir": str(root), "errors": ["output directory does not exist"], "warnings": []}

    for name in REQUIRED_DOCS:
        path = root / name
        if not path.is_file():
            errors.append(f"missing required file: {name}")
        elif path.stat().st_size == 0:
            errors.append(f"required file is empty: {name}")

    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return {"ok": False, "output_dir": str(root), "errors": errors, "warnings": warnings}

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"manifest.json is unreadable: {exc}")
        return {"ok": False, "output_dir": str(root), "errors": errors, "warnings": warnings}

    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    date = manifest.get("date")
    if not isinstance(date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        errors.append("date must use YYYY-MM-DD")
    status = manifest.get("status")
    if status not in {"draft", "complete"}:
        errors.append("status must be draft or complete")
    elif status == "draft":
        warnings.append("status is draft; change to complete only after final review")

    concept = manifest.get("concept")
    if not isinstance(concept, dict):
        errors.append("concept must be an object")
        concept = {}
    add_missing_text(concept, CONCEPT_TEXT_FIELDS, "concept", errors)
    flow = concept.get("flow")
    if not isinstance(flow, list) or not 3 <= len(flow) <= 5 or any(not isinstance(x, str) or not x.strip() for x in flow):
        errors.append("concept.flow must contain 3 to 5 non-empty steps")
    mvp = concept.get("mvp")
    if not isinstance(mvp, list) or len(mvp) < 2 or any(not isinstance(x, str) or not x.strip() for x in mvp):
        errors.append("concept.mvp must contain at least 2 non-empty items")
    exclusions = concept.get("exclusions")
    if not isinstance(exclusions, list) or len(exclusions) < 2 or any(not isinstance(x, str) or not x.strip() for x in exclusions):
        errors.append("concept.exclusions must contain at least 2 non-empty items")

    evidence = manifest.get("evidence")
    if not isinstance(evidence, dict):
        errors.append("evidence must be an object")
        evidence = {}
    direct = evidence.get("direct_user_feedback")
    if not isinstance(direct, list) or len(direct) < 2:
        errors.append("evidence.direct_user_feedback must contain at least 2 sources")
    else:
        for index, item in enumerate(direct):
            validate_source(item, f"evidence.direct_user_feedback[{index}]", errors, require_scope=True)
            if isinstance(item, dict) and (not isinstance(item.get("published"), str) or not item.get("published", "").strip()):
                errors.append(f"evidence.direct_user_feedback[{index}].published must be a non-empty string")
    market = evidence.get("market_proof")
    if not isinstance(market, list) or len(market) < 1:
        errors.append("evidence.market_proof must contain at least 1 source")
    else:
        for index, item in enumerate(market):
            validate_source(item, f"evidence.market_proof[{index}]", errors, require_scope=True)
    official = evidence.get("official_sources")
    if not isinstance(official, list) or len(official) < 1:
        errors.append("evidence.official_sources must contain at least 1 source")
    else:
        for index, item in enumerate(official):
            validate_source(item, f"evidence.official_sources[{index}]", errors)
    inferences = evidence.get("inferences")
    if not isinstance(inferences, list) or len(inferences) < 1 or any(not isinstance(x, str) or not x.strip() for x in inferences):
        errors.append("evidence.inferences must contain at least 1 explicit inference")

    visual = manifest.get("visual")
    if not isinstance(visual, dict):
        errors.append("visual must be an object")
        visual = {}
    add_missing_text(visual, ("style_summary",), "visual", errors)
    mappings = visual.get("mappings")
    if not isinstance(mappings, list) or len(mappings) < 3:
        errors.append("visual.mappings must contain at least 3 mappings")
    else:
        for index, mapping in enumerate(mappings):
            if not isinstance(mapping, dict):
                errors.append(f"visual.mappings[{index}] must be an object")
                continue
            add_missing_text(
                mapping,
                ("source_clue", "design_primitive", "component", "purpose"),
                f"visual.mappings[{index}]",
                errors,
            )
    assets_used = visual.get("third_party_assets_used")
    third_party_assets = visual.get("third_party_assets")
    if assets_used is not False and assets_used is not True:
        errors.append("visual.third_party_assets_used must be true or false")
    elif assets_used is True:
        if not isinstance(third_party_assets, list) or not third_party_assets:
            errors.append("third-party assets require source_url, license and usage records")
        else:
            for index, item in enumerate(third_party_assets):
                if not isinstance(item, dict):
                    errors.append(f"visual.third_party_assets[{index}] must be an object")
                    continue
                add_missing_text(item, ("source_url", "license", "usage"), f"visual.third_party_assets[{index}]", errors)
    elif third_party_assets not in (None, []):
        warnings.append("third_party_assets_used is false but third_party_assets is not empty")

    image_entries = manifest.get("images")
    dimensions: list[tuple[int, int]] = []
    hashes: list[str] = []
    roles: set[str] = set()
    listed_files: list[str] = []
    if not isinstance(image_entries, list) or not 5 <= len(image_entries) <= 7:
        errors.append("images must contain 5 to 7 entries")
        image_entries = []
    for index, entry in enumerate(image_entries):
        if not isinstance(entry, dict):
            errors.append(f"images[{index}] must be an object")
            continue
        filename = entry.get("file")
        role = entry.get("role")
        if not isinstance(filename, str) or not filename.strip():
            errors.append(f"images[{index}].file must be a non-empty string")
            continue
        if not isinstance(role, str) or not role.strip():
            errors.append(f"images[{index}].role must be a non-empty string")
        else:
            roles.add(role)
        if filename in listed_files:
            errors.append(f"duplicate image path in manifest: {filename}")
        listed_files.append(filename)
        path = (root / filename).resolve()
        if path != root and root not in path.parents:
            errors.append(f"image path escapes output directory: {filename}")
            continue
        if path.suffix.lower() != ".png":
            errors.append(f"image must be PNG: {filename}")
        if not path.is_file():
            errors.append(f"missing image: {filename}")
            continue
        try:
            actual = png_dimensions(path)
            dimensions.append(actual)
            hashes.append(sha256(path))
        except (OSError, ValueError) as exc:
            errors.append(f"unreadable PNG {filename}: {exc}")
            continue
        declared = (entry.get("width"), entry.get("height"))
        if declared != actual:
            errors.append(f"dimension mismatch for {filename}: declared={declared}, actual={actual}")

    missing_roles = sorted(REQUIRED_ROLES - roles)
    if missing_roles:
        errors.append(f"missing required image roles: {missing_roles}")
    if dimensions and len(set(dimensions)) != 1:
        errors.append(f"image dimensions are inconsistent: {sorted(set(dimensions))}")
    if hashes and len(hashes) != len(set(hashes)):
        errors.append("image hashes are not unique")

    images_dir = root / "images"
    actual_image_files = sorted(str(path.relative_to(root)) for path in images_dir.glob("*.png")) if images_dir.is_dir() else []
    if sorted(listed_files) != actual_image_files:
        errors.append(f"manifest image list does not match images directory: manifest={sorted(listed_files)} actual={actual_image_files}")

    return {
        "ok": not errors,
        "output_dir": str(root),
        "date": date,
        "status": status,
        "concept_name": concept.get("name"),
        "image_count": len(image_entries),
        "dimensions": list(dimensions[0]) if dimensions and len(set(dimensions)) == 1 else None,
        "unique_hashes": len(set(hashes)),
        "roles": sorted(roles),
        "direct_feedback_count": len(direct) if isinstance(direct, list) else 0,
        "market_proof_count": len(market) if isinstance(market, list) else 0,
        "official_source_count": len(official) if isinstance(official, list) else 0,
        "visual_mapping_count": len(mappings) if isinstance(mappings, list) else 0,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    result = validate(args.output_dir)
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        state = "PASS" if result["ok"] else "FAIL"
        print(f"{state}: {result['output_dir']}")
        for warning in result.get("warnings", []):
            print(f"warning: {warning}")
        for error in result.get("errors", []):
            print(f"error: {error}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
