# QWEN 图像生成提供方

> 非默认兼容入口（2026-11-03修订）：静态图片生成/编辑默认使用内置 Image 的 `image_gen`。
> 仅用户为当前任务明确选择QWEN/DashScope静态图API时读取并使用本文件；不自动测试、上传或重试。
> 历史提供方登记与已有API Key不改变默认路由。默认QWEN接口只保留给 `character-animation-pipeline` 的动画视频生成。


## 固定公开配置

- 提供方：Alibaba Cloud Model Studio / DashScope
- 提交地址：`https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis`
- 任务查询地址：`https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}`
- 模型：`qwen-image-plus`
- API Key 本机凭据文件：`E:/开发凭证（勿删勿上传）/QWEN-apiKey-8436848.csv`；可用 `-CredentialFile` 指定其他本地CSV
- 调用脚本：`scripts/invoke-qwen-image.ps1`

脚本仅在内存中读取CSV中API Key行（首列为apiKey/API Key/key，第二列为密钥），必须唯一且非空；密钥按不透明字符串使用，不限制为旧版十六进制格式。不再读取环境变量。不得输出密钥、复制或上传凭据文件，也不把密钥写入配置、产物或日志；仅向官方API发送Authorization头。

## 请求协议

该图像接口使用字符串提示词：

```json
{
  "model": "qwen-image-plus",
  "input": {
    "prompt": "非空字符串"
  },
  "parameters": {
    "size": "1024*1024",
    "n": 1,
    "prompt_extend": false,
    "watermark": false
  }
}
```

禁止把对话接口的 `input.messages` 用于此端点。每次调用都通过固定脚本执行；脚本在
联网前验证 `input.prompt`，异步轮询任务，并只把最终图片写到明确指定的输出路径。

## 使用方式

```powershell
& "<Skill目录>\scripts\invoke-qwen-image.ps1" `
  -Prompt "图像描述" `
  -OutputPath "<绝对输出路径>.png"
```

可用 `-ValidateOnly` 只检查凭据文件可解析、参数和请求结构，不发送网络请求，不生成图片。
