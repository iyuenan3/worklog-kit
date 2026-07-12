# vault 维护配方

> 日常体检与修复走 skill：说「检查」看体检报告，说「维护 vault」处理（见根 `CLAUDE.md` 路由）。本文档收录 skill 之外的两份配方：月度自动体检、`~/.claude` memory 瘦身。维护工序思想参考开源项目 InquisiMind/digital-life，在此致谢。

## 一、月度自动维护（报告模式）

worklog-maintain 的授权模型是「交互触发才动文件，无人值守只出报告」，所以可以放心把体检挂成定时任务：夜里只产报告，白天你说一声才真正修。

用 Claude Code 的 schedule 功能（定时云端 / 本地例行任务）建一条月度任务，在 vault 目录的会话里说：

```
每月 1 号早上 8 点跑一次：维护 vault（报告模式）
```

schedule 会把它建成月度 routine。到点触发时属于无人值守场景，worklog-maintain 按授权模型只跑 `lint --health` 出报告；你看到报告后，白天任意时刻交互说「处理体检项」即完成修复。

不用 schedule 也行：日常 ingest 已内置静默提醒（有待维护项时日记末尾出现一行体检提示），月度任务只是兜底，防止你长期不看日记尾行。

## 二、`~/.claude` memory 的 MEMORY.md 瘦身（手工配方）

worklog-maintain v1 只管 vault 仓内（git 可回滚）；`~/.claude/projects/<本 vault 对应目录>/memory/` 在 git 之外、误删不可恢复，所以瘦身是手工工序，建议每季度一次：

1. **先备份**（不可回滚，这步不能省）：

```bash
MEM=~/.claude/projects/<本 vault 对应目录>/memory
cp -R "$MEM" "$MEM.bak-$(date +%Y%m%d)"
```

2. 打开 `MEMORY.md` 索引逐行过：**已过时**（记的约束 / 决策已被推翻）→ 删对应记忆文件 + 索引行，若根因被证伪、值得留审计线索的改写为一句纠错而非直接删；**重复**（两条记同一件事）→ 合并进更完整的一条，删另一条 + 索引行；**description 漂移**（内容还对但描述已不准，影响召回）→ 改写 description。
3. 校验索引与文件一一对应：每条索引行都有对应文件、每个文件都有索引行（孤儿行与漏索引都要修）。
4. 确认无误后可删备份；拿不准的条目宁可留着，记忆的成本远低于误删。
