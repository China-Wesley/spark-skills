# 照书答人生 · book-life-advisor

基于 eternity4719 的《高性价比人生指南》回答人生困惑。每个实质性建议都必须有已读取的书内依据，并注明第几节、第几条、原标题、固定原文链接和书中引用。没有足够依据就明确说明。

## 安装与调用

将整个 `skills/book-life-advisor` 目录复制或链接到当前 Agent 支持的 Skills 目录。不要只复制 `SKILL.md`；正文、检索脚本和校验清单都是包的一部分。核心规则通用于支持 Agent Skills 的客户端，`agents/openai.yaml` 只是可选的界面元数据。

示例请求：

```text
使用 book-life-advisor 回答：朋友让我给贷款担保，我不想伤感情，该怎么办？
只依据这本书，每项建议注明第几节、第几条和原始出处。
```

Agent 先读 [SKILL.md](SKILL.md)，再检索并读完整相关条目，包括条件、备注、争议和来源。检索脚本仅使用 Python 3.9+ 标准库，可完全离线运行；没有 Python 时也可直接读取内置 Markdown。

在本 Skill 目录中执行：

```bash
python3 scripts/book.py verify
python3 scripts/book.py search '朋友 担保'
python3 scripts/book.py read 08.18
```

## 内容与边界

- 内置完整原文 34 节、654 条，另含 README、长文、引用核对材料与许可，共 163 份原始文件。
- 固定到 2026-10-04 的提交 `bd25430e9a380bdd3b9af728fcfc39daff31f8d2`，不会自动更新。快照不能证明法律、政策或医学资料今天仍有效。
- 只解释书内支持的内容，不用模型常识或外部资料补充建议；医疗、法律和财务条目保留原文的专业判断前提。即时安全仍遵守宿主要求，书外安全援助不得冒充书内出处。
- A/B/C 是作者的证据等级；没有对全部原始论文、法规和数字进行独立事实核验。
- [评估场景](evals/cases.json) 是待执行的行为标准，不是已通过的模型评测成绩。`verify` 检查文件完整性，不证明每个答案或原书主张正确。

独立阅读版 PDF 位于仓库的 [books/HowToLiveBetter.pdf](https://github.com/China-Wesley/spark-skills/blob/main/books/HowToLiveBetter.pdf)，安装 Skill 不需要它。PDF 的页码不能替代 Skill 固定快照的节条号和源码行号。

## 来源与许可

原书：[eternity4719/HowToLiveBetter](https://github.com/eternity4719/HowToLiveBetter)。书籍文字采用 CC BY 4.0，新增 Skill 规则与脚本采用 MIT；详见 [ATTRIBUTION.md](ATTRIBUTION.md)。内置原始文件逐字节保留，仓库接入仅统一评估场景的字段并补充使用说明。

This portable Skill answers questions strictly from the bundled Chinese book snapshot and cites exact chapter/item locations. Copy the whole directory to your Agent's skill location. Python helpers are optional and offline. Book text is CC BY 4.0; Skill instructions and code are MIT. See the attribution file for the source and revision.
