# Codex 配套第三方工具

该目录存放第三方程序、模型与独立源码仓库。不要把工具二进制、模型、虚拟环境或嵌套 Git 仓库提交到上级技能仓库。

## SpriteGen v2.2.0

- 源码：`E:\ChatGPT_Skills\ThirdParty\sprite-gen`
- 启动：`& E:\ChatGPT_Skills\ThirdParty\Invoke-SpriteGen.ps1 --help`
- Python：`sprite-gen\.venv\Scripts\python.exe`
- 从旧目录迁移了已有源码和 Git 历史，未重新下载。
- 原路径 `C:\Users\ding\Documents\Codex\2026-09-17\i\work\sprite-gen` 保留 Junction，指向新源码位置。
- 虚拟环境使用本机 Codex 提供的 Python 3.12，并复用其 Pillow/NumPy。不是可跨机器复制的便携 Python。
- 旧路径同级的 `sprite-gen-migration-backup` 保留迁移过程中的原剩余文件作备份；完整活动副本在此处。

## RIFE ncnn Vulkan

- 官方项目：https://github.com/nihui/rife-ncnn-vulkan
- 官方 Windows 发行版：20221029。
- 程序及模型：`rife-ncnn-vulkan\rife-ncnn-vulkan-20221029-windows`
- 下载包：`_downloads\rife-ncnn-vulkan-20221029-windows.zip`
- 本地 SHA256：`D8E4D772D26CD8006EF0AD0BC82EB191B53C68677D1AE2F42506D74CBBBEA606`（下载后的本地记录，不是官方签名证明）。
- 默认使用 `rife-v4.6`，也可指定 `rife-anime`。

```powershell
& E:\ChatGPT_Skills\ThirdParty\Invoke-Rife.ps1 -Frame0 C:\frames\01.png -Frame1 C:\frames\02.png -Output C:\frames\01-02-mid.png
```

输入需同尺寸、同尺度、同坐标基准。只生成一张中间帧，不改写输入，不自动对齐人物，不修改原关键帧。当前先用不透明背景验证；不要假定此程序支持保留透明通道。

包装脚本明确拒绝透明输入，避免丢失 alpha；对右侧和底部做边缘补齐到32倍数，推理后裁回原尺寸，原角色坐标不变。本机473×741原图直接推理曾出现条纹损坏，补齐后正常。

本机 Vulkan 自动发现失败，通过 `rife-local.json` 中 NVIDIA ICD 文件解决；该设置只传给子进程，不修改系统环境或注册表。驱动升级后若路径失效，应重新核对该配置。已在 RTX 2060 SUPER 上完成两图中间帧推理。`-Gpu -1` 显式使用 CPU。

宇航员试验：程序运行和尺寸检查通过，但腿部中间姿势有明显重影/变形，动作质量未通过。部署成功不等于插帧质量达标。

4 帧循环转 8 帧时分别处理 1→2、2→3、3→4、4→1，再按原1、插12、原2、插23、原3、插34、原4、插41排列。先核验一对，不自动批量扩大。插帧无法保证修正遮挡、错误步态或原帧漂移。

## Practical-RIFE 4.25

- 官方项目：https://github.com/hzwer/Practical-RIFE
- 源码提交：bbfd2ea90910789a860ea3e2b32a240cd577b75e。
- 目录：`Practical-RIFE`；独立 Python 3.11.17 环境，PyTorch 2.5.1+cpu、torchvision 0.20.1+cpu、numpy 1.23.5、opencv-python 4.10.0.84。
- 官方模型包：`_downloads\RIFEv4.25_0919.zip`，SHA256 `E63D481B7AE5D4A4E6AD7AC5B410FF78F3BF7BE3B51B2E38CA8152747ABDE5B4`。
- 启动：`& E:\ChatGPT_Skills\ThirdParty\Invoke-PracticalRife.ps1 -Frame0 C:\frames\01.png -Frame1 C:\frames\02.png -Output C:\frames\mid.png`
- 包装脚本调用官方模型，避免官方示例脚本固定缩放到448×256。只在右侧/底部补齐64倍数，推理后裁回，拒绝透明输入、覆盖输出或修改输入。
- 模型包的40个 teacher/caltime 训练参数不属于推理网络；过滤这些参数后严格加载全部推理权重。
- 宇航员第1→2帧试验：CPU推理约0.51秒，473×741尺寸和原图哈希验证通过；腿部与靴子依然变形，未达到动作质量要求。

## FFmpeg

- 程序目录：`E:\ChatGPT_Skills\ThirdParty\ffmpeg`。
- 可执行程序：`bin\ffmpeg.exe`、`bin\ffprobe.exe`；已验证版本为 9.0.1。
- 用途：供 `character-animation-pipeline` 及项目动画脚本进行视频处理、帧检查和 PNG 序列预览合成。
- 从 `D:\Tools\ffmpeg` 迁移，用户 PATH 已替换为 `E:\ChatGPT_Skills\ThirdParty\ffmpeg\bin`。现有应用需重启后继承新 PATH。

## COSCLI

- 官方 COSCLI v1.0.9 Windows：`COSCLI/coscli.exe`。
- 来源：https://cosbrowser.cloud.tencent.com/software/coscli/coscli-windows-amd64.exe
- SHA256：`705350f15ba90d9c0043122205b79c938e2993d36610fa82fbc3cc9012108300`。
- 用于 game-build-release 的 COS 上传；通过显式 `-c` 读取工程外加密配置，不依赖 PATH。
- 原 LocalAppData/GameBuildTools/COSCLI 副本保留备用，当前发布脚本使用本目录。二进制不得提交 Git。
