# BASELINE-001 视频与指标

唯一基线：OmniRe / nuScenes scene-0061 / **step 29,381**。完整设置见 [基线报告](../BASELINE-001-nuscenes-scene0061.md)。

## 播放入口

| 内容 | 视频 |
|---|---|
| 全场景重建 | [scene0061_step29381_full_rgb.mp4](videos/scene0061_step29381_full_rgb.mp4) |
| 全场景真值 | [scene0061_full_gt.mp4](videos/scene0061_full_gt.mp4) |
| 留出集重建 | [scene0061_step29381_test_rgb.mp4](videos/scene0061_step29381_test_rgb.mp4) |
| 留出集真值 | [scene0061_test_gt.mp4](videos/scene0061_test_gt.mp4) |
| 新视角 | [scene0061_step29381_novel_front.mp4](videos/scene0061_step29381_novel_front.mp4) |

这些文件是原始 H.264 MP4，直接播放或下载即可。每个文件约 0.7–8.7 MiB，五份视频合计约 20.6 MiB。未进行二次转码。

## 后续实验怎样对比

优先并排展示 **真值 / 本基线 / 优化结果** 的留出集视频；全场景视频用于观察整体布局、动态目标和时间一致性。

| 比较条件 | 固定要求 |
|---|---|
| 数据与相机 | 同一 scene-0061、同一六相机拼图排列 |
| 全场景序列 | 191 帧，视频帧索引 0–190 对应数据时刻 0–190 |
| 留出集序列 | 19 帧，视频帧索引 0–18 对应数据时刻 10、20、…、190 |
| 播放速度 | 全场景 10 FPS；留出集 2 FPS |
| 分辨率 | 六视角拼图 1600×608，沿用相同布局和填充规则，不单独裁切或缩放某个结果 |
| 同帧截图 | 以数据时刻标记；例如数据时刻 100 对应全场景索引 100、留出视频索引 9 |
| 定量评估 | 使用相同评估集合与掩码，读取原始评估 JSON；不从编码视频重新计算指标 |

全场景与留出集播放时间轴不同，不能用相同“第几秒”直接对齐两类视频。新视角视频为 24 FPS、191 帧，无匹配真值，仅作定性展示；未来只有相机轨迹一致时才能直接比较。

帧率、帧数与尺寸已由 MP4 容器元数据核对，重建/真值对应项一致。这不是逐帧解码或全部画面的人工验收。

## 来源与完整性

- [metrics_test.json](metrics_test.json)、[metrics_full.json](metrics_full.json)：最终基线原始正式评估。
- [video_metadata.json](video_metadata.json)：帧数、尺寸、编码和播放时长。
- [provenance.json](provenance.json)：原文件路径、大小和 SHA256，复制前后核对一致。

原始视频文件名中的 29382 是导出循环编号，本目录使用模型实际步号 29381 命名。原文件未被覆盖。
