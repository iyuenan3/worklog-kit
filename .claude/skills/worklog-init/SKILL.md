---
name: worklog-init
description: worklog vault 初始化向导。用户在 worklog-kit 模板仓里说「初始化 / init / setup」时触发：环境预检 + 仓库 visibility 检测 + 交互生成 worklog.config.yaml + 项目扫描预览与定级 + 三件套全局安装 + 可选移除开发文档 + 生成上手指南。这是整个系统唯一的交互式环节，之后的日常 ingest 全程无人值守。
---

# worklog-init：vault 初始化向导

> 你是 worklog vault 的初始化向导。与 ingest 相反，**本 skill 是交互式的**：这是用户唯一一次需要坐在屏幕前配置的环节，每一步都可以提问确认。与用户交互使用用户的语言（跟随其消息语言）。

## 前置与安全

- 只在 worklog-kit 模板仓（根目录有 `worklog.config.yaml` + `wiki/` + `diaries/`）里运行；不在则说明并退出。
- **重跑安全**：config 含 `initialized_at` 字段（Step 3 写入的初始化标记）→ 进入「更新模式」，只改用户点名的项；绝不整文件覆盖已配置的 config、绝不覆盖用户改过的骨架文件。
- 本 skill 不做任何网络拉取（三件套随模板自带）；只在 visibility 检测与鉴权预检时调用 gh / git 远端命令。

## 流程（7 步，顺序执行）

### Step 1 · 环境预检

逐项检查并汇总成一张表（✅ / ⚠️ / ❌）：

```bash
uname -s                                   # Darwin / Linux 通过；其它（原生 Windows）→ ❌ 终止并说明仅支持 macOS / Linux
grep -qi microsoft /proc/version 2>/dev/null && echo WSL   # uname 区分不了 WSL；命中 → ⚠️ 标注「WSL 实验性支持」
git config --get user.name; git config --get user.email   # 缺 → 引导设置（commit 必需）
git remote -v                              # 无 remote → ⚠️ 提示先建私有远端（无人值守 push 需要）
git ls-remote --heads origin 2>&1 | head -3   # push 鉴权 dry-run（仅当上一步检测到 remote 才跑；失败 → 给 SSH key / gh auth 两条修复路径，推荐 SSH key 无过期问题）
command -v gh && gh auth status           # 无 gh 或未认证 → ⚠️（visibility 检测与 github 源需要；修复命令 gh auth login，可后补）
command -v python3                         # 无 → ⚠️（lint 与部分脚本需要）
command -v uv || command -v uvx            # 无 → ⚠️（素材摄入 markitdown 需要；可后补）
```

❌ 项修完再继续；⚠️ 项记入收尾报告，不阻塞。

### Step 2 · 仓库 visibility 检测（隐私第一道闸）

```bash
gh api "repos/{owner}/{repo}" --jq .visibility   # owner/repo 从 git remote 解析
```

- 结果非 `private` → **红色警告并暂停**：日记与 wiki 将包含你的工作细节，必须先到仓库 Settings 改为 Private 再继续。用户明确表示接受公开风险才可跳过（记入报告）。
- 无 gh / 无 remote → 提醒「无法自动检测，请自行确认私有」并记入报告。

### Step 3 · 生成 config（问「你的工作都发生在哪」）

交互收集后**整体展示一遍再写入** `worklog.config.yaml`：

1. **语言** `language`：zh / en（决定骨架 locale 与写作规范）
2. **时区** `timezone` 与 **日期分割线** `day_boundary`（解释：凌晨工作归前一天的分界，按作息选，默认 07:00）
3. **身份** `identities`：从 `git config --get user.email` 预填，追问「还有别的 commit 署名 email 吗（公司邮箱等）」
4. **数据源** `sources`，逐类问：
   - 本机项目都在哪些目录 / 硬盘？→ `local-git.roots`（多硬盘 = 多 root；提示：给具体的项目父目录而非家目录，自动发现深度有限且不跟随符号链接）
   - 有 GitHub / GitLab 账号且工作会 push 上去吗？→ `github` / `gitlab` 源
   - 有「工作不经过托管平台」的远程机器吗？→ `remote-ssh`（提示连通性文档，推荐 Tailscale）
   - 用飞书等 IM 协调工作吗？→ `im` 源（提示：需另跑 feishu-setup 完成认证；默认只记你自己发的消息）
   - 有不用 git 的项目目录（写作 / 设计）吗？→ `local-dir` 显式声明

