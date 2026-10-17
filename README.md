# ac-bedtime-news · 每日睡前新闻

将亲子睡前对话整理成有依据、有温度、可长期保存的成长记录。这是供 AI Agent 使用的 Skill 通用版，不是时事新闻播报工具，也不是自动录音或独立运行的应用。

## 能做什么

- 分析匿名化的亲子对话，生成日报、周报、月报和年度报告。
- 同时关注孩子的表达、需求与成长，以及家长的倾听和回应。
- 默认交付完整文字、Markdown 和离线 HTML；HTML 提供 PDF 与单张长图 PNG 导出按钮。
- 维护观察点、修复记录、里程碑与家长确认的长期知识。
- 年度家长分析与给孩子的成长回忆录分别生成，私有分析不进入孩子的回忆录。

## 安装

将本仓库克隆或解压为名为 `ac-bedtime-news` 的文件夹，放到你的 Agent 的技能目录中。保持 `SKILL.md`、`agents/`、`references/`、`scripts/` 和 `assets/` 的相对位置不变。使用其他支持 Skill 的工具时，按该工具的导入方式加载整个文件夹。

```sh
git clone https://github.com/19archan88/ac-bedtime-news.git
```

技能由支持读取 Skill 指令和本地文件的 AI Agent 执行。Python 工具使用 Python 3 标准库，无须额外 Python 依赖；HTML 阅读及导出需要现代浏览器，相关 JavaScript 库已随包提供。

## 第一次使用

提供对话日期、匿名化逐字稿、参与对话者的角色，以及你愿意提供的孩子年龄或生日、学段信息。家长备注可选。首次启动会提醒设置孩子及家庭成员信息，并保存到私有的 `FAMILY-profile.json`。根据用户设置的生日或年龄基准、入学日期、年级基准和每年升级规则，自动推算对应报告日期的年龄、入学时长和年级；未知资料不填默认家庭值。详见 [家庭设置指南](references/family-setup.md)。

示例请求（请替换为自己的材料）：

> 请使用 $ac-bedtime-news 分析下面的睡前对话。对话日期是……，孩子代号是……，年龄是……，参与者是……。请将报告保存在我指定的私有档案目录。以下是匿名化逐字稿：……

只想审阅时，可以说明“先给审阅稿，不归档”；只想要某种格式时，直接指定。周、月、年汇总需要对应历史材料，缺失情况会明确说明。

## 数据与边界

- 家庭配置、录音、逐字稿、报告和运行状态保存在仓库以外的私有档案目录。不要将这些文件提交到公开仓库。
- 本仓库只含指令、空模板、渲染资源与测试；测试日期和示例不代表任何使用者的家庭资料。
- 转写和云存档需要用户另外提供材料或接入工具；技能不会凭空获得这些能力。
- 心理学视角用于形成有依据的观察与讨论，不作诊断。推断须与事实、原话分开。
- 周期按周六至周五计算，周五决定该周的月、年归属。年级按家长确认的学籍基准、升级日期和学制自动推算；留级、跳级等变化按新的生效日期保存，历史报告沿用当时规则。

## 本地工具

在技能目录内运行：

```sh
python scripts/calendar_context.py date 2030-05-17
python scripts/calendar_context.py date 2030-05-17 --birth-date 2023-04-12 --school-start 2029-08-20
python scripts/calendar_context.py date 2030-05-17 --profile /private/FAMILY-profile.json --child-id child-1
python scripts/calendar_context.py month 2030-05
python scripts/calendar_context.py year 2030
python scripts/profile_store.py status --archive /path/to/private --child-id child-1
python scripts/prepare_report.py /path/to/private/D-2030-05-17.md --archive /path/to/private --child-id child-1
```

第二条命令仅为虚构参数示例。日期工具不传家庭参数时仍可计算报告周期，未知的家庭字段返回 `null`。正式报告入口检查初始化状态，未回应时停止并提示补充；档案更新命令见家庭设置指南。底层 build_report_html.py 只负责排版，不代表已完成初始化。用户明确选择临时模式可使用 `--temporary --onboarding-acknowledged`，不创建家庭档案。

