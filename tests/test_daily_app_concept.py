from __future__ import annotations

import importlib.util
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECK_SCRIPT = ROOT / "skills/daily-app-concept/scripts/check_novelty.py"
VALIDATE_SCRIPT = ROOT / "skills/daily-app-concept/scripts/validate_output.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_novelty = load_module("check_novelty", CHECK_SCRIPT)
validate_output = load_module("validate_output", VALIDATE_SCRIPT)


def write_png(path: Path, rgb: tuple[int, int, int]) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    raw = b"\x00" + bytes(rgb)
    path.write_bytes(signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def candidate(name: str, action: str, decision: str = "rejected") -> dict[str, str]:
    return {
        "name": name,
        "target_user": "busy parents",
        "trigger": "before grocery shopping",
        "core_object": "shared pantry list",
        "core_action": action,
        "result": "know what to buy",
        "decision": decision,
        "reason": "fixture decision",
    }


def valid_manifest(status: str = "complete") -> dict:
    candidates = [
        candidate("Pantry Lens", "scan pantry", "selected"),
        candidate("Receipt Sort", "scan receipts"),
        candidate("Shelf Timer", "mark expiry dates"),
    ]
    return {
        "schema_version": 3,
        "date": "2026-09-17",
        "status": status,
        "concept": {
            "name": "Pantry Lens",
            "one_sentence": "Parents scan the pantry before shopping and immediately see missing staples.",
            "novelty_key": "parents|before shopping|pantry|scan|missing staples",
            "target_user": "busy parents",
            "trigger": "before grocery shopping",
            "core_action": "scan pantry",
            "result": "see missing staples",
            "core_screen": "pantry gap list",
            "monetization_hypothesis": "one-time purchase",
            "competition_risk": "grocery apps may add scanning",
            "flow": ["open", "scan", "review"],
            "mvp": ["scan", "gap list"],
            "exclusions": ["social feed", "delivery marketplace"],
        },
        "evidence": {
            "direct_user_feedback": [
                {
                    "url": "https://example.com/user-1", "accessed": "2026-09-17",
                    "published": "2026-09-01", "summary": "User forgets staples", "scope": "one comment",
                },
                {
                    "url": "https://example.com/user-2", "accessed": "2026-09-17",
                    "published": "2026-09-02", "summary": "User buys duplicates", "scope": "one comment",
                },
            ],
            "market_proof": [
                {
                    "url": "https://example.com/app", "accessed": "2026-09-17",
                    "summary": "Comparable app has reviews", "scope": "store listing",
                }
            ],
            "official_sources": [
                {"url": "https://example.com/official", "accessed": "2026-09-17", "summary": "Camera API limit"}
            ],
            "inferences": ["Users may pay for a local-first utility"],
        },
        "novelty_review": {
            "first_run": True,
            "first_run_reason": "Checked the workspace, adjacent histories, and current conversation; none exist.",
            "history_sources": [],
            "history_items_reviewed": 0,
            "conversation_prior_ideas_checked": True,
            "rejected_concepts_reserved": True,
            "candidate_count": 3,
            "candidates": candidates,
            "nearest_matches": [],
            "automated_check": {"comparison_count": 0, "max_similarity": 0, "decision": "first_run"},
            "selected_reason": "Best evidence and narrowest loop",
            "decision": "pass",
        },
        "visual": {
            "style_summary": "A shelf-gap visual system derived from the product state.",
            "mappings": [
                {"source_clue": "empty shelf", "design_primitive": "gap", "component": "missing item", "purpose": "state"},
                {"source_clue": "scan", "design_primitive": "beam", "component": "scanner", "purpose": "action"},
                {"source_clue": "staple", "design_primitive": "label", "component": "item chip", "purpose": "identity"},
            ],
            "third_party_assets_used": False,
            "third_party_assets": [],
            "references": [
                {
                    "url": f"https://example.com/design-{index}", "accessed": "2026-09-17",
                    "summary": "Reference method", "owner": f"Owner {index}",
                    "method_taken": "Hierarchy only", "license_judgment": "No assets reused",
                }
                for index in range(3)
            ],
            "quality_review": {
                "directions_explored": [
                    {
                        "name": name, "composition": f"Composition {name}",
                        "product_metaphor": f"Metaphor {name}", "why_not_template": f"Reason {name}",
                    }
                    for name in ("Shelf", "Scan", "Map")
                ],
                "selected_direction": "Shelf",
                "selection_mode": "automatic",
                "selection_evidence": "Shelf made the state change most legible.",
                "recent_sets_compared": 0,
                "first_run_reason": "No prior visual sets exist.",
                "template_fingerprint": {
                    "layout": "split shelf", "hero_structure": "product object", "palette": "warm neutral",
                    "type_treatment": "compact labels", "device_treatment": "cropped interface",
                },
                "contact_sheet_reviewed": True,
                "full_size_reviewed": True,
                "core_ui_reviewed": True,
                "scores": {
                    "product_specificity": 8, "information_hierarchy": 8,
                    "core_ui_believability": 8, "sequence_variety": 8,
                    "readability": 8, "craft": 8,
                },
                "blocking_issues": [],
                "decision": "pass",
            },
        },
        "images": [],
    }


def create_output(root: Path, status: str = "complete") -> Path:
    for name in ("research.md", "concept.md", "visual-system.md"):
        (root / name).write_text(f"# {name}\n", encoding="utf-8")
    images_dir = root / "images"
    images_dir.mkdir()
    roles = ["problem", "solution", "core-screen", "state-change", "outcome"]
    communicates = [["problem", "action"], ["result"], ["action"], ["result"], ["result"]]
    entries = []
    for index, role in enumerate(roles, start=1):
        filename = f"images/{index:02d}-{role}.png"
        write_png(root / filename, (index, index * 2, index * 3))
        entries.append({
            "file": filename,
            "role": role,
            "communicates": communicates[index - 1],
            "shows_product_ui": index <= 3,
            "width": 1,
            "height": 1,
        })
    manifest = valid_manifest(status)
    manifest["images"] = entries
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return root


class NoveltyTests(unittest.TestCase):
    def test_v3_history_reserves_selected_and_rejected_candidates(self) -> None:
        payload = {"concept": {"name": "Selected"}, "novelty_review": {"candidates": [candidate("A", "scan"), candidate("B", "sort")]}}
        self.assertEqual([item["name"] for item in check_novelty.history_records(payload)], ["A", "B"])

    def test_multiple_candidates_are_all_checked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            history = root / "index.json"
            history.write_text(json.dumps({"entries": [candidate("Prior", "scan pantry")]}), encoding="utf-8")
            candidate_path = root / "candidates.json"
            candidate_path.write_text(json.dumps({"candidates": [candidate("Duplicate", "scan pantry"), candidate("Different", "record bird songs")]}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(CHECK_SCRIPT), "--candidate", str(candidate_path), "--history", str(history), "--json"],
                check=False, capture_output=True, text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(payload["candidate_count"], 2)
            self.assertEqual(len(payload["results"]), 2)
            self.assertEqual(payload["results"][0]["decision"], "reject")

    def test_empty_history_requires_explicit_first_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate_path = Path(temp) / "candidate.json"
            candidate_path.write_text(json.dumps(candidate("First", "scan pantry")), encoding="utf-8")
            blocked = subprocess.run(
                [sys.executable, str(CHECK_SCRIPT), "--candidate", str(candidate_path), "--json"],
                check=False, capture_output=True, text=True,
            )
            allowed = subprocess.run(
                [sys.executable, str(CHECK_SCRIPT), "--candidate", str(candidate_path), "--allow-empty-history", "--json"],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(blocked.returncode, 2)
            self.assertEqual(allowed.returncode, 0)
            self.assertEqual(json.loads(allowed.stdout)["decision"], "first_run")


class OutputValidationTests(unittest.TestCase):
    def test_complete_v3_package_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = validate_output.validate(create_output(Path(temp)))
            self.assertTrue(result["ok"], result["errors"])

    def test_draft_requires_explicit_structural_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = create_output(Path(temp), status="draft")
            final_result = validate_output.validate(root)
            draft_result = validate_output.validate(root, allow_draft=True)
            self.assertFalse(final_result["ok"])
            self.assertTrue(draft_result["ok"], draft_result["errors"])

    def test_malformed_boolean_reports_an_error_instead_of_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = create_output(Path(temp))
            manifest_path = root / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["visual"]["third_party_assets_used"] = []
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            result = validate_output.validate(root)
            self.assertFalse(result["ok"])
            self.assertIn("visual.third_party_assets_used must be true or false", result["errors"])


if __name__ == "__main__":
    unittest.main()
