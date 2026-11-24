# DSH 内网桌面 · Windows 7 SP1 x64

这是 DeepSeek Harness 0.2.2-rc.5 的社区 Win7 适配与内网部署源码。可以直接浏览、下载及修改桌面、模型接入、工具调用、兼容层和安装程序的实现。克隆本仓库即可得到展开的 DSH 源码，无须再初始化子模块。

| 要审查的功能 | 源码位置 |
| --- | --- |
| Electron 桌面、桌面宿主、模型对话和工具 | [apps](dsh-win7/deepseek-harness/apps) 和 [packages](dsh-win7/deepseek-harness/packages) |
| Win7 原生兼容层、移植补丁、完整上游打包过程 | [shim](dsh-win7/shim)、[win7-fixes](dsh-win7/win7-fixes)、[移植文档](dsh-win7/docs) |
| 使用统计、软件更新和请求目标的改动 | [TypeScript 源码改动生成器](tools/apply-source.py) 和 [发布文件改动生成器](intranet/templates/tools/harden-app.py.in) |
| 系统级出站规则 | [Windows Filtering Platform 的 C 实现](intranet/templates/tools/network-policy.c.in) |
| 部署、模型配置和验收 | [离线安装与验收工具](intranet/templates) |
| Word、PowerPoint、Excel 和 PDF 生成 | [文档生成器](intranet/templates/tools/make-documents.py) 和 [本地 MCP 工具](intranet/templates/tools/office-tool.py) |
| 手动打开虚拟机、保存修改、交换文件 | [桌面播放器启动源码](player) |

### 构建及审查

在 Windows 10/11 x64 构建机准备 Python 3.11 或更新版本、Node.js 24、pnpm 11.28.5、Visual Studio C++ Build Tools 及 Windows SDK。目标机为 Windows 7 SP1 x64。以下 PowerShell 示例使用文档保留地址，部署时填入本单位的模型 IPv4、端口和模型名。

```powershell
python tools/configure.py --ip 192.0.2.10 --port 8080 --model example-model
.\tools\build-native.cmd
python tools/apply-source.py
git diff -- dsh-win7/deepseek-harness
cd dsh-win7/deepseek-harness
pnpm install --frozen-lockfile --ignore-scripts
pnpm run build:lib
pnpm run build:web
```

离线交付附带锁定版本的 Windows x64 依赖缓存。解压后，将安装命令替换成下面这一行。其中两个目录都应使用绝对路径。

```powershell
pnpm install --offline --frozen-lockfile --ignore-scripts --store-dir D:\build-deps\pnpm-store --config.cache-dir=D:\build-deps\pnpm-cache
```

上游的 Win7 Electron、原生插件和系统运行时有各自的构建步骤。使用 Win7 桌面时请按 [Win7 移植项目](dsh-win7/README.md) 的构建及适配说明准备这些组件。仅运行前端编译命令不能生成完整的 Win7 安装包。

### 复核当前发布文件

内网交付版采用锁定的上游桌面文件，通过可读脚本改写应用资源及其完整性摘要。将上游未修改的桌面解包到单独目录，使其直接包含 `DeepSeek Harness.exe` 和 `resources/app.asar`。从已交付的离线安装包准备 `office` 和 `payload` 两个子目录。在仓库根目录运行以下命令。需要 7-Zip 的 `7z.exe` 和 `7z.sfx`。

```powershell
python tools/assemble.py --original D:\upstream-desktop --media D:\offline-media
```

程序先检查上游主程序、ASAR 和依赖介质的摘要，再生成 `out/kit`。如果只想审查网络策略，可以从源码模板检查放行目的地，并在已部署的 Win7 中运行 `05-check-model.cmd` 执行对话及文件读写测试。整机模式作用于所有用户，专用账户模式作用于本机标准账户 DSHWork；本地回环和系统获取 DHCP 地址所需流量有单独规则。

### 来源与许可证

上游版本、提交及导入范围见 [sources.lock.json](sources.lock.json)。DSH 主项目与 Win7 移植的许可证分别保留在 [主项目 LICENSE](dsh-win7/deepseek-harness/LICENSE) 和 [移植项目 LICENSE](dsh-win7/LICENSE)。Electron、Chromium、LibreOffice、Python、Node.js 及其他依赖保留各自许可证。Windows 7、微软系统更新和 Visual C++ 运行库使用微软发布的文件，系统授权由部署单位提供。

交付版由上游未签名的 Windows 桌面发行物制作。源码、锁定版本、实际发布的应用代码及验收记录可用于独立检查。完整 Electron、Chromium 和所有第三方原生组件从源码编译至逐字节相同的 Windows 安装包，尚未完成验证。
