# QWEN 参考图生成提供方

## 固定公开配置

- 提供方：Alibaba Cloud Model Studio / DashScope
- 提交地址：`https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation`
- 模型：`wan2.6-image`
- API Key 环境变量：`QWEN_ANI`
- 调用脚本：`scripts/invoke-qwen-reference-image.ps1`

环境变量只保存 API Key。不得输出、记录或持久化它的值。

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
