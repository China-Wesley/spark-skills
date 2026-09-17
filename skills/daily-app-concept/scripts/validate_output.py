#!/usr/bin/env python3
"""Validate current and legacy daily-app-concept outputs using the Python stdlib."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any

DOCS = ("research.md", "concept.md", "visual-system.md", "manifest.json")
ROLES = {"problem", "solution", "core-screen", "state-change", "outcome"}
CONCEPT_FIELDS = (
    "name", "one_sentence", "novelty_key", "target_user", "trigger",
    "core_action", "result", "core_screen", "monetization_hypothesis",
    "competition_risk",
)
SCORE_FIELDS = (
    "product_specificity", "information_hierarchy", "core_ui_believability",
    "sequence_variety", "readability", "craft",
)
CANDIDATE_FIELDS = ("name", "target_user", "trigger", "core_object", "core_action", "result", "reason")


def text_fields(obj: dict[str, Any], fields: tuple[str, ...], label: str, errors: list[str]) -> None:
    for field in fields:
        if not isinstance(obj.get(field), str) or not obj[field].strip():
            errors.append(f"{label}.{field} must be a non-empty string")


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("invalid PNG signature or IHDR")
    return struct.unpack(">II", header[16:24])


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def source(item: Any, label: str, errors: list[str], scope: bool = False) -> None:
    if not isinstance(item, dict):
        errors.append(f"{label} must be an object")
        return
    fields = ("url", "accessed", "summary", "scope") if scope else ("url", "accessed", "summary")
    text_fields(item, fields, label, errors)
    if isinstance(item.get("url"), str) and not re.match(r"^https?://", item["url"]):
        errors.append(f"{label}.url must start with http:// or https://")


def list_of_text(obj: dict[str, Any], field: str, minimum: int, label: str, errors: list[str]) -> list[Any]:
    value = obj.get(field)
    if not isinstance(value, list) or len(value) < minimum or any(not isinstance(x, str) or not x.strip() for x in value):
        errors.append(f"{label}.{field} must contain at least {minimum} non-empty items")
        return []
    return value


def validate_novelty(manifest: dict[str, Any], errors: list[str], schema_version: int) -> dict[str, Any]:
    review = manifest.get("novelty_review")
    if not isinstance(review, dict):
        errors.append("novelty_review must be an object")
        return {}

    first_run = review.get("first_run", False)
    if schema_version >= 3 and not isinstance(first_run, bool):
        errors.append("novelty_review.first_run must be true or false")
        first_run = False
    history_sources = review.get("history_sources")
    if not isinstance(history_sources, list) or any(not isinstance(x, str) or not x.strip() for x in history_sources):
        errors.append("novelty_review.history_sources must be a string list")
    elif not first_run and not history_sources:
        errors.append("novelty_review.history_sources must contain at least 1 item outside a first run")
    count = review.get("history_items_reviewed")
    minimum_count = 0 if first_run else 1
    if not isinstance(count, int) or isinstance(count, bool) or count < minimum_count:
        errors.append(f"novelty_review.history_items_reviewed must be at least {minimum_count}")
        count = 0
    if first_run:
        if count != 0:
            errors.append("novelty_review.history_items_reviewed must be 0 on a first run")
        text_fields(review, ("first_run_reason",), "novelty_review", errors)
    if review.get("conversation_prior_ideas_checked") is not True:
        errors.append("novelty_review.conversation_prior_ideas_checked must be true")
    if review.get("rejected_concepts_reserved") is not True:
        errors.append("novelty_review.rejected_concepts_reserved must be true")
    candidate_count = review.get("candidate_count")
    if not isinstance(candidate_count, int) or isinstance(candidate_count, bool) or candidate_count < 3:
        errors.append("novelty_review.candidate_count must be at least 3")
    if schema_version >= 3:
        candidates = review.get("candidates")
        selected_names: list[str] = []
        if not isinstance(candidates, list) or len(candidates) < 3:
            errors.append("novelty_review.candidates must contain at least 3 reserved candidates")
        else:
            if isinstance(candidate_count, int) and candidate_count != len(candidates):
                errors.append("novelty_review.candidate_count must match the candidates list")
            candidate_names: set[str] = set()
            for index, item in enumerate(candidates):
                label = f"novelty_review.candidates[{index}]"
                if not isinstance(item, dict):
                    errors.append(f"{label} must be an object")
                    continue
                text_fields(item, CANDIDATE_FIELDS, label, errors)
                if isinstance(item.get("name"), str) and item["name"].strip():
                    if item["name"] in candidate_names:
                        errors.append(f"duplicate candidate name: {item['name']}")
                    candidate_names.add(item["name"])
                decision = item.get("decision")
                if decision not in ("selected", "rejected"):
                    errors.append(f"{label}.decision must be selected or rejected")
                elif decision == "selected" and isinstance(item.get("name"), str):
                    selected_names.append(item["name"])
            if len(selected_names) != 1:
                errors.append("novelty_review.candidates must contain exactly one selected candidate")
            concept_name = (manifest.get("concept") or {}).get("name") if isinstance(manifest.get("concept"), dict) else None
            if len(selected_names) == 1 and selected_names[0] != concept_name:
                errors.append("the selected candidate name must match concept.name")
    nearest = review.get("nearest_matches")
    minimum = 0 if first_run else min(3, count)
    if not isinstance(nearest, list) or len(nearest) < minimum:
        errors.append(f"novelty_review.nearest_matches must contain at least {minimum} comparisons")
    else:
        for index, item in enumerate(nearest):
            if not isinstance(item, dict):
                errors.append(f"novelty_review.nearest_matches[{index}] must be an object")
                continue
            text_fields(item, ("name", "overlap", "decision"), f"novelty_review.nearest_matches[{index}]", errors)
            if item.get("decision") not in ("different", "reject"):
                errors.append(f"novelty_review.nearest_matches[{index}].decision must be different or reject")
    automated = review.get("automated_check")
    if not isinstance(automated, dict):
        errors.append("novelty_review.automated_check must be an object")
    else:
        comparisons = automated.get("comparison_count")
        similarity = automated.get("max_similarity")
        minimum_comparisons = 0 if first_run else 1
        if not isinstance(comparisons, int) or isinstance(comparisons, bool) or comparisons < minimum_comparisons:
            errors.append(
                f"novelty_review.automated_check.comparison_count must be at least {minimum_comparisons}"
            )
        if not isinstance(similarity, (int, float)) or isinstance(similarity, bool) or not 0 <= similarity <= 1:
            errors.append("novelty_review.automated_check.max_similarity must be between 0 and 1")
        automated_decision = automated.get("decision")
        if first_run:
            if automated_decision != "first_run":
                errors.append("novelty_review.automated_check.decision must be first_run on a first run")
            if comparisons != 0 or similarity != 0:
                errors.append("a first-run automated check must report zero comparisons and zero similarity")
        elif automated_decision not in ("pass", "warn"):
            errors.append("novelty_review.automated_check.decision must be pass or warn")
        elif automated_decision == "warn":
            text_fields(automated, ("warning_resolution",), "novelty_review.automated_check", errors)
    text_fields(review, ("selected_reason",), "novelty_review", errors)
    if review.get("decision") != "pass":
        errors.append("novelty_review.decision must be pass")
    return review


def validate_visual(visual: dict[str, Any], errors: list[str], schema_version: int) -> dict[str, Any]:
    refs = visual.get("references")
    if not isinstance(refs, list) or len(refs) < 3:
        errors.append("visual.references must contain at least 3 design references")
    else:
        for index, item in enumerate(refs):
            label = f"visual.references[{index}]"
            source(item, label, errors)
            if isinstance(item, dict):
                text_fields(item, ("owner", "method_taken", "license_judgment"), label, errors)
    review = visual.get("quality_review")
    if not isinstance(review, dict):
        errors.append("visual.quality_review must be an object")
        return {}
    directions = review.get("directions_explored")
    names: set[str] = set()
    if not isinstance(directions, list) or len(directions) < 3:
        errors.append("visual.quality_review.directions_explored must contain at least 3 directions")
    else:
        for index, item in enumerate(directions):
            if not isinstance(item, dict):
                errors.append(f"visual.quality_review.directions_explored[{index}] must be an object")
                continue
            text_fields(
                item, ("name", "composition", "product_metaphor", "why_not_template"),
                f"visual.quality_review.directions_explored[{index}]", errors,
            )
            if isinstance(item.get("name"), str):
                names.add(item["name"])
        if len(names) != len(directions):
            errors.append("visual.quality_review direction names must be unique")
    selected = review.get("selected_direction")
    if not isinstance(selected, str) or not selected.strip():
        errors.append("visual.quality_review.selected_direction must be a non-empty string")
    elif names and selected not in names:
        errors.append("visual.quality_review.selected_direction must match an explored direction")
    if schema_version >= 3:
        if review.get("selection_mode") not in ("user", "automatic"):
            errors.append("visual.quality_review.selection_mode must be user or automatic")
        text_fields(review, ("selection_evidence",), "visual.quality_review", errors)
    recent = review.get("recent_sets_compared")
    if not isinstance(recent, int) or isinstance(recent, bool) or recent < 0:
        errors.append("visual.quality_review.recent_sets_compared must be a non-negative integer")
    elif recent == 0 and (not isinstance(review.get("first_run_reason"), str) or not review["first_run_reason"].strip()):
        errors.append("visual.quality_review.first_run_reason is required when no recent sets exist")
    fingerprint = review.get("template_fingerprint")
    if not isinstance(fingerprint, dict):
        errors.append("visual.quality_review.template_fingerprint must be an object")
    else:
        text_fields(
            fingerprint, ("layout", "hero_structure", "palette", "type_treatment", "device_treatment"),
            "visual.quality_review.template_fingerprint", errors,
        )
    for field in ("contact_sheet_reviewed", "full_size_reviewed", "core_ui_reviewed"):
        if review.get(field) is not True:
            errors.append(f"visual.quality_review.{field} must be true")
    scores = review.get("scores")
    if not isinstance(scores, dict):
        errors.append("visual.quality_review.scores must be an object")
    else:
        for field in SCORE_FIELDS:
            score = scores.get(field)
            if not isinstance(score, (int, float)) or isinstance(score, bool) or not 8 <= score <= 10:
                errors.append(f"visual.quality_review.scores.{field} must be between 8 and 10")
    if review.get("blocking_issues") != []:
        errors.append("visual.quality_review.blocking_issues must be an empty list")
    if review.get("decision") != "pass":
        errors.append("visual.quality_review.decision must be pass")
    return review


def validate(output_dir: Path, allow_draft: bool = False) -> dict[str, Any]:
    root, errors, warnings = output_dir.resolve(), [], []
    if not root.is_dir():
        return {"ok": False, "output_dir": str(root), "errors": ["output directory does not exist"], "warnings": []}
    for name in DOCS:
        path = root / name
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing or empty required file: {name}")
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return {"ok": False, "output_dir": str(root), "errors": errors, "warnings": warnings}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "output_dir": str(root), "errors": errors + [f"manifest.json is unreadable: {exc}"], "warnings": warnings}

    schema_version = manifest.get("schema_version")
    if schema_version not in (2, 3):
        errors.append("schema_version must be 3, or 2 for a legacy output")
        schema_version = 0
    elif schema_version == 2:
        warnings.append("schema_version 2 is legacy; new outputs must use schema_version 3")
    date = manifest.get("date")
    if not isinstance(date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        errors.append("date must use YYYY-MM-DD")
    status = manifest.get("status")
    if status not in ("draft", "complete"):
        errors.append("status must be draft or complete")
    elif status == "draft":
        warnings.append("status is draft; change to complete only after final review")
        if not allow_draft:
            errors.append("status is draft; use --allow-draft for a structural check or mark complete after review")
    if isinstance(date, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", output_dir.name) and output_dir.name != date:
        errors.append("manifest date must match a YYYY-MM-DD output directory name")

    concept = manifest.get("concept") if isinstance(manifest.get("concept"), dict) else {}
    if not concept:
        errors.append("concept must be an object")
    text_fields(concept, CONCEPT_FIELDS, "concept", errors)
    flow = list_of_text(concept, "flow", 3, "concept", errors)
    if len(flow) > 5:
        errors.append("concept.flow must contain no more than 5 steps")
    list_of_text(concept, "mvp", 2, "concept", errors)
    list_of_text(concept, "exclusions", 2, "concept", errors)

    evidence = manifest.get("evidence") if isinstance(manifest.get("evidence"), dict) else {}
    direct = evidence.get("direct_user_feedback")
    if not isinstance(direct, list) or len(direct) < 2:
        errors.append("evidence.direct_user_feedback must contain at least 2 sources")
        direct = []
    for index, item in enumerate(direct):
        source(item, f"evidence.direct_user_feedback[{index}]", errors, True)
        if isinstance(item, dict):
            text_fields(item, ("published",), f"evidence.direct_user_feedback[{index}]", errors)
    market = evidence.get("market_proof")
    if not isinstance(market, list) or not market:
        errors.append("evidence.market_proof must contain at least 1 source")
        market = []
    for index, item in enumerate(market):
        source(item, f"evidence.market_proof[{index}]", errors, True)
    official = evidence.get("official_sources")
    if not isinstance(official, list) or not official:
        errors.append("evidence.official_sources must contain at least 1 source")
        official = []
    for index, item in enumerate(official):
        source(item, f"evidence.official_sources[{index}]", errors)
    list_of_text(evidence, "inferences", 1, "evidence", errors)

    novelty = validate_novelty(manifest, errors, schema_version)
    visual = manifest.get("visual") if isinstance(manifest.get("visual"), dict) else {}
    text_fields(visual, ("style_summary",), "visual", errors)
    mappings = visual.get("mappings")
    if not isinstance(mappings, list) or len(mappings) < 3:
        errors.append("visual.mappings must contain at least 3 mappings")
        mappings = []
    for index, item in enumerate(mappings):
        if isinstance(item, dict):
            text_fields(item, ("source_clue", "design_primitive", "component", "purpose"), f"visual.mappings[{index}]", errors)
        else:
            errors.append(f"visual.mappings[{index}] must be an object")
    assets_used = visual.get("third_party_assets_used")
    assets = visual.get("third_party_assets")
    if not isinstance(assets_used, bool):
        errors.append("visual.third_party_assets_used must be true or false")
    elif assets_used is True:
        if not isinstance(assets, list) or not assets:
            errors.append("third-party assets require source_url, license and usage records")
        else:
            for index, item in enumerate(assets):
                if isinstance(item, dict):
                    text_fields(item, ("source_url", "license", "usage"), f"visual.third_party_assets[{index}]", errors)
                else:
                    errors.append(f"visual.third_party_assets[{index}] must be an object")
    elif assets not in (None, []):
        warnings.append("third_party_assets_used is false but third_party_assets is not empty")
    visual_review = validate_visual(visual, errors, schema_version)

    entries = manifest.get("images")
    if not isinstance(entries, list) or not 5 <= len(entries) <= 7:
        errors.append("images must contain 5 to 7 entries")
        entries = []
    dimensions, hashes, roles, listed, story, ui_count = [], [], set(), [], set(), 0
    for index, item in enumerate(entries):
        if not isinstance(item, dict):
            errors.append(f"images[{index}] must be an object")
            continue
        filename, role = item.get("file"), item.get("role")
        if not isinstance(filename, str) or not filename.strip():
            errors.append(f"images[{index}].file must be a non-empty string")
            continue
        if isinstance(role, str) and role.strip():
            roles.add(role)
        else:
            errors.append(f"images[{index}].role must be a non-empty string")
        communicates = item.get("communicates")
        if not isinstance(communicates, list) or not communicates:
            errors.append(f"images[{index}].communicates must contain labels")
        elif index < 2:
            story.update(x for x in communicates if isinstance(x, str))
        if item.get("shows_product_ui") is True:
            ui_count += 1
        elif item.get("shows_product_ui") is not False:
            errors.append(f"images[{index}].shows_product_ui must be true or false")
        if filename in listed:
            errors.append(f"duplicate image path: {filename}")
        listed.append(filename)
        path = (root / filename).resolve()
        if root not in path.parents or path.suffix.lower() != ".png" or not path.is_file():
            errors.append(f"invalid or missing PNG: {filename}")
            continue
        try:
            actual = png_size(path)
            dimensions.append(actual)
            hashes.append(digest(path))
            if (item.get("width"), item.get("height")) != actual:
                errors.append(f"dimension mismatch for {filename}: declared={(item.get('width'), item.get('height'))}, actual={actual}")
        except (OSError, ValueError) as exc:
            errors.append(f"unreadable PNG {filename}: {exc}")
    missing = sorted(ROLES - roles)
    if missing:
        errors.append(f"missing required image roles: {missing}")
    if not {"problem", "action", "result"}.issubset(story):
        errors.append("first two images must communicate problem, action and result")
    if ui_count < 3:
        errors.append("at least 3 images must set shows_product_ui=true")
    if dimensions and len(set(dimensions)) != 1:
        errors.append(f"image dimensions are inconsistent: {sorted(set(dimensions))}")
    if len(hashes) != len(set(hashes)):
        errors.append("image hashes are not unique")
    actual = sorted(str(path.relative_to(root)) for path in (root / "images").glob("*.png")) if (root / "images").is_dir() else []
    if sorted(listed) != actual:
        errors.append(f"manifest image list does not match images directory: manifest={sorted(listed)} actual={actual}")

    scores = visual_review.get("scores") if isinstance(visual_review.get("scores"), dict) else {}
    return {
        "ok": not errors, "output_dir": str(root), "date": date, "status": status,
        "concept_name": concept.get("name"), "image_count": len(entries),
        "dimensions": list(dimensions[0]) if dimensions and len(set(dimensions)) == 1 else None,
        "unique_hashes": len(set(hashes)), "roles": sorted(roles), "ui_image_count": ui_count,
        "history_items_reviewed": novelty.get("history_items_reviewed"),
        "visual_score_min": min(scores.values()) if scores else None,
        "errors": errors, "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--allow-draft", action="store_true", help="Validate a draft package without treating draft status as an error.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    result = validate(args.output_dir, allow_draft=args.allow_draft)
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{'PASS' if result['ok'] else 'FAIL'}: {result['output_dir']}")
        for warning in result["warnings"]:
            print(f"warning: {warning}")
        for error in result["errors"]:
            print(f"error: {error}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
