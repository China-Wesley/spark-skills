from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("catalog_validator", ROOT / "scripts/validate_catalog.py")
VALIDATOR = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(VALIDATOR)


class CatalogTests(unittest.TestCase):
    def validate_with_stages(self, stages, omit=False):
        catalog = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))
        for skill in catalog["skills"]:
            if skill["name"] == "book-life-advisor":
                if omit:
                    skill.pop("lifecycle_stages")
                else:
                    skill["lifecycle_stages"] = stages
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "skills.json").write_text(json.dumps(catalog), encoding="utf-8")
            for skill in catalog["skills"]:
                for field in ("entrypoint", "evals"):
                    path = root / skill[field]
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes((ROOT / skill[field]).read_bytes())
            return VALIDATOR.validate(root)

    def test_companion_skill_needs_no_app_stage(self):
        result = self.validate_with_stages([])
        self.assertTrue(result["ok"], result["errors"])

    def test_unknown_stage_is_still_rejected(self):
        result = self.validate_with_stages(["unknown-stage"])
        self.assertFalse(result["ok"])
        self.assertTrue(any("unknown lifecycle stages" in error for error in result["errors"]))

    def test_missing_or_invalid_stage_field_is_rejected(self):
        for value, omit in [(None, True), (None, False), ("design", False)]:
            with self.subTest(value=value, omit=omit):
                result = self.validate_with_stages(value, omit)
                self.assertFalse(result["ok"])
                self.assertTrue(any("lifecycle_stages must be a list" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
