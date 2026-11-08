# EXP-005：高清输入从头训练

状态：**已进入顺序队列，等待 EXP-004 完成**。分支 `codex/exp-005-from-scratch-resolution`，运行源码 `51bfdac3e202d6373c42705e0a7e01f36ac11f5f`。

## 目的与设置

检验从初始化阶段使用高清输入，配合完整学习率与早期增密，是否比晚期切换更有效。

与 EXP-004 唯一主要变量是六相机加载尺寸由约 533×300 改为 **800×450**。同样从数据初始化、step=0、seed=0、目标 40,000 步，采用相同损失、增密策略、划分和保存频率；不加载 EXP-004 或历史 baseline 的权重。

[完整配置](../../configs/experiments/exp-005-from-scratch-resolution.yaml)

```bash
export PYTHONPATH="$PWD"
python tools/train.py --config_file configs/experiments/exp-005-from-scratch-resolution.yaml --output_root /root/omnire_exp_20261108_fresh/results --project scene0061 --run_name exp-005-from-scratch-resolution
```

在原生 800×450 和共同约 533×300 两种尺寸下分别用 `tools/stream_eval.py` 独立评估。原生指标不与较低尺寸的结果直接混比。

云端结果目录：`/root/omnire_exp_20261108_fresh/results/scene0061/exp-005-from-scratch-resolution/`。本地回传目录：`artifacts/20261108-fresh/exp-005-from-scratch-resolution/`。

## 结果

尚未开始本组的优化迭代，不填写指标或收益结论。最终以同一步数、共同分辨率的留出集 PSNR/SSIM/LPIPS、区域指标、同帧细节与运行成本共同判断。
