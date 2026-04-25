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
