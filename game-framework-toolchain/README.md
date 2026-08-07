# Game Framework Toolchain

自包含的 Game Framework Unity 模板、导出工具与 Codex Skill。普通导出不依赖任何外部 Unity 工程。

## 结构

```text
game-framework-toolchain/
├── SKILL.md
├── AGENTS.md
├── docs/
├── Tools/
└── Templates/GameFramework/
    └── ProjectFiles/        Unity 工程复制源
```

## 验证模板

```powershell
powershell -ExecutionPolicy Bypass -File Tools\Test-GameFrameworkTemplate.ps1
```

## 导出样例工程

```powershell
powershell -ExecutionPolicy Bypass -File Tools\Generate-GameFrameworkProject.ps1 `
  -ProjectName GameFrameworkTest9 `
  -OutputRoot E:\UnityTemplateTest
```

导出过程会在临时 staging 中完成 Unity 编译和 Addressables 现场构建。验证成功后，最终工程的 `Library` 只保留 `com.unity.addressables`，其他可再生缓存由 Unity 在接收方首次打开工程时重新生成。

Unity Hub 打开：`E:\UnityTemplateTest\GameFrameworkTest9\Project`。

完整规则见 `AGENTS.md` 和 `docs/`。
