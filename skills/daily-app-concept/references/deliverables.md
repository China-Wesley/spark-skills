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

可以增加第 6、7 张，但不要为了数量填充无意义页面。研究过程、生成提示词和废案可放在日期目录之外的工作目录。

## 文件内容

### research.md

包含至少 3 个候选、来源日期、访问日期、可见热度、直接反馈、市场证明、技术来源、行为成本、六项评分、淘汰原因和最终证据边界。

### concept.md

包含目标用户、触发、核心动作、立即结果、核心一屏、3–5 个流程、竞品边界、MVP、明确不做、技术可行性、收费假设与主要风险。

### visual-system.md

包含设计案例来源与许可判断、3–5 条视觉映射、色彩、排版、核心组件、状态变化和图组叙事。

### manifest.json

`manifest.json` 是校验所用的机器可读摘要。参考结构：

```json
{
  "schema_version": 1,
  "date": "YYYY-MM-DD",
  "status": "draft",
  "concept": {
    "name": "App name",
    "one_sentence": "谁在什么时刻，通过什么动作，得到什么结果",
    "target_user": "",
    "trigger": "",
    "core_action": "",
    "result": "",
    "core_screen": "",
    "flow": ["", "", ""],
    "mvp": ["", "", ""],
    "exclusions": ["", ""],
    "monetization_hypothesis": "",
    "competition_risk": ""
  },
  "evidence": {
    "direct_user_feedback": [
      {"url": "", "published": "", "accessed": "", "summary": "", "scope": ""},
      {"url": "", "published": "", "accessed": "", "summary": "", "scope": ""}
    ],
    "market_proof": [{"url": "", "accessed": "", "summary": "", "scope": ""}],
    "official_sources": [{"url": "", "accessed": "", "summary": ""}],
    "inferences": [""]
  },
  "visual": {
    "style_summary": "",
    "mappings": [
      {"source_clue": "", "design_primitive": "", "component": "", "purpose": ""}
    ],
    "third_party_assets_used": false,
    "third_party_assets": []
  },
  "images": [
    {"file": "images/01-problem.png", "role": "problem", "width": 1080, "height": 1440}
  ]
}
```

如果使用第三方素材，`third_party_assets_used` 必须为 `true`，并为每项记录 `source_url`、`license` 和 `usage`。没有明确许可时不得使用。

## 完成标准

- 5–7 张独立 PNG，统一尺寸，文件可读且哈希互不重复。
- 图组包含 `problem`、`solution`、`core-screen`、`state-change` 和 `outcome`。
- 至少两条普通用户反馈、一条市场证明和一条官方来源。
- 至少三条产品到视觉的映射。
- `status=complete` 只表示本次概念产物完成，不代表 App 已上线或需求已验证。

运行 `scripts/validate_output.py <输出目录> --json`。先以 `draft` 状态校验；修复所有错误后改为 `complete` 并再次运行。
