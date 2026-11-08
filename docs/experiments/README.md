# 实验记录

[昨晚结果汇总](RESULTS-20261108.md) · [模型索引](model_index_20261108.json) · [历史 baseline](BASELINE-001-nuscenes-scene0061.md)

| 实验 | 内容 | 初始化 | 状态 | 报告 |
|---|---|---|---|---|
| EXP-001 | 原配置续训对照 | baseline 29,381 步 | 已完成至 40,000 步 | [报告](exp-001-control.md) |
| EXP-002 | 高清输入续训 | 同一 baseline | 已完成至 40,000 步 | [报告](exp-002-resolution.md) |
| EXP-003 | 重新开放背景增密 | 同一 baseline | 已完成至 40,000 步 | [报告](exp-003-bg-densify.md) |
| EXP-004 | 原配置从头训练 | 数据初始化，step=0 | 40,000 步及评估完成，331 文件回传校验通过 | [记录](exp-004-from-scratch-control.md) |
| EXP-005 | 高清输入从头训练 | 数据初始化，step=0 | 2026-11-08 13:42 左右启动，训练中 | [记录](exp-005-from-scratch-resolution.md) |

Git 保留实验说明、配置、关键原始指标、短留出视频和必要对比图。模型、完整日志、逐帧输出及审计材料保存在本地 `artifacts/`。
