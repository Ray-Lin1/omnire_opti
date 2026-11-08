# 多实验同步视频

所有源视频使用共同约 533×300 相机评估尺寸，编码后六相机画布均为 1600×608、19 帧、2 FPS。源时刻为留出集 t10、t20、…、t190；按相同源帧编号拼接，不做插帧、锐化或额外缩放。视频为有损编码材料，量化结果以原始指标为准。

## 视频入口

- [前视快速总览](all_experiments_front.mp4)：9.5 秒，GT、baseline、EXP-001～005 同屏。
- 全部实验、全部相机：`all_experiments_all_cameras.mp4`，57 秒，每个相机播放同一组 19 个留出时刻，再切换相机。
- 重点四宫格：`control_exp004_exp005_all_cameras.mp4`，GT、EXP-001、004、005，57 秒，四宫格布局便于放大检查。

后两段较大的完整视频位于本地 `artifacts/20261108-fresh/combined-videos/`，不提交 Git；前视短总览及本说明、制作脚本提交保存。

七宫格顺序从左到右、从上到下：

| 第 1 列 | 第 2 列 | 第 3 列 | 第 4 列 |
|---|---|---|---|
| GT | baseline 29,381 步 | EXP-001 原配置续训 | EXP-002 高清续训 |
| EXP-003 背景增密续训 | EXP-004 原配置从头 | EXP-005 高清从头 | 说明 |

四宫格为左上 GT、右上 EXP-001、左下 EXP-004、右下 EXP-005。EXP-001～005 均为 40,000 步；baseline 为 29,381 步，训练轨迹不同。

## 相机分段

| 起始秒数 | 相机 |
|---:|---|
| 0 | CAM_FRONT |
| 9.5 | CAM_FRONT_LEFT |
| 19 | CAM_FRONT_RIGHT |
| 28.5 | CAM_BACK_LEFT |
| 38 | CAM_BACK |
| 47.5 | CAM_BACK_RIGHT |

各相机画面从源 MP4 的六相机布局裁切：横向边界为 0、533、1067、1600，纵向为 0、304、608。保留解码像素，在 534 像素宽的格子中居左放置，较窄列仅补背景，不拉伸画面。源视频本身已有编码及画布调整，不声称其等同于无损原始 PNG。

对五个实验的 GT 视频分别验证了全部 19 帧与 baseline GT 的最近帧匹配，检查时间顺序；同时核对源/输出帧数、帧率、尺寸，并解码输出首、中、尾帧。详细校验记录仅保存在本地 `artifacts/20261108-fresh/combined-video-verification.json`。

复现：在仓库根目录运行 `python tools/make_experiment_comparison_video.py`，需本地完整归档以及 FFmpeg、ffprobe、NumPy、Pillow。
