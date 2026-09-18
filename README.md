# Spark Skills

**Portable Agent Skills for building and shipping independent apps.**

[English](README.md) · [简体中文](README.zh-CN.md)

Spark Skills is a growing collection of portable Agent Skills designed to help people become independent app developers. It breaks the path from discovering a real need to shipping an App Store product into focused workflows that can be used one stage at a time.

Each skill covers a practical part of the product lifecycle with clear triggers, decision criteria, concrete deliverables, and deterministic validation where possible. The long-term goal is a connected skill set that can guide a solo developer from opportunity discovery, product definition, and interface design through implementation, testing, App Store submission, launch, and iteration.

The core packages follow the open [Agent Skills specification](https://agentskills.io/specification): each skill has a portable `SKILL.md` entrypoint and may include `references/`, `scripts/`, and `assets/`. Client-specific metadata is optional and never required to understand or execute the core workflow.

## 30-second start

Ask your Agent to read the repository and install the skill that matches your current stage:

```text
Read https://github.com/China-Wesley/spark-skills and its skills.json. Recommend the most relevant available skill for my current App-development stage, explain what it will deliver, and install its source folder in the skills directory supported by this Agent.
```

To start directly with demand discovery and product definition:

```text
Install the daily-app-concept skill from https://github.com/China-Wesley/spark-skills and use it to find and validate one mobile App opportunity.
```

If you already have a product direction and need a clickable prototype:

```text
Install the interactive-prototype skill from https://github.com/China-Wesley/spark-skills and turn my product idea into a high-fidelity prototype that I can open and verify in a desktop browser.
```

## What belongs here

- **Demand discovery** based on current user feedback, market signals, and existing alternatives.
- **Product validation and definition** for choosing a narrow user, problem, core action, and MVP.
- **UX, interface, and prototype workflows** that turn product behavior into a usable experience.
- **Implementation and testing workflows** for building a reliable App as a solo developer.
- **App Store release workflows** covering product pages, privacy, compliance, review, and launch readiness.
- **Post-launch workflows** for learning from usage, feedback, and business results.
- **Validation tools and focused references** that make every stage easier to review and repeat.

The goal is to turn independent development into a visible sequence of decisions and deliverables. Each skill should improve judgment at one stage and produce work that can be reviewed directly or handed to the next stage.

## The independent app path

```mermaid
flowchart LR
    A[Discover a need] --> B[Validate demand]
    B --> C[Define the MVP]
    C --> D[Design the experience]
    D --> E[Build the App]
    E --> F[Test and polish]
    F --> G[Submit to the App Store]
    G --> H[Launch and learn]
```

The repository will grow along this path. The lifecycle table below separates what can be used today from stages still being developed.

| Stage | Core question | Skill | Status |
| --- | --- | --- | --- |
| Discover | Is there a real, specific user problem? | [`daily-app-concept`](skills/daily-app-concept/) | Available |
| Validate | Is the opportunity supported by users, market evidence, and technical reality? | [`daily-app-concept`](skills/daily-app-concept/) | Available |
| Define | What is the smallest useful product one person can build? | [`daily-app-concept`](skills/daily-app-concept/) | Available |
| Design | How should the core behavior, states, and visual language work? | [`interactive-prototype`](skills/interactive-prototype/) | Available |
| Build | How should the App be implemented without losing the MVP boundary? | — | Planned |
| Test | Is the product reliable, accessible, private, and ready to release? | — | Planned |
| Ship | Are metadata, screenshots, compliance, TestFlight, and review materials ready? | — | Planned |
| Learn | What should change after real usage and feedback? | — | Planned |

## Available skills

| Skill | Purpose | Main deliverables | Status |
| --- | --- | --- | --- |
| [`daily-app-concept`](skills/daily-app-concept/) | Find a current mobile product need, narrow it into a solo-developer-friendly App concept, derive an original visual system from product behavior, and create a coherent concept image set. | Research notes, product definition, visual system, manifest, and 5–7 App concept images. | Available |
| [`interactive-prototype`](skills/interactive-prototype/) | Turn a defined product direction into a user journey, product states, and a high-fidelity mobile or desktop prototype that can be operated in a desktop browser. | Browser preview, interactive product, product brief, executable primary journey, validation report, and screenshots. | Available |

The machine-readable catalog is [`skills.json`](skills.json). It records lifecycle coverage, discovery keywords, installation paths, deliverables, and availability so an Agent can select a skill without parsing the full README.

### `daily-app-concept`

This is the first workflow in Spark Skills and covers the opening stages of independent development: finding a need, validating the opportunity, defining a focused product, and making its core experience visible. Every concept must answer four basic questions:

1. Is there credible evidence that the problem exists?
2. Can one person build and test a narrow solution?
3. Does the visual language explain the product's core behavior?
4. Are the final images readable, consistent, original, and complete?

The skill researches recent user feedback and comparable products, scores candidate directions, defines a focused MVP, studies relevant design methods, and maps product behavior into interface components and states. It then creates a set of actual concept images and validates the output package.

```mermaid
flowchart LR
    A[Recent user signals] --> B[Evidence gate]
    B --> C[Narrow App concept]
    C --> D[Behavior and state model]
    D --> E[Original visual system]
    E --> F[Concept image set]
    F --> G[File and consistency validation]
```

Read the full instructions in [`skills/daily-app-concept/SKILL.md`](skills/daily-app-concept/SKILL.md).

### `interactive-prototype`

This skill connects product definition to implementation. It turns the idea into one high-value user journey, derives screens and states from that journey, and produces a browser-delivered prototype. Mobile work appears inside a scalable phone window on desktop; desktop work appears inside a browser window, with a direct link to the raw prototype.

Static screens are not treated as an interactive prototype, and simulated login, payment, AI, or persistence are not described as production integrations. Complete delivery requires structural validation and evidence from a real browser walkthrough.

```mermaid
flowchart LR
    A[Product idea] --> B[Product contract]
    B --> C[Journey and states]
    C --> D[High-fidelity browser prototype]
    D --> E[Browser journey verification]
    E --> F[Implementation handoff]
```

Read the full instructions in [`skills/interactive-prototype/SKILL.md`](skills/interactive-prototype/SKILL.md).

## Working principles

Spark Skills follows a few recurring principles:

- **Evidence before commitment.** Separate direct user feedback, market proof, company or founder claims, and inference.
- **Narrow the product.** Define one target user, one trigger, one core action, and one immediate result before adding features.
- **Respect behavior cost.** Favor actions users already take, system-readable data, and fast feedback over workflows that demand constant manual maintenance.
- **Let behavior shape the visual system.** Colors, containers, type, motion, and components should communicate information, state, or action.
- **Learn from design work without copying it.** Extract general methods while preserving source links, authorship, and licensing boundaries.
- **Deliver artifacts.** Research lists and prompts support the work; reviewable files are the outcome.
- **Validate what can be validated.** Use deterministic scripts for structure, dimensions, duplicates, manifests, and other mechanical checks.

## Install

Clone the repository:

```bash
git clone https://github.com/China-Wesley/spark-skills.git
cd spark-skills
```

The Agent Skills format defines the package, while each Agent decides where it discovers installed skills. Set the destination to the user-level or project-level skills directory documented by your Agent. A symbolic link is convenient when you plan to update this repository regularly:

```bash
SPARK_AGENT_SKILLS_DIR="/absolute/path/to/your-agent/skills"
mkdir -p "$SPARK_AGENT_SKILLS_DIR"
ln -s "$(pwd)/skills/daily-app-concept" "$SPARK_AGENT_SKILLS_DIR/daily-app-concept"
ln -s "$(pwd)/skills/interactive-prototype" "$SPARK_AGENT_SKILLS_DIR/interactive-prototype"
```

If your Agent supports installation from a Git repository and subdirectory, use the `install.source` value in [`skills.json`](skills.json). The portable unit is the individual skill directory, not the whole repository.

Pulling future repository updates will then update the linked skill:

```bash
git pull --ff-only
```

## Use

Invocation syntax varies by Agent. Name the skill directly in your request, or let a compatible Agent select it from the frontmatter description:

```text
Use the daily-app-concept skill to research one current mobile need and produce a complete App concept with actual images.

Use the interactive-prototype skill to turn this product idea into a high-fidelity browser prototype and verify its primary journey.
```

Before using a skill, read its `SKILL.md`. Some skills may route to additional files in `references/`, use helpers in `scripts/`, or include reusable materials in `assets/`.

## Portability contract

- `SKILL.md` is the portable source of truth. Its required frontmatter stays within the open Agent Skills specification.
- Relative links inside a skill resolve from the skill directory, so the folder can be copied or linked independently.
- Core instructions describe capabilities instead of assuming a vendor-specific tool name or invocation syntax.
- Client-specific files are optional adapters. An Agent that does not recognize them can ignore them without losing the workflow.
- Environment requirements are described as portable capabilities such as network, filesystem, or image generation access, without binding the workflow to a product name.

## Agent discovery protocol

When an Agent is asked to find or install a Spark Skill:

1. Read [`skills.json`](skills.json) and match the request against `lifecycle_stages`, `keywords`, and `summary`.
2. Recommend only skills whose status is `available`. Explain the stage covered, expected deliverables, and important boundaries.
3. Read the selected `entrypoint` before starting work. Load files in `references/` only when the entrypoint routes to them.
4. Install the catalog's `install.source` directory under the Agent's skills directory using the skill `name`.
5. Verify that `SKILL.md` exists and its frontmatter name matches the catalog entry. Do not treat a copied folder as successfully installed until this check passes.

Repository maintainers should run the catalog validator after adding, moving, or renaming a skill:

```bash
python3 scripts/validate_catalog.py --json
```

## Repository structure

```text
spark-skills/
├── README.md
├── README.zh-CN.md
├── skills.json
├── LICENSE
├── scripts/
│   └── validate_catalog.py
└── skills/
    ├── daily-app-concept/
    │   ├── SKILL.md
    │   ├── agents/
    │   │   └── openai.yaml       # Optional OpenAI client metadata
    │   ├── evals/
    │   │   └── cases.json        # Trigger, boundary, failure, and evidence cases
    │   ├── references/
    │   │   ├── deliverables.md
    │   │   ├── evidence-and-selection.md
    │   │   └── visual-system.md
    │   └── scripts/
    │       ├── check_novelty.py
    │       └── validate_output.py
    └── interactive-prototype/
        ├── SKILL.md
        ├── THIRD_PARTY_NOTICES.md
        ├── agents/
        ├── assets/
        ├── evals/
        ├── references/
        └── scripts/
```

Each skill keeps its main instructions in `SKILL.md` and adds supporting resources only when they improve the workflow:

- `agents/` contains optional client-specific metadata. The core skill never depends on it.
- `evals/` contains realistic behavioral cases for routing, boundaries, recovery, and evidence; they are evaluation inputs, not proof by themselves.
- `references/` contains detailed guidance loaded only when relevant.
- `scripts/` contains repeatable or deterministic operations.
- `assets/` may contain templates or source materials intended for generated output.

## How new skills are designed

New skills are added when a workflow has been exercised enough to capture useful judgment and produce a reliable handoff to the next stage. Every addition should have:

- A precise name and description that make automatic discovery reliable.
- Frontmatter that stays compatible with the open Agent Skills specification.
- A clear lifecycle stage, trigger, scope boundary, input, output, and handoff.
- A concise `SKILL.md`, with conditional detail moved into `references/`.
- Scripts only where repeatability or deterministic validation adds real value.
- Concrete deliverables that can be inspected independently of the conversation.
- Machine-readable evaluation cases covering trigger, non-trigger, failure recovery, and prohibited behavior.
- A matching entry in `skills.json` and a passing catalog validation result.

Build, test, App Store submission, and post-launch learning remain planned areas. The lifecycle table above is the source of truth for current coverage.

## Contributing and feedback

Suggestions, real usage reports, and focused improvements are welcome through GitHub Issues. When proposing a new skill, describe the stage of independent development it supports, the decisions it should improve, and what a reviewable result looks like.

## Inspiration

The repository navigation and catalog design were informed by [`alchaincyf/huashu-skills`](https://github.com/alchaincyf/huashu-skills), especially its human-readable routing, machine-readable skill index, and explicit installation protocol. `interactive-prototype` separately adapts the HTML-prototype and browser-verification methods from the MIT-licensed [`alchaincyf/huashu-design`](https://github.com/alchaincyf/huashu-design). Its source boundary and retained license notice are documented in [`THIRD_PARTY_NOTICES.md`](skills/interactive-prototype/THIRD_PARTY_NOTICES.md).

## License

This repository is available under the [MIT License](LICENSE).
