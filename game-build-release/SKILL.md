---
name: game-build-release
description: Build and release standardized Unity projects through conversation-driven, project-configured workflows. Use for base or content builds, candidate validation, deployment, rollback, and build/release script maintenance. Project generation belongs to game-framework-toolchain; gameplay implementation is outside this skill.
---

# Game Build & Release

服务于遵循 Game Framework 规范的工程，不默认选择任何案例工程。此目录是通用编排脚本和执行规则的权威来源；Unity 内的平台实现随工程版本管理。暂不引入 Jenkins。

## 确认任务

1. 从用户当前及既有明确上下文确认工程和环境，读取工程 AGENTS、构建配置和 Git 状态。目标不明确时询问，不按最近使用目录猜测。
2. 读取 [构建发布规范](references/构建发布规范.md)。首次接入或修改配置时再读 [工程配置](references/工程配置.md)。
3. 当前可执行的平台适配为 WeChat。其他平台先识别已有入口，没有适配时明确说明，不套用微信命令或自动改平台。
4. 微信任务读取 [微信执行流程](references/微信执行流程.md)，运行 `scripts/Invoke-GameBuild.ps1 -ProjectPath <Unity工程绝对路径> -Action inspect`。该操作只读，不创建队列。

| 用户指令 | 默认结果 |
|---|---|
| 构建 | 生成并校验候选产物，不更新指针、不上传 |
| 发布 | 校验已选候选版本，部署并核验远端；缺少候选时说明，不暗中构建另一版本 |
| 构建发布 | 顺序完成构建、候选校验、部署和远端生效核验 |
| 仅内容构建 | 保持底座标识；先检查兼容性，不能支持时说明需要新底座 |
| 回退 | 选择明确且兼容的历史版本，验证完整后切换指针，不重建或删除版本 |

沿用用户已授权范围，不逐步重复确认。维护工具、检查状态不等于授权远端发布。选择内容或底座构建时说明证据，不能只因 DLL 编译成功就判定兼容。目标环境缺失、无法判定兼容或有冲突的发布状态时，完成只读检查后精简询问。

## 执行与核验

- 通用脚本使用显式 ProjectPath，参数来自 `ProjectSettings/FrameworkPlatform.json`；不将个人盘符、域名、AppID 写入通用实现。
- `Invoke-GameBuild.ps1` 提交到已打开的目标 Unity；同一工程只允许一个请求。按返回的 requestId 读取结果，旧结果不能作为本次成功。`-WhatIf` 预检而不提交。
- 长时间构建分次读取结果并更新进度，不修改脚本来重复触发构建。超时不自动重提，不关闭用户启动的 Unity。
- `scripts/validate_release.py --project <路径>` 只读验证候选、Catalog、Bundle 和包内底座标识；通过后才能切换本地指针。发布后加 `--published` 检查本地指针。
- Git Pages 远端发布由当前会话按平台流程执行，脚本不暗中提交推送。检查目标分支、项目相对目录、已暂存和待推送提交，不带入其他项目修改。
- 不自动删除历史资源，不覆盖旧版本；保留各底座的 AOT、桥接与构建记录。归档和回退见规范。
- Skill 自检使用临时夹具及只读案例，不对真实工程提交构建请求或远端变更，除非用户要求。

## 维护与交付

- 工程生成交给 game-framework-toolchain；日常构建不重新导出或复制工程。平台协议变更同时检查生产端与客户端，不自动修改游戏玩法。
- 兼容入口使用 `assets/Build-WeChatHotUpdate.ps1`，只转发到此 Skill。Unity 适配升级单独完成一次编译核验，不在每次构建前同步 Editor 源码。
- 结束时分别报告构建类型、底座/内容版本、产物、本地指针、远端部署和真机验证状态。仅推送成功不能报告 Pages 已生效。
- Skill 保存在检出仓库，通过现有安装脚本创建链接。未经请求不提交工具链 Git，不搭建 Jenkins。
