# EXP-004：原配置从头训练

状态：**云端训练中**。2026-11-08 08:31 左右启动；分支 `codex/exp-004-from-scratch-control`，运行源码 `51bfdac3e202d6373c42705e0a7e01f36ac11f5f`。

## 目的与设置

为从头训练的高清实验建立公平对照，不使用昨晚任何模型作为初始化。

- scene-0061、191 时刻、六相机、seed=0，沿用原划分和评估掩码。
- 从 LiDAR、随机点、实例与 SMPL 数据初始化，**没有 `--resume_from`**。
- 全局 step 从 0 开始，位置学习率从 `1.6e-4 × scene_radius` 开始，目标 40,000 步。
- 加载尺寸约 533×300；背景停止增密步数为 20,000。
- 每 5,000 步保存检查点；稳定训练每 15 分钟查询一次。

[完整配置](../../configs/experiments/exp-004-from-scratch-control.yaml)

```bash
export PYTHONPATH="$PWD"
python tools/train.py --config_file configs/experiments/exp-004-from-scratch-control.yaml --output_root /root/omnire_exp_20261108_fresh/results --project scene0061 --run_name exp-004-from-scratch-control
```

评估在模型保存后独立执行 `tools/stream_eval.py`，逐帧累计指标并写视频，避免全场景结果常驻内存。EXP-005 与本组使用相同评估实现。

云端结果目录：`/root/omnire_exp_20261108_fresh/results/scene0061/exp-004-from-scratch-control/`。本地回传目录：`artifacts/20261108-fresh/exp-004-from-scratch-control/`。

## 结果

尚未完成，不填写指标或收益结论。主要对照为本组与 EXP-005 同为 40,000 步、同为约 533×300 评估尺寸的留出集结果。
