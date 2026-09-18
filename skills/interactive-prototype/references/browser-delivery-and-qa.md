# 浏览器交付与验收

## 默认输出结构

```text
<output-dir>/
├── index.html                # PC 浏览器中的展示壳与设备窗口
├── prototype.html            # 可以单独打开的交互产品
├── prototype-brief.md        # 产品契约、范围与假设
├── prototype-spec.json       # 屏幕、主任务和可执行步骤
├── prototype-report.md       # 验收证据与已知边界
├── assets/                   # 本地字体、图片和图标，可选
└── screenshots/              # 浏览器验收截图，自动生成
```

`index.html` 和 `prototype.html` 必须使用相对路径，核心体验不得依赖构建服务、远程脚本或临时 URL。较小原型优先用无构建的 HTML/CSS/JavaScript；已有代码库可沿用现有技术栈，但仍需提供稳定的预览入口。

## 初始化

```bash
python3 <skill-root>/scripts/init_prototype.py \
  --output outputs/my-product-prototype \
  --title "My Product" \
  --mode mobile
```

`--mode` 支持 `mobile`、`desktop`、`responsive`。可用 `--force` 覆盖脚本之前生成的同名骨架，但不要用它覆盖用户已有设计。

初始化文件带有 `data-scaffold="true"` 和 `status: draft`。它们是未完成信号。完成产品界面和状态后移除 scaffold 标记，将规格状态改为 `complete`，并填写报告。

## 静态校验

```bash
python3 <skill-root>/scripts/validate_prototype.py <output-dir> --json
```

制作中可以使用：

```bash
python3 <skill-root>/scripts/validate_prototype.py <output-dir> --allow-draft --json
```

`--allow-draft` 只用于发现结构问题。它允许骨架和草稿状态，不会把结果变成完整交付。

校验范围包括：

- 必需文件、JSON schema、平台模式、屏幕和主任务；
- 规格里的屏幕、动作选择器和页面 DOM 是否对应；
- 重复 ID、未命名按钮、缺少 viewport、骨架占位和外部脚本依赖；
- 浏览器展示壳是否仍包含 iframe、设备窗口、重置和单独打开入口；
- 是否提供 `prefers-reduced-motion` 处理。

## 浏览器主路径

若环境已有 Playwright：

```bash
node <skill-root>/scripts/browser_smoke.mjs <output-dir>
```

脚本直接打开本地 `prototype.html`，按 `prototype-spec.json` 执行主任务，并生成：

- `screenshots/overview.png`：电脑中的完整展示壳；
- `screenshots/step-00-start.png`：初始状态；
- `screenshots/step-NN-<action>.png`：每一步后的状态；
- `screenshots/browser-smoke.json`：动作、断言、脚本错误和结果。

如果提示未安装 Playwright，使用当前可用浏览器打开 `index.html`，逐步执行同一份规格并截图。报告必须写“人工浏览器验收”，不能写“自动测试通过”。

## 规格动作

| action | 必填字段 | 行为 |
| --- | --- | --- |
| `click` | `selector` | 点击一个可见元素 |
| `fill` | `selector`, `value` | 清空并填写输入控件 |
| `select` | `selector`, `value` | 选择下拉项 |
| `press` | `selector`, `value` | 聚焦元素后按键 |
| `wait` | `value` | 等待指定毫秒，范围 0–5000 |

可选 `expect`：

```json
{
  "screen": "result",
  "visible": "[data-test=\"success-card\"]",
  "text": {
    "selector": "[data-test=\"result-title\"]",
    "includes": "已保存"
  }
}
```

`screen` 通过可见的 `[data-screen="..."]` 判断。不要把隐藏的全部页面同时留在可访问树中；隐藏状态使用 `hidden`、`display: none` 或按状态渲染。

## 人工视觉检查

自动点击通过后仍要目视检查：

1. 初始 3 秒内能否看懂产品和主动作。
2. 每次点击后是否有及时且位置合理的反馈。
3. 内容是否使用可信文案与数据，而非模板占位。
4. 手机窗口是否完整显示，滚动、弹层和键盘区域是否合理。
5. 桌面端是否真正利用空间，而非放大手机页面。
6. 窄屏和大屏是否出现裁切、溢出、过小文字或漂移。
7. 返回、重置、失败恢复和重复操作是否保持状态一致。

## 完成边界

可以说“高保真可点击原型已完成并通过主路径验收”，前提是完整文件、静态校验和浏览器点击证据都存在。若只完成页面或静态校验，应分别称为“高保真视觉稿”或“原型骨架”，并列出未验证内容。

原型中的登录、支付、AI 生成、同步、通知和数据保存可以模拟交互和状态，但不代表真实服务已经接入。
