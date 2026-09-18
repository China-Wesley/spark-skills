#!/usr/bin/env python3
"""Validate the structure and static interaction contract of a prototype output."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "index.html",
    "prototype.html",
    "prototype-spec.json",
    "prototype-brief.md",
    "prototype-report.md",
)
VALID_MODES = {"mobile", "desktop", "responsive"}
VALID_ACTIONS = {"click", "fill", "select", "press", "wait"}
PLACEHOLDER_PATTERNS = (
    r"\bTODO\b",
    r"\bLorem ipsum\b",
    r"\[replace[^\]]*\]",
    r"replace with",
)


class PrototypeHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.attributes: list[dict[str, str]] = []
        self.remote_scripts: list[str] = []
        self.remote_styles: list[str] = []
        self.remote_media: list[str] = []
        self.button_depth = 0
        self.current_button_text: list[str] = []
        self.current_button_attrs: dict[str, str] = {}
        self.unlabelled_buttons: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        self.attributes.append(values)
        if values.get("id"):
            self.ids.append(values["id"])

        if tag == "script" and values.get("src", "").startswith(("http://", "https://", "//")):
            self.remote_scripts.append(values["src"])
        if tag == "link" and values.get("href", "").startswith(("http://", "https://", "//")):
            self.remote_styles.append(values["href"])
        if tag in {"img", "video", "audio", "source"} and values.get("src", "").startswith(("http://", "https://", "//")):
            self.remote_media.append(values["src"])

        if tag == "button":
            self.button_depth += 1
            self.current_button_text = []
            self.current_button_attrs = values

    def handle_data(self, data: str) -> None:
        if self.button_depth:
            self.current_button_text.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag != "button" or not self.button_depth:
            return
        label = " ".join(part for part in self.current_button_text if part).strip()
        if not label and not self.current_button_attrs.get("aria-label"):
            identifier = self.current_button_attrs.get("id") or self.current_button_attrs.get("data-test") or "<button>"
            self.unlabelled_buttons.append(identifier)
        self.button_depth -= 1
        self.current_button_text = []
        self.current_button_attrs = {}


def non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def selector_exists(selector: str, html_text: str, parser: PrototypeHTMLParser) -> bool:
    if selector.startswith("#") and re.fullmatch(r"#[A-Za-z][\w:.-]*", selector):
        return selector[1:] in parser.ids

    attribute_match = re.fullmatch(
        r"\[([\w:-]+)=(?:\"([^\"]+)\"|'([^']+)'|([^\]]+))\]",
        selector,
    )
    if attribute_match:
        key = attribute_match.group(1)
        value = next(group for group in attribute_match.groups()[1:] if group is not None).strip()
        return any(attrs.get(key) == value for attrs in parser.attributes)

    # Complex CSS selectors are verified by Playwright. Static validation still
    # requires their literal anchor to appear in the source.
    tokens = re.findall(r"#[\w:.-]+|\[([\w:-]+)", selector)
    if not tokens:
        return selector in html_text
    return selector in html_text


def validate(root: Path, allow_draft: bool) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if not root.is_dir():
        return {"ok": False, "root": str(root), "errors": ["prototype output directory does not exist"], "warnings": []}

    for name in REQUIRED_FILES:
        if not (root / name).is_file():
            errors.append(f"missing required file: {name}")

    if errors:
        return {"ok": False, "root": str(root), "errors": errors, "warnings": warnings}

    try:
        spec = json.loads((root / "prototype-spec.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"ok": False, "root": str(root), "errors": [f"invalid prototype-spec.json: {exc}"], "warnings": []}

    shell_text = (root / "index.html").read_text(encoding="utf-8")
    prototype_text = (root / "prototype.html").read_text(encoding="utf-8")
    brief_text = (root / "prototype-brief.md").read_text(encoding="utf-8")
    report_text = (root / "prototype-report.md").read_text(encoding="utf-8")

    parser = PrototypeHTMLParser()
    parser.feed(prototype_text)

    if spec.get("schema_version") != 1:
        errors.append("prototype-spec.json schema_version must be 1")
    status = spec.get("status")
    if status not in {"draft", "complete"}:
        errors.append("prototype-spec.json status must be draft or complete")
    elif status != "complete":
        (warnings if allow_draft else errors).append("prototype status is draft")

    if not non_empty(spec.get("title")):
        errors.append("prototype-spec.json title must be a non-empty string")
    if spec.get("mode") not in VALID_MODES:
        errors.append("prototype-spec.json mode must be mobile, desktop, or responsive")

    viewport = spec.get("primary_viewport")
    if not isinstance(viewport, dict) or not all(isinstance(viewport.get(key), int) and viewport[key] > 0 for key in ("width", "height")):
        errors.append("primary_viewport must contain positive integer width and height")

    screens = spec.get("screens")
    screen_ids: set[str] = set()
    if not isinstance(screens, list) or len(screens) < 3:
        errors.append("prototype-spec.json must define at least three task-relevant screens or states")
        screens = []
    for index, screen in enumerate(screens):
        label = f"screens[{index}]"
        if not isinstance(screen, dict):
            errors.append(f"{label} must be an object")
            continue
        for field in ("id", "name", "purpose"):
            if not non_empty(screen.get(field)):
                errors.append(f"{label}.{field} must be a non-empty string")
        screen_id = screen.get("id")
        if non_empty(screen_id):
            if screen_id in screen_ids:
                errors.append(f"duplicate screen id: {screen_id}")
            screen_ids.add(screen_id)
            if not selector_exists(f'[data-screen="{screen_id}"]', prototype_text, parser):
                errors.append(f"screen missing from prototype.html: {screen_id}")

    journey = spec.get("primary_journey")
    if not isinstance(journey, dict):
        errors.append("primary_journey must be an object")
        journey = {}
    for field in ("id", "name", "start_screen"):
        if not non_empty(journey.get(field)):
            errors.append(f"primary_journey.{field} must be a non-empty string")
    if non_empty(journey.get("start_screen")) and journey["start_screen"] not in screen_ids:
        errors.append("primary_journey.start_screen must reference a declared screen")

    steps = journey.get("steps")
    if not isinstance(steps, list) or len(steps) < 2:
        errors.append("primary_journey.steps must contain at least two interactions")
        steps = []
    for index, step in enumerate(steps):
        label = f"primary_journey.steps[{index}]"
        if not isinstance(step, dict):
            errors.append(f"{label} must be an object")
            continue
        action = step.get("action")
        if action not in VALID_ACTIONS:
            errors.append(f"{label}.action must be one of {sorted(VALID_ACTIONS)}")
            continue
        selector = step.get("selector")
        if action != "wait":
            if not non_empty(selector):
                errors.append(f"{label}.selector must be a non-empty string")
            elif not selector_exists(selector, prototype_text, parser):
                errors.append(f"{label}.selector does not match a static prototype anchor: {selector}")
        if action in {"fill", "select", "press", "wait"} and "value" not in step:
            errors.append(f"{label}.value is required for action {action}")

        expect = step.get("expect")
        if expect is not None and not isinstance(expect, dict):
            errors.append(f"{label}.expect must be an object")
            continue
        if isinstance(expect, dict):
            expected_screen = expect.get("screen")
            if expected_screen is not None and expected_screen not in screen_ids:
                errors.append(f"{label}.expect.screen must reference a declared screen")
            visible = expect.get("visible")
            if visible is not None and (not non_empty(visible) or not selector_exists(visible, prototype_text, parser)):
                errors.append(f"{label}.expect.visible does not match a static prototype anchor: {visible}")
            text_expectation = expect.get("text")
            if text_expectation is not None:
                if not isinstance(text_expectation, dict):
                    errors.append(f"{label}.expect.text must be an object")
                else:
                    text_selector = text_expectation.get("selector")
                    if not non_empty(text_selector) or not selector_exists(text_selector, prototype_text, parser):
                        errors.append(f"{label}.expect.text.selector does not match a static prototype anchor")
                    if not non_empty(text_expectation.get("includes")):
                        errors.append(f"{label}.expect.text.includes must be a non-empty string")

    duplicates = sorted(item for item, count in Counter(parser.ids).items() if count > 1)
    if duplicates:
        errors.append(f"prototype.html contains duplicate ids: {duplicates}")
    if parser.unlabelled_buttons:
        errors.append(f"prototype.html contains buttons without text or aria-label: {parser.unlabelled_buttons}")
    if parser.remote_scripts:
        errors.append(f"prototype.html uses remote scripts: {parser.remote_scripts}")
    if parser.remote_styles:
        errors.append(f"prototype.html uses remote stylesheets: {parser.remote_styles}")
    if parser.remote_media:
        warnings.append(f"prototype.html uses remote media that may fail offline: {parser.remote_media}")

    if 'name="viewport"' not in prototype_text and "name='viewport'" not in prototype_text:
        errors.append("prototype.html is missing a viewport meta tag")
    if "prefers-reduced-motion" not in prototype_text:
        errors.append("prototype.html must handle prefers-reduced-motion")
    if 'data-scaffold="true"' in prototype_text or "data-scaffold='true'" in prototype_text:
        (warnings if allow_draft else errors).append("prototype.html is still marked as scaffold")

    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, brief_text + "\n" + report_text, flags=re.IGNORECASE):
            (warnings if allow_draft else errors).append(f"brief or report contains unfinished placeholder matching: {pattern}")

    if "data-prototype-shell" not in shell_text:
        errors.append("index.html is missing the prototype shell marker")
    if "data-prototype-device" not in shell_text:
        errors.append("index.html is missing the device/browser preview marker")
    if 'src="prototype.html"' not in shell_text and "src='prototype.html'" not in shell_text:
        errors.append("index.html must embed prototype.html")
    if "reset-button" not in shell_text:
        errors.append("index.html is missing the reset control")
    if 'href="prototype.html"' not in shell_text and "href='prototype.html'" not in shell_text:
        errors.append("index.html is missing a direct-open link to prototype.html")

    return {
        "ok": not errors,
        "root": str(root),
        "status": status,
        "mode": spec.get("mode"),
        "screen_count": len(screen_ids),
        "journey_step_count": len(steps),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Prototype output directory")
    parser.add_argument("--allow-draft", action="store_true", help="Report draft markers as warnings")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    result = validate(args.root.expanduser().resolve(), args.allow_draft)
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{'PASS' if result['ok'] else 'FAIL'}: {result['root']}")
        for warning in result.get("warnings", []):
            print(f"warning: {warning}")
        for error in result.get("errors", []):
            print(f"error: {error}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
