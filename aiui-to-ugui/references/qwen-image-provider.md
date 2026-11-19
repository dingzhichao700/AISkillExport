# QWEN 图像生成提供方

> 非默认兼容入口（2026-11-03修订）：静态图片生成/编辑默认使用内置 Image 的 `image_gen`。
> 仅用户为当前任务明确选择QWEN/DashScope静态图API时读取并使用本文件；不自动测试、上传或重试。
> 历史提供方登记与已有API Key不改变默认路由。默认QWEN接口只保留给 `character-animation-pipeline` 的动画视频生成。


## 固定公开配置

- 提供方：Alibaba Cloud Model Studio / DashScope
- 提交地址：`https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis`
- 任务查询地址：`https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}`
- 模型：`qwen-image-plus`
- 凭据：仅显式外部模式按当前项目登记的本机CSV安全读取，不沿用历史 `QWEN_ANI` 环境变量约定；不得输出/复制/上传凭据文件
- 调用脚本：`scripts/invoke-qwen-image.ps1`

禁止从环境变量读取图片接口凭据。上述旧脚本仍含环境变量调用，仅供历史协议参考，禁止直接执行。显式外部任务须使用项目已批准的凭据读取与队列调用器；未提供合规入口时停止外部调用，不影响内置 Image。

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

## 历史脚本示例（禁止直接执行）

```powershell
& "<Skill目录>\scripts\invoke-qwen-image.ps1" `
  -Prompt "图像描述" `
  -OutputPath "<绝对输出路径>.png"
```

下列旧脚本参数示例不再是可执行入口；仅保留协议历史参考。不得运行旧 ValidateOnly 作为内置 Image 的前置条件。
