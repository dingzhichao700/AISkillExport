# QWEN 参考图生成提供方

> 非默认兼容入口（2026-11-03修订）：静态图片生成/编辑默认使用内置 Image 的 `image_gen`。
> 仅用户为当前任务明确选择QWEN/DashScope静态图API时读取并使用本文件；不自动测试、上传或重试。
> 历史提供方登记与已有API Key不改变默认路由。默认QWEN接口只保留给 `character-animation-pipeline` 的动画视频生成。


## 固定公开配置

- 提供方：Alibaba Cloud Model Studio / DashScope
- 提交地址：`https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation`
- 模型：`wan2.6-image`
- API Key 本机凭据文件：`E:/开发凭证（勿删勿上传）/QWEN-apiKey-8436848.csv`；可用 `-CredentialFile` 指定其他本地CSV
- 调用脚本：`scripts/invoke-qwen-reference-image.ps1`

脚本仅在内存中读取CSV中API Key行（首列为apiKey/API Key/key，第二列为密钥），必须唯一且非空；密钥按不透明字符串使用，不限制为旧版十六进制格式。不再读取环境变量。不得输出密钥、复制或上传凭据文件，也不把密钥写入配置、产物或日志；仅向官方API发送Authorization头。

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

## 使用方式

```powershell
& "<Skill目录>\scripts\invoke-qwen-reference-image.ps1" `
  -Prompt "参考图1的画风和视角生成新资产" `
  -ReferenceImagePath "<绝对参考图路径>.png" `
  -OutputPath "<绝对输出路径>.png"
```

可传入多个 `-ReferenceImagePath` 值，最多 4 张。使用 `-ValidateOnly` 只检查凭据、
文件、参数和请求结构，不联网、不生成图片。
