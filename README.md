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

技能由支持读取 Skill 指令和本地文件的 AI Agent 执行。两个 Python 工具使用 Python 3 标准库，无须额外 Python 依赖；HTML 阅读及导出需要现代浏览器，相关 JavaScript 库已随包提供。

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
python scripts/build_report_html.py /path/to/private/D-2030-05-17.md
```

第二条命令仅为虚构参数示例。日期工具不传家庭参数时仍可计算报告周期，未知的家庭字段返回 `null`。HTML 工具将已有 Markdown 转为阅读版，不会自行生成分析或更新档案。

运行维护测试：

```sh
python -m unittest discover -s scripts -p "test_*.py"
node scripts/test_png_encoder.cjs
```

## 文件导航

| 路径 | 用途 |
| --- | --- |
| [SKILL.md](SKILL.md) | 技能入口与工作流程 |
| [agents/openai.yaml](agents/openai.yaml) | 展示名称与默认调用提示 |
| [references/](references/) | 分级报告规范、证据规则和运行协议 |
| [assets/](assets/) | 空状态模板、空知识模板及离线 HTML 资源 |
| [scripts/](scripts/) | 日期计算、HTML 生成及测试 |

## 作者与第三方资源

作者：阿昌；公众号：阿昌正传。报告模板底部保留这一署名。

离线渲染使用的第三方库附带其原始许可证：

- [marked 许可证](assets/web/vendor/marked-LICENSE.md)
- [html2canvas 许可证](assets/web/vendor/html2canvas-LICENSE.txt)

本仓库暂未为自有内容指定开源许可证；第三方资源适用各自随附的许可证。
