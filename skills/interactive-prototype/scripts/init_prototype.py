#!/usr/bin/env python3
"""Initialize a browser-delivered interactive prototype workspace."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


VALID_MODES = {"mobile", "desktop", "responsive"}


def render_template(source: Path, replacements: dict[str, str]) -> str:
    content = source.read_text(encoding="utf-8")
    for token, value in replacements.items():
        content = content.replace(token, value)
    return content


def write_new(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Prototype output directory")
    parser.add_argument("--title", required=True, help="Product title")
    parser.add_argument("--mode", choices=sorted(VALID_MODES), default="mobile")
    parser.add_argument("--force", action="store_true", help="Overwrite files created by this scaffold")
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parents[1]
    assets = skill_root / "assets"
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)

    viewport = (1440, 900) if args.mode == "desktop" else (390, 844)
    replacements = {
        "__PROTOTYPE_TITLE__": html.escape(args.title, quote=True),
        "__PROTOTYPE_MODE__": args.mode,
        "__VIEWPORT_WIDTH__": str(viewport[0]),
        "__VIEWPORT_HEIGHT__": str(viewport[1]),
    }

    shell = render_template(assets / "preview-shell.html", replacements)
    prototype = render_template(assets / "starter-prototype.html", replacements)

    spec = {
        "schema_version": 1,
        "status": "draft",
        "title": args.title,
        "mode": args.mode,
        "primary_viewport": {"width": viewport[0], "height": viewport[1]},
        "screens": [
            {"id": "home", "name": "起点", "purpose": "说明核心价值并发起主任务"},
            {"id": "compose", "name": "输入", "purpose": "收集完成任务所需的最少信息"},
            {"id": "processing", "name": "处理中", "purpose": "解释耗时操作并防止重复提交"},
            {"id": "result", "name": "结果", "purpose": "显示任务已经完成和即时价值"},
        ],
        "primary_journey": {
            "id": "core-task",
            "name": "完成核心任务",
            "start_screen": "home",
            "steps": [
                {
                    "action": "click",
                    "selector": "[data-test=\"start\"]",
                    "expect": {"screen": "compose", "visible": "[data-screen=\"compose\"]"},
                },
                {
                    "action": "fill",
                    "selector": "[data-test=\"goal-input\"]",
                    "value": "验证主任务",
                },
                {
                    "action": "click",
                    "selector": "[data-test=\"submit\"]",
                    "expect": {
                        "screen": "result",
                        "text": {"selector": "[data-test=\"result-title\"]", "includes": "验证主任务"},
                    },
                },
            ],
        },
    }

    brief = f"""# {args.title} · Prototype brief

## Product contract

- Target user: replace with a specific user
- Trigger moment: replace with a concrete situation
- Current friction: replace with the existing obstacle
- Core object: replace with the product object the user manipulates
- Core action: replace with the one action this prototype validates
- Immediate result: replace with the visible outcome
- Out of scope: replace with explicit exclusions

## Evidence and assumptions

- User-provided facts:
- Existing product or repository facts:
- Assumptions made for this first prototype:

## Primary journey

`trigger -> start -> action -> feedback -> decision -> result`
"""

    report = f"""# {args.title} · Prototype report

- Status: draft
- Mode: {args.mode}
- Primary journey: not yet verified
- Static validation: not yet run
- Browser validation: not yet run

## Included states

- Replace with the actual default, input, loading, success, error, empty, or undo states.

## Validation evidence

- Record the static validator command and result.
- Record Playwright or manual browser steps and screenshot paths.
- Record console or page errors and how they were resolved.

## Known limits

- This is an interactive prototype. Simulated services are not production integrations.
"""

    write_new(output / "index.html", shell, args.force)
    write_new(output / "prototype.html", prototype, args.force)
    write_new(output / "prototype-spec.json", json.dumps(spec, ensure_ascii=False, indent=2) + "\n", args.force)
    write_new(output / "prototype-brief.md", brief, args.force)
    write_new(output / "prototype-report.md", report, args.force)
    (output / "assets").mkdir(exist_ok=True)

    print(json.dumps({
        "ok": True,
        "status": "draft",
        "output": str(output),
        "mode": args.mode,
        "files": ["index.html", "prototype.html", "prototype-spec.json", "prototype-brief.md", "prototype-report.md"],
        "next": "Replace the scaffold with product-specific UI and interactions, then run validate_prototype.py.",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
