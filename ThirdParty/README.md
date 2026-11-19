# Codex 配套第三方工具

该目录存放第三方程序、模型与独立源码仓库。不要把工具二进制、模型、虚拟环境或嵌套 Git 仓库提交到上级技能仓库。

## Git 同步边界

- 同步：本说明、仓库自有的 `../Tools/Invoke-SpriteGen.ps1` 和 `ThirdParty/Invoke-SpriteGen.ps1` 兼容入口。旧调用路径仍可使用；实现只在 Tools 维护。
- 忽略：ThirdParty 中其余所有程序、第三方源码及嵌套 Git、模型、虚拟环境、Python 运行时、uv、本机配置、凭证、安装包和缓存。新增工具默认忽略，不要用 `git add -f` 绕过。
- Git 检出不会自动安装这些依赖。启动脚本按仓库相对路径定位；换机需另行安装依赖并重建虚拟环境，不直接复制绑定本机解释器的 `.venv`。
- 配置示例和依赖安装说明可以纳入 Git，但不加入实际凭证或机器专用配置；需要新增白名单时按具体文件放行，不放行整个 ThirdParty。

## 共享 Python 与 uv

- `python/cpython-3.11.17-windows-x86_64-none`：现行 character-animation-pipeline 虚拟环境依赖的 Python 3.11.17，必须保留。无版本路径是指向它的本机 Junction。
- `uv`：Python 版本、依赖与虚拟环境管理工具，用户明确保留；可执行程序不进 Git。
- SpriteGen 使用单独的 Python 3.12 环境，具体本机依赖见下节。
- `_downloads`、`_cache`、`_work` 已于 2026-11-18 清理；后续重新生成仍默认忽略。

## SpriteGen v2.2.0

- 源码：`E:\ChatGPT_Skills\ThirdParty\sprite-gen`
- 启动：`& E:\ChatGPT_Skills\Tools\Invoke-SpriteGen.ps1 --help`
- Python：`sprite-gen\.venv\Scripts\python.exe`
- 从旧目录迁移了已有源码和 Git 历史，未重新下载。
- 原路径 `C:\Users\ding\Documents\Codex\2026-09-17\i\work\sprite-gen` 保留 Junction，指向新源码位置。
- 虚拟环境使用本机 Codex 提供的 Python 3.12，并复用其 Pillow/NumPy。不是可跨机器复制的便携 Python。
- 旧路径同级的 `sprite-gen-migration-backup` 保留迁移过程中的原剩余文件作备份；完整活动副本在此处。

## RIFE 插帧工具（已退役）

2026-11-18 按用户要求移除 RIFE ncnn Vulkan、Practical-RIFE 的程序、模型、专用虚拟环境、启动脚本及本机配置。此前宇航员插帧试验有重影、变形，未通过动作质量验收；核查现行 Skill 未发现 RIFE 调用。安装包与安装缓存已先行清理。

保留共享 Python 3.11：现行 character-animation-pipeline 的虚拟环境仍依赖 ThirdParty/python/cpython-3.11.17-windows-x86_64-none。SpriteGen、uv 和其他工具保留。

## FFmpeg

- 程序目录：`E:\ChatGPT_Skills\ThirdParty\ffmpeg`。
- 可执行程序：`bin\ffmpeg.exe`、`bin\ffprobe.exe`；已验证版本为 9.0.1。
- 用途：供 `character-animation-pipeline` 及项目动画脚本进行视频处理、帧检查和 PNG 序列预览合成。
- 从 `D:\Tools\ffmpeg` 迁移，用户 PATH 已替换为 `E:\ChatGPT_Skills\ThirdParty\ffmpeg\bin`。现有应用需重启后继承新 PATH。

## PythonValidation

- 目录：`PythonValidation`；PyYAML 6.0.3，供skill-creator官方`quick_validate.py`解析Skill前置配置。
- 校验进程通过`PYTHONPATH`显式引用，不修改游戏依赖或全局PATH；第三方包不提交Git。

## COSCLI

- 官方 COSCLI v1.0.9 Windows：`COSCLI/coscli.exe`。
- 来源：https://cosbrowser.cloud.tencent.com/software/coscli/coscli-windows-amd64.exe
- SHA256：`705350f15ba90d9c0043122205b79c938e2993d36610fa82fbc3cc9012108300`。
- 用于 game-build-release 的 COS 上传；通过显式 `-c` 读取工程外加密配置，不依赖 PATH。
- 原 LocalAppData/GameBuildTools/COSCLI 副本保留备用，当前发布脚本使用本目录。二进制不得提交 Git。

## .NET 8 portable runtime

- 目录：`dotnet/8.0.34/win-x64`；仅运行时，不安装系统服务、不修改全局PATH。
- 来源：微软官方.NET 8发布元数据与Runtime win-x64 ZIP，原下载包为`_downloads/dotnet-runtime-8.0.34-win-x64.zip`（2026-11-18 已清理安装包，运行时保留），已按官方元数据SHA512核验。
- 用途：框架工具链Luban JSON/bin验证；命令进程显式将此目录加入自身PATH即可，不将机器路径写入导出工程。
- 官方元数据：`https://dotnetcli.blob.core.windows.net/dotnet/release-metadata/8.0/releases.json`。ZIP SHA512：`d86d165a29dcdb71df23dd150a3fc5db6386fa55da5cb18c0c22889a0dab5071a3a2d852572e6cebfecf12b489870ac76243ae35665a746ed5b1011e7c68979d`；二进制不提交Git。
