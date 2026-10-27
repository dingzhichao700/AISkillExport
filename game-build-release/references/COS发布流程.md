# COS 发布流程

用于已配置的公有读、私有写 COS 桶。沿用用户授权的项目目录，不修改桶权限、不删除历史资源。

工程 `buildRelease.deployment` 配置：

```json
{
  "kind": "cos",
  "bucket": "<桶完整名称>",
  "region": "<地域标识>",
  "projectSubdirectory": "<项目名>",
  "publicRoot": "https://<桶完整名称>.cos.<地域标识>.myqcloud.com/<项目名>/"
}
```

`bootstrapUrl` 等于 publicRoot 加 bootstrap.json；`cdnRoot` 为本项目本地候选资源目录。适配器当前支持 COS 默认 HTTPS 域名，其他域名需先验证适配。

COSCLI 统一位于技能仓库 `ThirdParty/COSCLI`；原始密钥和加密配置保存在用户指定的工程外专用凭证目录，并以服务、账号和用途命名。真实路径只记录在本机环境说明，不写入项目或通用 Skill。凭证不得进入 Git、包体或发布资源。脚本通过 `--coscli` 与 `--cos-config` 显式接收路径，不读取或输出密钥，不将机器路径写入通用实现。不要使用 config show 输出凭证配置。

执行顺序：

1. 按微信流程完成 generate、export，检查同一 requestId 成功。运行 validate_release.py 并归档底座、源码状态、AOT、桥接和包体。
2. `python scripts/publish_cos.py --project <工程> --coscli <程序> --cos-config <配置> --action stage`。只上传候选引用的版本资源及 Bundle；先比较远端 SHA256，相同复用，不同拒绝覆盖；新文件使用禁止覆盖上传，再以匿名 HTTPS 下载比对。
3. 候选完整核验后执行 Invoke-GameBuild.ps1 的 publish-local，并执行 validate_release.py --published。
4. 同样参数运行 `--action activate`。再次核验不可变资源后更新本底座 current，最后合并发布 bootstrap，保留其他底座映射。指针使用禁止缓存策略；不可变资源使用一年缓存。
5. `--action verify` 可只读复查远端完整资源和当前映射。收据存放工程根 build/cos-*.json；包含文件哈希，不包含凭证。

每个项目同时只能有一个发布者。脚本本地锁不能替代跨机器协调。中断后先检查进程、收据和远端，不删除资源；确认无活动发布者才清理遗留锁。切换前后仍须由使用者验证微信真机加载，HTTP 验证不等于真机验收。

入口地址及客户端缓存协议以目标工程的《微信小游戏平台规范》为准；执行前按该协议判断是否需要重建底座。默认 COS 域名不是额外购买的 CDN 加速域名。

维护说明（2026-10-27）：根据用户确认的职责划分补充项目隔离、凭证分离和分层验收要求；本文件维护 COS 操作流程，项目维护运行协议，实例值在工程配置中管理，验收结果在项目构建记录中管理。
