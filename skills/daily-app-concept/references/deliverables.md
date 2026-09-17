# 交付与校验

## 输出目录

```text
YYYY-MM-DD/
├── research.md
├── concept.md
├── visual-system.md
├── manifest.json
└── images/
    ├── 01-problem.png
    ├── 02-solution.png
    ├── 03-core-screen.png
    ├── 04-state-change.png
    └── 05-outcome.png
```

可增加第 6、7 张。生成提示词、三方向草图、联系表和废案可放在日期目录的 `working/`，但正式图片必须逐张独立输出。

## 文档内容

- `research.md`：三个候选、证据、查重、评分、行为成本、淘汰原因和证据边界。
- `concept.md`：目标用户、触发、动作、结果、流程、竞品、MVP、不做、技术、收费和风险。
- `visual-system.md`：参考来源、三方向比较、选择理由、视觉映射、模板指纹、组件、状态和目视复核。
- `manifest.json`：供校验与历史索引读取的机器摘要。

## manifest v2 新增硬门槛

旧有的 `concept`、`evidence`、`visual.mappings` 和 `images` 字段继续保留，并新增：

```json
{
  "schema_version": 2,
  "status": "draft",
  "concept": {
    "novelty_key": "目标用户|触发|核心对象|核心动作|立即结果"
  },
  "novelty_review": {
    "history_sources": ["path/to/index.json"],
    "history_items_reviewed": 12,
    "conversation_prior_ideas_checked": true,
    "rejected_concepts_reserved": true,
    "candidate_count": 3,
    "nearest_matches": [
      {"name": "Prior concept", "overlap": "同属摄影但触发与动作不同", "decision": "different"}
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
  },
  "images": [
    {
      "file": "images/01-problem.png",
      "role": "problem",
      "communicates": ["problem"],
      "shows_product_ui": true,
      "width": 1080,
      "height": 1440
    }
  ]
}
```

`directions_explored` 实际至少三项，`references` 至少三项。前两张图片的 `communicates` 合集必须包含 `problem`、`action`、`result`；至少三张 `shows_product_ui=true`。

## 校验

```bash
python3 scripts/check_novelty.py --candidate manifest.json --history <history-root> --json
python3 scripts/validate_output.py <输出目录> --json
```

完成标准：5–7 张 PNG、统一尺寸、哈希互不重复、五类叙事角色齐全、证据达到门槛、至少三条视觉映射、三套方向比较、六项视觉评分均不低于 8。脚本通过后再将 `status` 改为 `complete` 并复跑。