完整虚构示例见 [Markdown](examples/D-2030-05-17.md) 与 [离线 HTML](examples/D-2030-05-17.html)。增强排版初始化失败时仍可阅读完整文字原稿。

日报时间线用简短标签辅助浏览，重要解释与事实边界保留在正常字号的正文中。加粗集中于关键句，较长分析按议题分段；具体约定见 [HTML 编排规范](references/html-delivery.md#原稿编排)。既有报告不会因标签较长而被自动截断。

运行维护测试：

```sh
python -m unittest discover -s scripts -p "test_*.py"
node scripts/test_png_encoder.cjs
npm install
npm run test:presentation
```

后两条仅供维护者运行 DOM 集成测试，需要 Node.js 18 或更新版本；开发依赖不会进入离线 HTML，也不是使用技能的前置条件。可用 `PYTHON` 环境变量指定 Python 可执行文件。DOM 测试核对实际生成页面的结构和内容，不能替代真实浏览器的布局、打印与 PNG 导出检查。

呈现层以随包原有设计为基础，保留必要修复和纯文本故障回退；输入约定与各周期示例的适用范围见 [HTML 规范](references/html-delivery.md#markdown-与渲染器的约定)。提示词版本保持 `v2.0`，独立视觉版本以构建器中的 `renderVersion` 为准。

## 文件导航

| 路径 | 用途 |
| --- | --- |
| [SKILL.md](SKILL.md) | 技能入口与工作流程 |
| [agents/openai.yaml](agents/openai.yaml) | 展示名称与默认调用提示 |
| [references/](references/) | 分级报告规范、证据规则和运行协议 |
| [assets/](assets/) | 空状态模板、空知识模板及离线 HTML 资源 |
| [scripts/](scripts/) | 日期计算、HTML 生成及测试 |

## 开源许可与版权

Copyright (c) 2026 阿昌 (19archan88)。公众号：阿昌正传。

除另有说明的第三方资源外，本项目的 Skill 指令、说明文档、脚本和模板采用 **MIT License**。完整授权条款以根目录 [LICENSE](LICENSE) 为准；以下中文说明仅用于帮助理解，不增设限制。

- 允许使用、复制、修改、再分发和商业使用，也允许闭源衍生版本。
- 分发本项目副本或实质性部分时，须保留版权声明和 MIT 许可声明。
- 软件按现状提供，不作保证；免责与责任限制以 LICENSE 原文为准。
- 第三方资源继续适用各自的许可证，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

### 署名与生成报告

报告模板默认显示“作者：阿昌 丨 公众号：阿昌正传”，用于标识模板来源，不表示阿昌撰写或审阅了使用者的报告。使用者可以修改或移除这一可见署名；MIT 不要求在报告中展示公众号。修改署名不免除再分发代码时保留版权及许可声明的义务。

离线 HTML 会内嵌本项目与第三方库的许可信息，不占用正文版面。用户输入、家庭配置、录音、逐字稿和独立生成的报告正文不会仅因使用本 Skill 而自动适用 MIT，也不需要公开。HTML 中复制的模板和库代码仍遵守各自许可证。

### 使用说明

本 Skill 提供亲子对话整理与观察辅助，不能替代医疗、心理诊断或专业服务，也不承诺特定成长结果。发布问题反馈或改进建议时，请使用虚构或充分匿名化的材料，不上传真实家庭档案。

## 本次维护更新（2026-10-18）

视觉版本 `2.4.3`：加深小号橙色信息文字及编号，保留原有布局、正文和装饰配色。公开示例已使用当前构建器重新生成。源码与自动化测试不能代替真实浏览器和导出文件的视觉验收。

### 档案合并修复（2026-10-18）

修复已有 `onboarding.decisions` 后追加 `family_members: deferred/declined` 被误判为成员列表的问题。成员按 id 合并仅作用于档案顶层，学籍历史合并仅作用于孩子的 `school_baselines`；其他嵌套同名键正常合并。已有档案无需迁移，更新技能后重新提交上次未成功保存的补丁即可；不要清空档案。
