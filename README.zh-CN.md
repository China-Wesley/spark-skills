# Spark Skills

**用可移植的 Agent Skills，帮助每个人完成从需求发现到 App 上架的独立开发。**

[English](README.md) · [简体中文](README.zh-CN.md)

Spark Skills 是一个帮助大家成为独立开发者的通用 Agent Skills 仓库。它把“发现真实需求，做出产品，再把 App 上架”这条复杂路径拆成可以逐步调用的工作流。

每个 Skill 负责产品生命周期中的一个具体阶段，写清何时触发、依据什么做判断、如何推进、需要交付哪些文件，以及哪些结果可以通过脚本校验。长期目标是形成一套相互衔接的 Skills，让一个人也能从机会发现、产品定义和界面设计，一直走到开发、测试、App Store 审核、发布和后续迭代。

核心 Skill 遵循开放的 [Agent Skills 规范](https://agentskills.io/specification)：每个 Skill 都以可移植的 `SKILL.md` 为入口，并可按需附带 `references/`、`scripts/` 和 `assets/`。客户端专属元数据只是可选适配层，不影响其他 Agent 理解和执行核心工作流。

## 30 秒开始

可以直接让当前 Agent 阅读仓库，并根据你目前所处的阶段选择和安装 Skill：

```text
阅读 https://github.com/China-Wesley/spark-skills 和其中的 skills.json，根据我当前所处的 App 开发阶段推荐最相关的可用 Skill，说明它会交付什么，然后把来源目录安装到当前 Agent 支持的 Skills 目录。
```

如果准备直接开始需求发现和产品定义：

```text
从 https://github.com/China-Wesley/spark-skills 安装 daily-app-concept Skill，并用它发现和验证一个移动 App 机会。
```

如果已经有产品想法，需要直接做成可点击原型：

```text
从 https://github.com/China-Wesley/spark-skills 安装 interactive-prototype Skill，把我的产品想法做成能在电脑浏览器中打开和验收的高保真交互原型。
```

## 这个仓库会收录什么

- **需求发现**：从近期用户反馈、市场信号和现有替代方案中识别值得解决的问题。
- **产品验证与定义**：确定窄目标用户、核心问题、关键动作和 MVP。
- **体验设计与原型**：把产品行为转化为清楚、可用的交互和界面。
- **开发与测试**：帮助个人开发者构建可靠的 App，并控制实现范围。
- **App Store 上架**：覆盖产品页、隐私、合规、审核和发布准备。
- **发布后迭代**：根据使用情况、反馈和商业结果持续判断下一步。
- **校验工具与参考资料**：让每个阶段都更容易检查、复用和交接。

这个仓库希望把独立开发变成一条看得见的决策和交付链路。每个 Skill 都应当改善其中一个阶段的判断，并产出可以直接检查或交给下一阶段继续使用的结果。

## 独立 App 开发路径

```mermaid
flowchart LR
    A[发现需求] --> B[验证机会]
    B --> C[定义 MVP]
    C --> D[设计体验]
    D --> E[开发 App]
    E --> F[测试与打磨]
    F --> G[提交 App Store]
    G --> H[发布与迭代]
```

仓库会沿着这条路径持续补全。下方生命周期表明确区分现在可以使用的能力和仍在建设的阶段。

| 阶段 | 核心问题 | Skill | 状态 |
| --- | --- | --- | --- |
| 发现需求 | 是否存在真实、具体的用户问题？ | [`daily-app-concept`](skills/daily-app-concept/) | 可用 |
| 验证机会 | 用户、市场证据和技术现实是否支持这个机会？ | [`daily-app-concept`](skills/daily-app-concept/) | 可用 |
| 定义产品 | 一个人能够实现的最小有用产品是什么？ | [`daily-app-concept`](skills/daily-app-concept/) | 可用 |
| 设计体验 | 核心行为、状态和视觉语言应该怎样工作？ | [`interactive-prototype`](skills/interactive-prototype/) | 可用 |
| 开发实现 | 怎样在不突破 MVP 边界的前提下实现 App？ | — | 规划中 |
| 测试打磨 | 产品是否可靠、可访问、保护隐私并达到发布标准？ | — | 规划中 |
| App Store 上架 | 元数据、截图、合规、TestFlight 和审核材料是否齐全？ | — | 规划中 |
| 发布后迭代 | 真实使用和反馈说明下一步应该改什么？ | — | 规划中 |

## 已有 Skills

| Skill | 用途 | 主要交付物 | 状态 |
| --- | --- | --- | --- |
| [`daily-app-concept`](skills/daily-app-concept/) | 从近期真实反馈中发现一个移动产品需求，将其收窄成适合个人开发者验证的 App 概念，再从产品行为推导原创视觉系统并制作完整示意图。 | 调研记录、产品定义、视觉系统、清单文件和 5–7 张 App 概念图。 | 可用 |
| [`interactive-prototype`](skills/interactive-prototype/) | 把已有方向的产品想法整理成用户任务、状态与交互动线，并做成电脑浏览器中可直接操作的移动端或桌面端高保真原型。 | 浏览器展示页、交互产品、产品契约、可执行主路径、验收报告与截图。 | 可用 |

机器可读目录位于 [`skills.json`](skills.json)，其中记录了生命周期阶段、检索关键词、安装路径、交付物和可用状态，让 Agent 无需解析整篇 README 就能准确选择 Skill。

### `daily-app-concept`

这是 Spark Skills 的第一个工作流，覆盖独立开发的起点：发现需求、验证机会、定义聚焦的产品，并把核心体验清楚地呈现出来。每个概念都必须回答四个基本问题：

1. 是否有可信证据说明这个问题真实存在？
2. 能否收窄成一个人可以开发和验证的方案？
3. 视觉语言能否解释产品最核心的行为？
4. 最终图片是否清楚、一致、原创并且完整？

这个 Skill 会调研近期用户反馈和可比产品，给候选方向评分，定义聚焦的 MVP，研究相关设计方法，再把产品行为映射为界面组件和状态。最后生成一套实际的概念图片，并校验输出目录。

```mermaid
flowchart LR
    A[近期用户信号] --> B[证据门槛]
    B --> C[收窄 App 概念]
    C --> D[行为与状态模型]
    D --> E[原创视觉系统]
    E --> F[概念图片组]
    F --> G[文件与一致性校验]
```

完整说明见 [`skills/daily-app-concept/SKILL.md`](skills/daily-app-concept/SKILL.md)。

### `interactive-prototype`

这个 Skill 衔接产品定义与开发实现。它先把想法整理成一条最需要验证的用户任务，再从任务推导页面、局部状态、反馈和恢复路径。交付物可直接在电脑浏览器中打开：移动端显示在可缩放的手机窗口中，桌面端显示在浏览器窗口中，并保留原型单独打开入口。

它不会把几张静态图当作交互原型，也不会把模拟的登录、支付、AI 或数据保存描述成生产能力。完整结果需要静态结构校验和真实浏览器点击证据。

```mermaid
flowchart LR
    A[产品想法] --> B[产品契约]
    B --> C[主任务与状态]
    C --> D[高保真浏览器原型]
    D --> E[主路径点击验收]
    E --> F[交给开发实现]
```

完整说明见 [`skills/interactive-prototype/SKILL.md`](skills/interactive-prototype/SKILL.md)。

## 工作原则

Spark Skills 会长期坚持几条方法：

- **先看证据，再确定方向。** 分开记录普通用户反馈、市场证明、公司或开发者自述和仍属于推断的部分。
- **先收窄产品。** 增加功能以前，先定义一个目标用户、一个触发时刻、一个核心动作和一个立即可见的结果。
- **评估行为成本。** 优先承接用户已经发生的行为、系统可读取的数据和快速反馈，谨慎对待需要长期手工维护的流程。
- **从行为推导视觉。** 色彩、容器、字体、动效和组件都应承担信息、状态或操作作用。
- **研究设计方法，同时尊重原创。** 提炼通用方法，保留来源、作者和许可判断，不复制第三方独特表达。
- **交付实际成果。** 调研清单和提示词用于支持制作，可以直接检查的文件才是最终结果。
- **能自动检查的就自动检查。** 使用确定性脚本验证目录、尺寸、重复文件、清单和其他机械要求。

## 安装

克隆仓库：

```bash
git clone https://github.com/China-Wesley/spark-skills.git
cd spark-skills
```

Agent Skills 规范定义 Skill 包的结构，具体安装目录由各个 Agent 决定。请把目标路径设置为当前 Agent 文档规定的用户级或项目级 Skills 目录。如果准备长期更新这个仓库，使用软链接会更方便：

```bash
SPARK_AGENT_SKILLS_DIR="/当前Agent使用的Skills绝对路径"
mkdir -p "$SPARK_AGENT_SKILLS_DIR"
ln -s "$(pwd)/skills/daily-app-concept" "$SPARK_AGENT_SKILLS_DIR/daily-app-concept"
ln -s "$(pwd)/skills/interactive-prototype" "$SPARK_AGENT_SKILLS_DIR/interactive-prototype"
```

如果当前 Agent 支持从 Git 仓库和子目录直接安装，可以读取 [`skills.json`](skills.json) 中的 `install.source`。真正可移植的安装单元是单个 Skill 目录，而不是整个仓库。

以后拉取仓库更新，软链接安装的 Skill 也会同步更新：

```bash
git pull --ff-only
```

## 使用

不同 Agent 的显式调用语法可能不同。可以在请求中直接写出 Skill 名称，也可以由兼容的 Agent 根据 frontmatter 描述自动选择：

```text
使用 daily-app-concept Skill 调研一个近期移动端需求，并交付包含实际图片的完整 App 概念。

使用 interactive-prototype Skill 把这个产品想法做成在电脑浏览器中可操作并完成主路径验收的高保真原型。
```

使用前先阅读对应的 `SKILL.md`。部分 Skill 会按需读取 `references/` 中的详细规则，调用 `scripts/` 中的工具，或使用 `assets/` 中的模板与素材。

## 可移植性约定

- `SKILL.md` 是可移植的唯一事实源，必需 frontmatter 保持在开放 Agent Skills 规范范围内。
- Skill 内使用相对于自身目录的链接，使整个文件夹可以独立复制或软链接安装。
- 核心指令描述所需能力，不预设某个厂商的工具名称或调用语法。
- 客户端专属文件只是可选适配器；其他 Agent 即使忽略它们，也不会丢失核心工作流。
- 环境要求用联网、文件系统或图像生成等可移植能力描述，不把工作流绑定到某个产品名称。

## Agent 发现与安装协议

当 Agent 需要查找或安装 Spark Skill 时：

1. 读取 [`skills.json`](skills.json)，根据 `lifecycle_stages`、`keywords` 和 `summary` 匹配用户需求。
2. 只推荐状态为 `available` 的 Skill，并说明覆盖阶段、预期交付物和重要边界。
3. 开始工作前读取选中 Skill 的 `entrypoint`，只有入口文件明确路由时才加载 `references/`。
4. 按目录中的 `install.source`，把对应文件夹安装到 Agent 的 Skills 目录，并使用目录中的 `name` 作为安装名。
5. 验证 `SKILL.md` 确实存在，并确认其 frontmatter 名称与目录记录一致；只复制了文件夹不代表安装成功。

维护者新增、移动或改名 Skill 后应运行目录校验：

```bash
python3 scripts/validate_catalog.py --json
```

## 仓库结构

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
    │   │   └── openai.yaml       # 可选的 OpenAI 客户端元数据
    │   ├── evals/
    │   │   └── cases.json        # 触发、边界、失败与证据用例
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

每个 Skill 都把主要指令放在 `SKILL.md` 中，只在确实有用时增加辅助资源：

- `agents/`：可选的客户端专属元数据，核心 Skill 不依赖它。
- `evals/`：覆盖路由、边界、恢复和证据的真实行为用例；它们是评测输入，不单独构成质量证明。
- `references/`：只在相关任务中加载的详细知识。
- `scripts/`：可重复运行或需要确定性结果的操作。
- `assets/`：用于生成结果的模板、图片或其他源文件。

## 新 Skill 如何进入仓库

只有当一套流程经过足够实践，能够沉淀出可靠判断并顺利交接给下一阶段时，才会整理成新的 Skill。每个新增 Skill 都应该具备：

- 精确的名称和描述，让自动发现足够可靠。
- 保持兼容开放 Agent Skills 规范的 frontmatter。
- 清楚的生命周期阶段、触发条件、范围边界、输入、输出和交接关系。
- 简洁的 `SKILL.md`，把条件性细节放进 `references/`。
- 只在可重复执行或确定性校验确实有价值时增加脚本。
- 脱离当前对话也能独立检查的实际交付物。
- 覆盖触发、非触发、失败恢复和禁止行为的机器可读评测用例。
- 与 `skills.json` 对应的目录记录，以及通过的仓库校验结果。

开发、测试、App Store 提交和发布后迭代仍是规划中的方向。上方生命周期表是当前能力范围的准确信息源。

## 反馈与共建

欢迎通过 GitHub Issues 提交建议、真实使用反馈和聚焦的改进。如果希望增加新的 Skill，请尽量说明它服务于独立开发的哪个阶段、需要改善哪些判断，以及怎样的结果才算可检查、可交付。

## 设计参考

本仓库的导航和目录设计参考了 [`alchaincyf/huashu-skills`](https://github.com/alchaincyf/huashu-skills) 在“面向人的需求路由、机器可读 Skill 索引和明确安装协议”上的做法。`interactive-prototype` 另参考并改造了 MIT 开源项目 [`alchaincyf/huashu-design`](https://github.com/alchaincyf/huashu-design) 的 HTML 原型与浏览器验收方法，具体来源、改造边界和许可证保留在该 Skill 的 [`THIRD_PARTY_NOTICES.md`](skills/interactive-prototype/THIRD_PARTY_NOTICES.md)。

## 许可协议

本仓库使用 [MIT License](LICENSE)。
