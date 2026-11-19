# QWEN 参考图生成提供方

> 非默认兼容入口（2026-11-03修订）：静态图片生成/编辑默认使用内置 Image 的 `image_gen`。
> 仅用户为当前任务明确选择QWEN/DashScope静态图API时读取并使用本文件；不自动测试、上传或重试。
> 历史提供方登记与已有API Key不改变默认路由。默认QWEN接口只保留给 `character-animation-pipeline` 的动画视频生成。


## 固定公开配置

- 提供方：Alibaba Cloud Model Studio / DashScope
- 提交地址：`https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation`
- 模型：`wan2.6-image`
- 凭据：仅显式外部模式按当前项目登记的本机CSV安全读取，不沿用历史 `QWEN_ANI` 环境变量约定；不得输出/复制/上传凭据文件
- 调用脚本：`scripts/invoke-qwen-reference-image.ps1`

禁止从环境变量读取图片接口凭据。上述旧脚本仍含环境变量调用，仅供历史协议参考，禁止直接执行。显式外部任务须使用项目已批准的凭据读取与队列调用器；未提供合规入口时停止外部调用，不影响内置 Image。

## 请求协议

参考图生成使用 `input.messages[0].content`：其中必须有且只有一个 `text` 对象，
并附带 1–4 个 `image` 对象。脚本把本地参考图编码为 Base64 数据 URI；若输入含
Alpha 通道，只在内存中铺到纯洋红背景，不创建临时参考文件。

固定参数：

- `enable_interleave=false`
- `n=1`
- `prompt_extend=false`
- `watermark=false`
- `size=1K`

使用同步 HTTP 调用。不要发送 `X-DashScope-Async`；部分账号在该模型上不支持异步调用。

## 历史脚本示例（禁止直接执行）

```powershell
& "<Skill目录>\scripts\invoke-qwen-reference-image.ps1" `
  -Prompt "参考图1的画风和视角生成新资产" `
  -ReferenceImagePath "<绝对参考图路径>.png" `
  -OutputPath "<绝对输出路径>.png"
```

可传入多个 `-ReferenceImagePath` 值，最多 4 张。使用 `-ValidateOnly` 只检查凭据、
文件、参数和请求结构，不联网、不生成图片。
