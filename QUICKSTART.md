# XHS Agent - 快速使用指南

## 📦 可执行文件 (推荐)

已打包为独立 `.exe` 文件，无需 Python 环境。

**位置：** `dist/xhs_agent.exe` (48.7 MB)

### 最简单的用法

```powershell
# 方式1：直接双击 dist/xhs_agent.exe
# 方式2：命令行运行
.\dist\xhs_agent.exe --profile-url "https://www.xiaohongshu.com/user/profile/..." --help
```

### 完整示例

```powershell
# 小样本（推荐先试）
.\dist\xhs_agent.exe `
  --profile-url "https://www.xiaohongshu.com/user/profile/56187171e4b1cf2cc6dc8b8b" `
  --login-wait-seconds 120 `
  --max-scrolls 20 `
  --request-interval 1.0 `
  --log-file "test.log"

# 全量采集
.\dist\xhs_agent.exe `
  --profile-url "https://www.xiaohongshu.com/user/profile/你的ID" `
  --login-wait-seconds 180 `
  --max-scrolls 80 `
  --scroll-pause 1.2 `
  --stable-rounds 5 `
  --request-interval 0.8
```

---

## 🔧 配置参数

### 必填参数
- `--profile-url` - 小红书账号主页链接（必填）

### 常用参数
| 参数 | 说明 | 默认值 | 例子 |
|------|------|--------|------|
| `--login-wait-seconds` | 登录等待时间（秒）| 0 | 180 |
| `--max-scrolls` | 最大滚动轮数 | 10 | 80 |
| `--request-interval` | API请求间隔（秒）| 0.8 | 1.0 |
| `--log-file` | 日志文件名 | 无 | xhs_agent.log |
| `--browser-path` | 浏览器路径 | 自动查询 | C:/Program Files/Google/Chrome/Application/chrome.exe |

### 高级参数
- `--max-notes` - 最多收集多少条链接（0=不限）
- `--scroll-pause` - 每次滚动暂停时间（秒）
- `--stable-rounds` - 无新链接多少轮后停止滚动
- `--api-base` - XHS-Downloader API地址
- `--user-data-dir` - 浏览器数据目录

---

## 📋 前置要求

1. **XHS-Downloader API 必须在运行**
   ```powershell
   # 在 XHS-Downloader 项目目录执行
   python main.py api
   ```

2. **确认 API 可访问**
   ```powershell
   Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5556/docs
   ```

---

## 📝 输出日志解析

运行后会生成以下文件：

```
xhs_agent.log              # 详细运行日志
xhs_links.txt              # 采集到的所有链接
xhs_agent_debug/           # 失败时的快照（HTML + 截图）
.xhs_browser/              # Chrome会话数据（用于保持登录态）
```

### 查看日志

```powershell
# 查看实时日志
Get-Content xhs_agent.log -Wait

# 查看最后50行
Get-Content xhs_agent.log -Tail 50
```

---

## 🐛 常见问题

### Q: 运行后浏览器弹出后立即关闭？
**A:** 
- 检查 XHS-Downloader API 是否正在运行
- 查看 `xhs_agent.log` 文件的错误信息
- 尝试增加 `--login-wait-seconds` 到 180 秒

### Q: 提示"获取小红书作品数据失败"?
**A:**
- 确认已手动登录且页面完全加载
- 检查网络连接
- 确保主页链接包含 xsec_token 参数

### Q: 怎样避免触发反爬虫?
**A:**
- 增加 `--request-interval` 到 1.5-2.0 秒
- 不要频繁运行（同一账号间隔1小时以上）
- 避免在凌晨 0-2 点运行

---

## 🚀 快速入门（3步）

### 第1步：准备工作
```powershell
# 启动 XHS-Downloader API
cd C:\Users\ChenXu\XHS-Downloader
python main.py api
# 等到看到: INFO: Uvicorn running on http://127.0.0.1:5556
```

### 第2步：获取主页链接
```
打开小红书 → 进入某个账号主页
复制地址栏 URL，应该类似:
https://www.xiaohongshu.com/user/profile/56187171e4b1cf2cc6dc8b8b?...
```

### 第3步：运行采集
```powershell
cd C:\Users\ChenXu\xhs-downloader-agent

# 小样本测试（推荐）
.\dist\xhs_agent.exe `
  --profile-url "你复制的链接" `
  --login-wait-seconds 120 `
  --max-scrolls 10
```

**完成！** 日志会显示采集进度和结果统计。

---

## 📊 运行output示例

```
[SCROLL] 1/10 links=3
[SCROLL] 2/10 links=7
[SCROLL] 3/10 links=12
...
[1/12] https://www.xiaohongshu.com/user/profile/.../...
  -> download submitted
[2/12] https://www.xiaohongshu.com/user/profile/.../...
  -> skip non-video note
...
========== DONE ==========
Total links: 12
Video submitted: 8
Skipped non-video: 4
Failed: 0
```

---

## 💡 优化建议

### 为了最佳体验：
1. 使用 Chrome 而不是 Edge（Playwright 兼容性更好）
2. 关闭 VPN（防止被平台检测）
3. 设置合理的请求间隔（1 秒最安全）
4. 预留充足的登录时间（180 秒）

---

## 📚 更多信息

- [完整参数说明](README.md)
- [打包指南](PACKAGING.md)
- [GitHub 项目](https://github.com/chenxu124/xhs-downloader-agent)

