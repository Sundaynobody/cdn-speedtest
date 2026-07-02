# CDNSpeedTest v4.3.1

## 变更清单

### 1. 下载引擎重构：Range 分段并行
- **策略**：6 个 worker 各下载文件的 1/6（HTTP `Range: bytes=start-end`）
- **效果**：`total_bytes == content_length`，进度 / 已下载 / 速度三方显示天然一致
- **降级**：不支持 Range 或文件 < 10MB 时自动回退单连接

### 2. 默认测试节点更新
| 节点 | URL | 大小 | Range |
|------|-----|------|-------|
| Europe (Tele2 50MB) | `http://speedtest.tele2.net/50MB.zip` | 50 MB | ✓ |
| Europe (Tele2 100MB) | `http://speedtest.tele2.net/100MB.zip` | 100 MB | ✓ |
| Asia (Linode SG 100MB) | `http://speedtest.singapore.linode.com/100MB-singapore.bin` | 100 MB | ✓ |
| US East (Linode NJ 100MB) | `http://speedtest.newark.linode.com/100MB-newark.bin` | 100 MB | ✓ |
| Europe (Linode DE 100MB) | `http://speedtest.frankfurt.linode.com/100MB-frankfurt.bin` | 100 MB | ✓ |

### 3. Windows 7 兼容
- **编译器**：Python 3.8.10（最后支持 Win7 的版本）
- **TLS 1.2**：`constants.py` 主动配置 SCHANNEL 兼容层
- **DPI**：`GetDpiForMonitor` 已有 try/except 降级至 96 DPI
- **PowerShell**：Win7 PSv2 不支持 `Get-NetRoute/NetAdapter`，已有 try/except 降级至 netsh

### 4. IP 地址实时刷新
- 新增 `_ip_timer` 定时器，每 5 分钟重新请求 IP 定位 API
- 刷新前清除缓存时间戳，确保每次获取最新数据

### 5. 报告导出路径
- 自动报告从 `%LOCALAPPDATA%\CDNSpeedTest\` 改为当前目录 `os.getcwd()`

### 6. 构建
- 双架构编译（Python 3.8.10）
- x86_64: `CDNSpeedTest_x86_64.exe`（~13 MB）
- x86: `CDNSpeedTest_x86.exe`（~10 MB）
- ARM64 需 CI 构建

### 7. 代码巡查修复
| 文件 | 问题 | 修复 |
|------|------|------|
| `constants.py` | VERSION = "4.3.0" | → "4.3.1" |
| `network.py` | 方法内重复 `import glob` | 移除 |
| `build.py` | Python 3.8 未在搜索范围 | range 扩展至 3.8 |
| `ip_location.py` | 重复 `_show_ip_info` 方法 | 合并 |