写入时附加 `initialized_at: <ISO8601 时间戳>`（重跑判据）。`language: en` 时以 `templates/locale/en/worklog.config.yaml` 为底生成（英文注释 + 英文 `diary_title_template`），再填入上面收集的值。

### Step 4 · locale 骨架实例化

- `language: en` → 用 `templates/locale/en/` 整套覆盖对应产品件：`wiki/` 三件、根 `CLAUDE.md`、`AGENTS.md`、`AIREADME/` 全套（config 已在 Step 3 处理）。zh 为默认，无动作。
- **出厂检测**：仅覆盖用户未改过的文件，判据 = `git diff --name-only HEAD -- <path>` 无输出且该文件与模板仓出厂内容一致（本仓 clone 后未动即满足）；有用户改动的文件跳过并说明。

### Step 5 · 扫描预览与项目定级（同意机制第一道闸，PRD §6.4）

```bash
bash .claude/skills/worklog-init/scripts/discover.sh <roots...>
```

- 把发现的项目列成表（含 IGNORED 项与未挂载 root），向用户逐个或按目录批量定级：`detail` / `summary` / `presence` / `exclude`。
- 强调一句：**这份清单就是「会被记录的范围」**，雇主 / 敏感项目建议 summary 或 exclude；漏掉的目录回 Step 3 补 root。
- 定级结果写进 config 的 `projects.overrides`，条目格式**必须**是 `- {match: "<glob>", level: detail|summary|presence|exclude}`（例：`- {match: "~/work/**", level: summary}`）；全部默认 detail 的可不写 override。
- 提醒：日后新发现的项目默认 `presence` 级（安全默认），晨报会列「待定级」。

### Step 6 · 三件套全局安装 + pitfalls 纪律行

对 `aireadme` / `stash` / `pitfalls` 逐个执行：

```bash
mkdir -p ~/.claude/skills
# 目标已存在 → diff -rq 比较，向用户提示 覆盖 / 跳过（不默改用户已有的全局 skill）
cp -r .claude/skills/<name> ~/.claude/skills/
```

pitfalls 装好后，展示这行全局纪律并**征得同意**后追加进 `~/.claude/CLAUDE.md`（文件不存在则新建；先 grep 查重，已有则跳过；只追加，绝不覆盖已有内容）：

```
- 写 bash / 改 git 历史 / macOS 文件·locale 操作 / 配 DNS·Docker·反代 / Read·Edit 改大文件前，先查 pitfalls 的 LIBRARY.md。
```

### Step 7 · 收尾

1. **可选移除开发文档**：询问是否删除 `docs/dev/`（worklog-kit 的开发文档，vault 用户不需要）。同意则 `git rm -r docs/dev/` 并删除根 CLAUDE.md 末尾的 dev 指针行。
2. **生成上手指南**：按 language 把 `.claude/skills/worklog-init/templates/GETTING_STARTED.<lang>.md` 复制为 vault 根 `GETTING_STARTED.md`（已在 .gitignore）。
3. **commit**：消息按 language（zh `init: worklog vault 初始化` / en `init: worklog vault initialized`），含 config 与骨架变更；Step 1 检测到 remote 才 push 一次验证链路，无 remote 则跳过并在报告提示。
4. **收尾报告**：预检 ⚠️ 清单、visibility 结论、config 摘要（几个源 / 几个项目 / 各级别计数）、下一步指引（读 GETTING_STARTED；ingest 就绪后今晚就能「记录今天」）。

### Step 8 · 冷启动回填（可选）

问一句「要不要把最近几天回填成简版日记（默认 3 天）」；同意则按 worklog-ingest 的**回填模式**逐天生成（概览 + 时间线 + commit 清单，只回填定级为 detail / summary 的项目，标注「自动回填、信息有限」），已存在的日期跳过。

## 边界

- 本 skill 绝不写入任何凭证；用户给出 token 类信息时引导放 `worklog.config.local.yaml`。
