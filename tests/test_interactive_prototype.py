from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "interactive-prototype"
INIT_SCRIPT = SKILL_ROOT / "scripts" / "init_prototype.py"
VALIDATOR_PATH = SKILL_ROOT / "scripts" / "validate_prototype.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("interactive_prototype_validator", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


class InteractivePrototypeTests(unittest.TestCase):
    def create_draft(self, root: Path, mode: str = "mobile") -> Path:
        output = root / "prototype"
        subprocess.run(
            [sys.executable, str(INIT_SCRIPT), "--output", str(output), "--title", "Flow Notes", "--mode", mode],
            check=True,
            capture_output=True,
            text=True,
        )
        return output

    def complete(self, output: Path) -> None:
        prototype = output / "prototype.html"
        prototype.write_text(
            prototype.read_text(encoding="utf-8").replace('data-scaffold="true"', 'data-scaffold="false"'),
            encoding="utf-8",
        )
        spec_path = output / "prototype-spec.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        spec["status"] = "complete"
        spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (output / "prototype-brief.md").write_text(
            "# Flow Notes · Prototype brief\n\n"
            "- Target user: solo makers validating one product journey\n"
            "- Trigger moment: a product idea is clear enough to prototype\n"
            "- Core object: the user's stated goal\n"
            "- Core action: create the goal\n"
            "- Immediate result: the saved goal appears\n",
            encoding="utf-8",
        )
        (output / "prototype-report.md").write_text(
            "# Flow Notes · Prototype report\n\n"
            "- Status: complete\n"
            "- Static validation: passed\n"
            "- Browser validation: pending in this unit fixture\n\n"
            "## Included states\n\nDefault, input, processing, and result.\n",
            encoding="utf-8",
        )

    def test_initializer_creates_reviewable_draft(self):
        with tempfile.TemporaryDirectory() as temp:
            output = self.create_draft(Path(temp))
            for filename in (
                "index.html",
                "prototype.html",
                "prototype-spec.json",
                "prototype-brief.md",
                "prototype-report.md",
            ):
                self.assertTrue((output / filename).is_file(), filename)
            result = VALIDATOR.validate(output, allow_draft=True)
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["status"], "draft")
            self.assertTrue(result["warnings"])

    def test_completed_scaffold_contract_passes_static_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            output = self.create_draft(Path(temp), mode="responsive")
            self.complete(output)
            result = VALIDATOR.validate(output, allow_draft=False)
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["mode"], "responsive")
            self.assertEqual(result["journey_step_count"], 3)

    def test_missing_journey_selector_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            output = self.create_draft(Path(temp))
            self.complete(output)
            spec_path = output / "prototype-spec.json"
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["primary_journey"]["steps"][0]["selector"] = '[data-test="missing"]'
            spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result = VALIDATOR.validate(output, allow_draft=False)
            self.assertFalse(result["ok"])
            self.assertTrue(any("does not match" in error for error in result["errors"]))

    def test_remote_script_fails_offline_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            output = self.create_draft(Path(temp))
            self.complete(output)
            prototype = output / "prototype.html"
            text = prototype.read_text(encoding="utf-8").replace(
                "</body>", '<script src="https://cdn.example.com/app.js"></script></body>'
            )
            prototype.write_text(text, encoding="utf-8")
            result = VALIDATOR.validate(output, allow_draft=False)
            self.assertFalse(result["ok"])
            self.assertTrue(any("remote scripts" in error for error in result["errors"]))

    def test_catalog_lists_interactive_prototype(self):
        catalog = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))
        names = {skill["name"] for skill in catalog["skills"]}
        self.assertIn("interactive-prototype", names)


if __name__ == "__main__":
    unittest.main()
