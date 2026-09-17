#!/usr/bin/env python3
"""Validate the Spark Skills machine-readable catalog against the repository."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VALID_SKILL_STATUSES = {"available", "planned", "deprecated"}
VALID_STAGE_STATUSES = {"available", "planned"}


def read_frontmatter_name(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    for line in text[4:end].splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"\'')
    return None


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    catalog_path = root / "skills.json"

    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"ok": False, "errors": ["missing skills.json"]}
    except json.JSONDecodeError as exc:
        return {"ok": False, "errors": [f"skills.json is invalid JSON: {exc}"]}

    if catalog.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not DATE_RE.fullmatch(str(catalog.get("updated", ""))):
        errors.append("updated must use YYYY-MM-DD")
    for field in ("repository", "purpose"):
        if not non_empty_string(catalog.get(field)):
            errors.append(f"{field} must be a non-empty string")

    skill_format = catalog.get("format")
    if not isinstance(skill_format, dict):
        errors.append("format must be an object")
    else:
        if skill_format.get("name") != "Agent Skills":
            errors.append("format.name must be Agent Skills")
        specification = skill_format.get("specification")
        if not non_empty_string(specification) or not specification.startswith("https://"):
            errors.append("format.specification must be an HTTPS URL")
        if skill_format.get("portable_entrypoint") != "SKILL.md":
            errors.append("format.portable_entrypoint must be SKILL.md")

    stages = catalog.get("lifecycle_stages")
    stage_ids: set[str] = set()
    if not isinstance(stages, list) or not stages:
        errors.append("lifecycle_stages must be a non-empty list")
        stages = []
    for index, stage in enumerate(stages):
        label = f"lifecycle_stages[{index}]"
        if not isinstance(stage, dict):
            errors.append(f"{label} must be an object")
            continue
        stage_id = stage.get("id")
        if not non_empty_string(stage_id) or not NAME_RE.fullmatch(stage_id):
            errors.append(f"{label}.id must use lowercase kebab-case")
        elif stage_id in stage_ids:
            errors.append(f"duplicate lifecycle stage: {stage_id}")
        else:
            stage_ids.add(stage_id)
        for field in ("name", "name_zh"):
            if not non_empty_string(stage.get(field)):
                errors.append(f"{label}.{field} must be a non-empty string")
        if stage.get("status") not in VALID_STAGE_STATUSES:
            errors.append(f"{label}.status must be available or planned")

    skills = catalog.get("skills")
    catalog_names: set[str] = set()
    if not isinstance(skills, list) or not skills:
        errors.append("skills must be a non-empty list")
        skills = []
    for index, skill in enumerate(skills):
        label = f"skills[{index}]"
        if not isinstance(skill, dict):
            errors.append(f"{label} must be an object")
            continue
        name = skill.get("name")
        if not non_empty_string(name) or not NAME_RE.fullmatch(name):
            errors.append(f"{label}.name must use lowercase kebab-case")
            continue
        if name in catalog_names:
            errors.append(f"duplicate skill name: {name}")
        catalog_names.add(name)

        if skill.get("status") not in VALID_SKILL_STATUSES:
            errors.append(f"{label}.status is invalid")
        for field in ("category", "compatibility", "summary", "summary_zh"):
            if not non_empty_string(skill.get(field)):
                errors.append(f"{label}.{field} must be a non-empty string")

        linked_stages = skill.get("lifecycle_stages")
        if not isinstance(linked_stages, list) or not linked_stages:
            errors.append(f"{label}.lifecycle_stages must be a non-empty list")
        else:
            unknown = sorted(set(linked_stages) - stage_ids)
            if unknown:
                errors.append(f"{label} references unknown lifecycle stages: {unknown}")

        path_value = skill.get("path")
        entrypoint_value = skill.get("entrypoint")
        if not non_empty_string(path_value) or not non_empty_string(entrypoint_value):
            errors.append(f"{label}.path and entrypoint must be non-empty strings")
            continue
        skill_dir = (root / path_value).resolve()
        entrypoint = (root / entrypoint_value).resolve()
        if root.resolve() not in skill_dir.parents:
            errors.append(f"{label}.path escapes the repository")
            continue
        if skill_dir != entrypoint.parent and skill_dir not in entrypoint.parents:
            errors.append(f"{label}.entrypoint must be inside the skill directory")
        if not skill_dir.is_dir():
            errors.append(f"missing skill directory: {path_value}")
        if not entrypoint.is_file():
            errors.append(f"missing skill entrypoint: {entrypoint_value}")
        elif read_frontmatter_name(entrypoint) != name:
            errors.append(f"frontmatter name does not match catalog: {entrypoint_value}")

        for field in ("keywords", "deliverables"):
            values = skill.get(field)
            if not isinstance(values, list) or not values or any(not non_empty_string(item) for item in values):
                errors.append(f"{label}.{field} must be a non-empty string list")

        evals_value = skill.get("evals")
        if not non_empty_string(evals_value):
            errors.append(f"{label}.evals must be a repository-relative JSON path")
        else:
            evals_path = (root / evals_value).resolve()
            if root.resolve() not in evals_path.parents or not evals_path.is_file():
                errors.append(f"{label}.evals is missing or escapes the repository")
            elif skill_dir not in evals_path.parents:
                errors.append(f"{label}.evals must be inside the skill directory")
            else:
                try:
                    evals = json.loads(evals_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as exc:
                    errors.append(f"{label}.evals is invalid JSON: {exc}")
                else:
                    if evals.get("schema_version") != 1:
                        errors.append(f"{label}.evals schema_version must be 1")
                    if evals.get("skill") != name:
                        errors.append(f"{label}.evals skill must match the catalog name")
                    cases = evals.get("cases")
                    case_ids: set[str] = set()
                    if not isinstance(cases, list) or len(cases) < 4:
                        errors.append(f"{label}.evals must contain at least 4 cases")
                    else:
                        for case_index, case in enumerate(cases):
                            case_label = f"{label}.evals.cases[{case_index}]"
                            if not isinstance(case, dict):
                                errors.append(f"{case_label} must be an object")
                                continue
                            for case_field in ("id", "category", "prompt"):
                                if not non_empty_string(case.get(case_field)):
                                    errors.append(f"{case_label}.{case_field} must be a non-empty string")
                            case_id = case.get("id")
                            if isinstance(case_id, str):
                                if case_id in case_ids:
                                    errors.append(f"duplicate eval case id: {case_id}")
                                case_ids.add(case_id)
                            for case_field in ("expected", "prohibited"):
                                values = case.get(case_field)
                                if not isinstance(values, list) or not values or any(
                                    not non_empty_string(item) for item in values
                                ):
                                    errors.append(f"{case_label}.{case_field} must be a non-empty string list")

        install = skill.get("install")
        if not isinstance(install, dict):
            errors.append(f"{label}.install must be an object")
        else:
            if install.get("type") != "subdirectory":
                errors.append(f"{label}.install.type must be subdirectory")
            if install.get("source") != path_value:
                errors.append(f"{label}.install.source must match path")

    discovered = {
        path.parent.name
        for path in (root / "skills").glob("*/SKILL.md")
        if path.is_file()
    }
    missing_from_catalog = sorted(discovered - catalog_names)
    missing_from_tree = sorted(catalog_names - discovered)
    if missing_from_catalog:
        errors.append(f"skills missing from catalog: {missing_from_catalog}")
    if missing_from_tree:
        errors.append(f"catalog skills missing from repository: {missing_from_tree}")

    return {
        "ok": not errors,
        "catalog": str(catalog_path),
        "stage_count": len(stage_ids),
        "skill_count": len(catalog_names),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    result = validate(args.root.resolve())
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{'PASS' if result['ok'] else 'FAIL'}: {result.get('catalog', 'skills.json')}")
        for error in result.get("errors", []):
            print(f"error: {error}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
