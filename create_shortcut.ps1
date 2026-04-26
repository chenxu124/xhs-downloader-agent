# 创建桌面快捷方式脚本

$exe_path = "C:\Users\ChenXu\xhs-downloader-agent\dist\xhs_agent.exe"
$shortcut_path = [Environment]::GetFolderPath("Desktop") + "\XHS Agent.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcut_path)
$shortcut.TargetPath = $exe_path
$shortcut.WorkingDirectory = "C:\Users\ChenXu\xhs-downloader-agent"
$shortcut.Description = "XHS Downloader Agent - 小红书视频批量下载"
$shortcut.IconLocation = $exe_path + ",0"
$shortcut.Save()

Write-Host "✓ 已创建快捷方式: $shortcut_path"
Write-Host ""
Write-Host "快速开始:"
Write-Host "1. 确保 XHS-Downloader API 已启动"
Write-Host "2. 双击快捷方式或直接运行 exe 文件"
Write-Host "3. 按照提示输入主页链接和参数"
