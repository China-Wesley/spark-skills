# 交付、状态与校验

## 输出目录

```text
YYYY-MM-DD/
├── research.md
├── concept.md
├── visual-system.md
├── manifest.json
├── images/
│   ├── 01-problem.png
│   ├── 02-solution.png
│   ├── 03-core-screen.png
│   ├── 04-state-change.png
│   └── 05-outcome.png
└── working/
    └── candidates.json
```

可增加第 6、7 张。生成提示词、三方向草图、联系表和废案可放在 `working/`，但正式图片必须逐张独立输出。

## 文档职责

- `research.md`：三个候选、证据、查重、评分、行为成本、淘汰原因和证据边界。
- `concept.md`：目标用户、触发、动作、结果、流程、竞品、MVP、不做、技术、收费和风险。
- `visual-system.md`：参考来源、三方向比较、选择证据、视觉映射、模板指纹和目视复核。
- `manifest.json`：状态机、Gate 结果、历史排除集和文件清单的机器摘要。
- `working/candidates.json`：正式选择前供查重脚本逐项比较的候选数组。

## candidates.json

```json
{
  "candidates": [
    {
      "name": "Candidate A",
      "target_user": "目标用户",
      "trigger": "触发时刻",
      "core_object": "核心对象",
      "core_action": "核心动作",
      "result": "立即结果"
    }
  ]
}
```

数组至少三项。脚本会逐项返回 `pass`、`warn`、`reject` 或首次运行时的 `first_run`，不能只检查第一项后替其他候选推断结果。

## manifest schema v3

新产物使用 `schema_version: 3`。v2 只作为历史兼容输入；校验时会提示升级。除原有 `concept`、`evidence`、`visual.mappings` 和 `images` 字段外，v3 必须物化以下 Gate：

```json
{
  "schema_version": 3,
  "date": "YYYY-MM-DD",
  "status": "draft",
  "concept": {
    "name": "Selected concept",
    "novelty_key": "目标用户|触发|核心对象|核心动作|立即结果"
  },
  "novelty_review": {
    "first_run": false,
    "history_sources": ["path/to/index.json"],
    "history_items_reviewed": 12,
    "conversation_prior_ideas_checked": true,
    "rejected_concepts_reserved": true,
    "candidate_count": 3,
    "candidates": [
      {
        "name": "Selected concept",
        "target_user": "目标用户",
        "trigger": "触发时刻",
        "core_object": "核心对象",
        "core_action": "核心动作",
        "result": "立即结果",
        "decision": "selected",
        "reason": "证据、差异和一人可行性最佳"
      },
      {
        "name": "Rejected concept",
        "target_user": "目标用户",
        "trigger": "触发时刻",
        "core_object": "核心对象",
        "core_action": "核心动作",
        "result": "立即结果",
        "decision": "rejected",
        "reason": "与历史核心动作重复"
      }
    ],
    "nearest_matches": [
      {"name": "Prior concept", "overlap": "相似与差异", "decision": "different"}
    ],
    "automated_check": {
      "comparison_count": 12,
      "max_similarity": 0.21,
      "decision": "pass"
    },
    "selected_reason": "五元组与历史均有实质差异",
    "decision": "pass"
  },
  "visual": {
    "references": [
      {
        "url": "https://example.com",
        "accessed": "YYYY-MM-DD",
        "summary": "参考信息层级",
        "owner": "Author or product",
        "method_taken": "只采用层级方法",
        "license_judgment": "不复用其图片或独特构图"
      }
    ],
    "quality_review": {
      "directions_explored": [
        {
          "name": "Direction A",
          "composition": "主构图",
          "product_metaphor": "产品隐喻",
          "why_not_template": "与通用模板的结构差异"
        }
      ],
      "selected_direction": "Direction A",
      "selection_mode": "user",
      "selection_evidence": "用户选择原话，或自动选择使用的判据与理由",
      "recent_sets_compared": 7,
      "template_fingerprint": {
        "layout": "",
        "hero_structure": "",
        "palette": "",
        "type_treatment": "",
        "device_treatment": ""
      },
      "contact_sheet_reviewed": true,
      "full_size_reviewed": true,
      "core_ui_reviewed": true,
      "scores": {
        "product_specificity": 8,
        "information_hierarchy": 8,
        "core_ui_believability": 8,
        "sequence_variety": 8,
        "readability": 8,
        "craft": 8
      },
      "blocking_issues": [],
      "decision": "pass"
    }
  }
}
```

`candidates` 实际至少三项且只能有一项 `selected`，其名称必须等于 `concept.name`。被淘汰候选仍保留，供未来历史查重。

真正首次运行时使用：

```json
{
  "first_run": true,
  "first_run_reason": "已检查指定根目录、工作区、相邻历史目录和当前对话，未找到既有概念",
  "history_sources": [],
  "history_items_reviewed": 0,
  "automated_check": {
    "comparison_count": 0,
    "max_similarity": 0,
    "decision": "first_run"
  }
}
```

自动结果为 `warn` 时，`automated_check` 还必须写入 `warning_resolution`，说明五元组人工比较后为何仍可保留。`reject` 不能通过最终 Gate。

`directions_explored` 实际至少三项，`references` 至少三项。`selection_mode` 为 `user` 或 `automatic`；两者都必须留下 `selection_evidence`。前两张图片的 `communicates` 合集必须包含 `problem`、`action`、`result`；至少三张 `shows_product_ui=true`。

## 校验

从 Skill 根目录运行：

```bash
python3 scripts/check_novelty.py --candidate <candidate.json> --history <history-root> --json
python3 scripts/validate_output.py <output-dir> --allow-draft --json
python3 scripts/validate_output.py <output-dir> --json
```

若已确认是首次运行，查重命令用 `--allow-empty-history` 取代 `--history`。

完成标准：5–7 张 PNG、统一尺寸、哈希互不重复、五类叙事角色齐全、证据达到门槛、至少三条视觉映射、三套方向比较、选择证据存在、六项视觉评分均不低于 8。`--allow-draft` 只用于结构检查；最终命令要求 `status=complete`。
