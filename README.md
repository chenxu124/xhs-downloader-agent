# XHS Downloader Agent

一个用于配合 [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader) 的自动化脚本：

- 命令行启动
- 自动打开本机 Chrome/Edge（优先复用本机浏览器，不强制下载 Playwright 内核）
- 等待手动登录小红书
- 从账号主页批量提取作品链接
- 仅提交视频作品下载任务到 XHS-Downloader API
- 生成运行日志，便于排查登录态/页面结构问题

## 适用场景

- 你已在本机运行 XHS-Downloader 的 API 模式
- 你希望对某个账号主页进行批量视频下载
- 你需要可观测日志与失败排查信息

## 免责声明

请仅用于你有权下载的内容，并遵守平台规则与当地法律法规。

## 环境要求

- Python 3.12+
- Windows（脚本内置了 Windows 浏览器路径探测）
- 已安装并运行 XHS-Downloader（API 地址默认 `http://127.0.0.1:5556`）

## 安装依赖

```powershell
pip install -r requirements.txt
```

## 先启动 XHS-Downloader API

在 XHS-Downloader 项目目录执行：

```powershell
python main.py api
```

确认接口可访问：

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5556/docs
```

## 运行示例（小样本）

```powershell
python xhs_agent_batch_video.py \
  --profile-url "https://www.xiaohongshu.com/user/profile/你的主页链接" \
  --browser-path "C:/Users/你的用户名/AppData/Local/Google/Chrome/Application/chrome.exe" \
  --login-wait-seconds 60 \
  --max-scrolls 10 \
  --max-notes 10 \
  --request-interval 0.8 \
  --log-file "xhs_agent.log" \
  --snapshot-dir "xhs_agent_debug"
```

## 运行示例（全量）

```powershell
python xhs_agent_batch_video.py \
  --profile-url "https://www.xiaohongshu.com/user/profile/你的主页链接" \
  --browser-path "C:/Users/你的用户名/AppData/Local/Google/Chrome/Application/chrome.exe" \
  --login-wait-seconds 120 \
  --max-scrolls 80 \
  --scroll-pause 1.2 \
  --stable-rounds 5 \
  --request-interval 0.8 \
  --log-file "xhs_agent.log" \
  --snapshot-dir "xhs_agent_debug"
```

## 关键参数

- `--profile-url`：目标账号主页链接（必填）
- `--api-base`：XHS-Downloader API 地址，默认 `http://127.0.0.1:5556`
- `--browser-path`：本机浏览器可执行文件路径
- `--login-wait-seconds`：给手动登录预留时间
- `--max-scrolls`：最大滚动轮次
- `--max-notes`：最多收集多少条作品链接（0 表示不限制）
- `--request-interval`：每次 API 请求间隔
- `--log-file`：运行日志文件
- `--snapshot-dir`：失败时 HTML/截图输出目录

## 输出文件

- `xhs_agent.log`：运行日志
- `xhs_links.txt`：采集到的作品链接
- `xhs_agent_debug/`：失败快照（仅失败时生成）

## 已验证能力

- 小样本（3 条）测试可成功采集并提交视频下载
- 可自动跳过非视频作品
- 能输出主页状态诊断信息（卡片数量、标题、当前 URL）

---

## 🆕 稳定性改进（v1.1）

脚本已优化以下问题：

- ✅ **会话锁清理** - 避免多次运行时的进程冲突
- ✅ **增强错误处理** - 防止浏览器意外关闭导致无日志输出
- ✅ **自动化隐藏标记** - 减少页面检测到自动化工具的概率
- ✅ **持久化会话改进** - 长期会话运行更稳定

### 测试改进效果

```powershell
# 运行脚本并查看详细日志
python xhs_agent_batch_video.py `
  --profile-url "https://..." `
  --max-scrolls 30 `
  --log-file "test.log"

# 查看日志
Get-Content test.log
```

---

## 📦 打包成独立 .exe（开发中）

如无需修改代码，建议打包为 `.exe` 文件，双击即运行：

```powershell
# 1. 安装PyInstaller (如未安装)
pip install pyinstaller

# 2. 生成exe
python build_exe.py

# 3. 输出文件
# dist/xhs_agent.exe  <- 可直接运行
```

**详细说明：** 见 [PACKAGING.md](PACKAGING.md)

### 快速使用

```powershell
# 可交互式运行（推荐）
dist/xhs_agent.exe --profile-url "https://..." --login-wait-seconds 120
```

---

## 常见问题

### Q: 浏览器频繁关闭？
**A:** 已在 v1.1 版本改进会话管理。运行前确保：
- XHS-Downloader API 正在运行
- 网络连接正常
- 查看 `xhs_agent.log` 了解具体错误

### Q: 登录容易被审查？
**A:** 
- 使用长 `--login-wait-seconds`（如 180 秒）让系统有充分时间登录
- 脚本采集时会复用持久化会话，无需重复登录
- 不要在短时间内频繁运行多次，容易触发审查

### Q: 怎样避免触发小红书的反爬虫机制？
**A:**
- 设置合理的 `--request-interval`（建议 0.8~2.0 秒）
- 不要在凌晨 0-2 点高频运行
- 每个账号单次采集间隔不少于 1 小时
