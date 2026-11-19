# Pinned WeChat SDK background patch

Upstream d288776c50578926c732496882bd6ab6684c778c; MIT license retained. Only three assignments disabling PlayerSettings.runInBackground removed from Editor/WXConvertCore.cs. Package is embedded on WeChat project generation; no native export wrappers, polling or recovery journal.

## 安装与Git边界

Package目录为本机依赖，不进入Git；本目录提交锁定修订、上游文件SHA清单、三行修正后的WXConvertCore.cs.patched和许可证说明。
在独立目录检出 https://github.com/wechat-miniprogram/minigame-tuanjie-transform-sdk.git 的 d288776c50578926c732496882bd6ab6684c778c 修订，再运行：

```powershell
./game-framework-toolchain/Tools/Install-PinnedWeChatSdk.ps1 -UpstreamPackagePath <检出目录>
```

传入包含package.json的SDK包根；脚本验证完整文件清单/哈希、使用仓库补丁并验证候选哈希。也可从已经通过该清单验证的同版Package恢复。未知或被改写的包拒绝安装；不会下载、升级或覆盖现有Package。随后执行Tools/Test-GameFrameworkTemplate.ps1。SDK为MIT，LICENSE随完整依赖安装且须保留。
