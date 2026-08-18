# QWEN 图像生成提供方

## 固定公开配置

- 提供方：Alibaba Cloud Model Studio / DashScope
- 提交地址：`https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis`
- 任务查询地址：`https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}`
- 模型：`qwen-image-plus`
- API Key 环境变量：`QWEN_ANI`
- 调用脚本：`scripts/invoke-qwen-image.ps1`

环境变量只保存 API Key。不得输出、记录或持久化它的值。

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

可用 `-ValidateOnly` 只检查环境变量存在、参数和请求结构，不发送网络请求，不生成图片。
