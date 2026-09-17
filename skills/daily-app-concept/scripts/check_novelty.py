#!/usr/bin/env python3
"""Compare one or more candidate concepts with JSON histories."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

GROUPS = {
    "user": ("target_user", "user_need"),
    "trigger": ("trigger", "specific_trigger"),
    "action": ("core_action", "core_job", "core_task"),
    "result": ("result", "core_screen", "differentiator", "positioning"),
    "topic": ("one_sentence", "theme", "category", "core_object", "topic_key", "semantic_keywords", "subject"),
}
WEIGHTS = {"user": .12, "trigger": .22, "action": .32, "result": .22, "topic": .12}


def as_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(as_text(item) for item in value)
    return ""


def concept(item: dict[str, Any]) -> dict[str, Any]:
    base = dict(item.get("concept") or item.get("app_idea") or item)
    for key in (
        "concept_name", "one_sentence", "user_need", "theme", "category",
        "core_object", "core_action", "topic_key", "semantic_keywords", "subject",
    ):
        if key in item and key not in base:
            base[key] = item[key]
    if "name" not in base and isinstance(item.get("concept_name"), str):
        base["name"] = item["concept_name"]
    return base


def records(payload: Any) -> list[dict[str, Any]]:
    """Read legacy manifests, ledgers, lists, or a single concept."""
    if isinstance(payload, list):
        return [concept(item) for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    if isinstance(payload.get("entries"), list):
        return [concept(item) for item in payload["entries"] if isinstance(item, dict)]
    if any(key in payload for key in ("concept", "app_idea", "concept_name", "one_sentence", "core_action")):
        return [concept(payload)]
    found: list[dict[str, Any]] = []
    for value in payload.values():
        if isinstance(value, (dict, list)):
            found.extend(records(value))
    return found


def candidate_records(payload: Any) -> list[dict[str, Any]]:
    """A research candidate file may use {"candidates": [...]} to check all options."""
    if isinstance(payload, dict) and isinstance(payload.get("candidates"), list):
        return [concept(item) for item in payload["candidates"] if isinstance(item, dict)]
    return records(payload)


def history_records(payload: Any) -> list[dict[str, Any]]:
    """Schema v3 manifests reserve selected and rejected candidates alike."""
    if isinstance(payload, dict):
        review = payload.get("novelty_review")
        if isinstance(review, dict) and isinstance(review.get("candidates"), list):
            values = [concept(item) for item in review["candidates"] if isinstance(item, dict)]
            if values:
                return values
    return records(payload)


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower()
    return re.sub(r"[^0-9a-z\u3400-\u9fff]+", "", value)


def grams(value: str) -> set[str]:
    value = normalize(value)
    if not value:
        return set()
    result = {value}
    result.update(value[i:i + 2] for i in range(max(0, len(value) - 1)))
    result.update(value[i:i + 3] for i in range(max(0, len(value) - 2)))
    return result


def jaccard(left: str, right: str) -> float:
    a, b = grams(left), grams(right)
    return len(a & b) / len(a | b) if a and b else 0.0


def group_text(item: dict[str, Any], keys: tuple[str, ...]) -> str:
    return " ".join(as_text(item.get(key)) for key in keys if item.get(key))


def compare(candidate: dict[str, Any], prior: dict[str, Any]) -> tuple[float, dict[str, float]]:
    parts = {name: jaccard(group_text(candidate, keys), group_text(prior, keys)) for name, keys in GROUPS.items()}
    score = sum(parts[name] * WEIGHTS[name] for name in WEIGHTS)
    if parts["trigger"] >= .5 and parts["action"] >= .5:
        score = max(score, (parts["trigger"] + parts["action"] + parts["result"]) / 3)
    return score, parts


def json_files(path: Path) -> list[Path]:
    if path.is_file() and path.suffix.lower() == ".json":
        return [path]
    if path.is_dir():
        return sorted({*path.rglob("manifest.json"), *path.rglob("选题台账.json"), *path.rglob("index.json")})
    return []


def evaluate(
    candidate: dict[str, Any],
    prior_records: list[tuple[dict[str, Any], str]],
    reject_threshold: float,
    warn_threshold: float,
    index: int,
) -> dict[str, Any]:
    name = as_text(candidate.get("name") or candidate.get("concept_name") or candidate.get("theme")) or f"candidate-{index}"
    if not prior_records:
        return {
            "name": name,
            "decision": "first_run",
            "max_similarity": 0.0,
            "nearest_matches": [],
        }

    matches = []
    for prior, path in prior_records:
        score, parts = compare(candidate, prior)
        prior_name = as_text(prior.get("name") or prior.get("concept_name") or prior.get("theme")) or "unnamed concept"
        matches.append({
            "name": prior_name,
            "source": path,
            "similarity": round(score, 4),
            "parts": {key: round(value, 4) for key, value in parts.items()},
        })
    matches.sort(key=lambda item: item["similarity"], reverse=True)
    maximum = matches[0]["similarity"]
    decision = "reject" if maximum >= reject_threshold else "warn" if maximum >= warn_threshold else "pass"
    return {
        "name": name,
        "decision": decision,
        "max_similarity": maximum,
        "nearest_matches": matches[:5],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--history", type=Path, action="append", default=[])
    parser.add_argument(
        "--allow-empty-history",
        action="store_true",
        help="Explicitly mark a verified first run after all known history locations were checked.",
    )
    parser.add_argument("--reject-threshold", type=float, default=.56)
    parser.add_argument("--warn-threshold", type=float, default=.40)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    try:
        if not 0 <= args.warn_threshold < args.reject_threshold <= 1:
            raise ValueError("thresholds must satisfy 0 <= warn < reject <= 1")
        payload = json.loads(args.candidate.read_text(encoding="utf-8"))
        candidates = candidate_records(payload)
        if not candidates:
            raise ValueError("candidate JSON contains no recognizable concept")

        prior_records: list[tuple[dict[str, Any], str]] = []
        seen: set[Path] = set()
        candidate_path = args.candidate.resolve()
        for root in args.history:
            for path in json_files(root.resolve()):
                resolved = path.resolve()
                if resolved in seen or resolved == candidate_path:
                    continue
                seen.add(resolved)
                history_payload = json.loads(path.read_text(encoding="utf-8"))
                prior_records.extend((item, str(path)) for item in history_records(history_payload))
        if not prior_records and not args.allow_empty_history:
            raise ValueError(
                "no history records found; search known history locations, then use --allow-empty-history only for a verified first run"
            )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    results = [
        evaluate(candidate, prior_records, args.reject_threshold, args.warn_threshold, index)
        for index, candidate in enumerate(candidates, start=1)
    ]
    decisions = {item["decision"] for item in results}
    if "reject" in decisions:
        decision = "reject"
    elif "warn" in decisions:
        decision = "warn"
    elif decisions == {"first_run"}:
        decision = "first_run"
    else:
        decision = "pass"

    output: dict[str, Any] = {
        "ok": "reject" not in decisions,
        "decision": decision,
        "candidate_count": len(candidates),
        "comparison_count": len(prior_records),
        "reject_threshold": args.reject_threshold,
        "warn_threshold": args.warn_threshold,
        "results": results,
        "note": "Review target user, trigger, core action, result and object semantically; warn requires a written resolution.",
    }
    if len(results) == 1:
        output["max_similarity"] = results[0]["max_similarity"]
        output["nearest_matches"] = results[0]["nearest_matches"]

    if args.as_json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"{decision.upper()}: checked {len(candidates)} candidate(s) against {len(prior_records)} record(s)")
        for item in results:
            print(f"- {item['decision'].upper()} {item['name']}: max similarity={item['max_similarity']:.4f}")
    return 1 if "reject" in decisions else 0


if __name__ == "__main__":
    sys.exit(main())
