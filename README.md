# CursorUsageTray

Windows **纯 Python** 用量监视器：桌面**置顶悬浮框** + 系统托盘（`pystray`）。读取本机 Cursor 登录态，调用 `GetCurrentPeriodUsage` 显示套餐已用百分比。

## 功能

- **置顶悬浮框**：无边框小徽章，文案为 `Cursor Usage : xx.x%`，默认贴在屏幕右上；可拖动，始终置顶。左键仅拖动，右键打开菜单（刷新 / Dashboard / 退出）
- **穿透模式**：托盘图标右键菜单可开关。开启后鼠标点击会穿透悬浮框，作用于下方窗口；悬浮框略变透明作提示。关闭穿透后可再拖动/右键操作悬浮框
- 托盘图标：**黑底半粗数字**（Segoe UI Semibold）。不足 100 时显示一位小数（如 `12.3`）；满额显示 `100`。颜色按用量从绿渐变到红
- 托盘悬停可看 `已使用 x.x%` 及 Auto/API 等详细文案
- **自动刷新**：周一至周五 8:00–22:00，每 30 分钟（如 8:00、8:30、9:00 … 22:00）；周末和夜间不自动请求。若在该时段内启动，会立刻刷新一次
- 右键菜单或托盘菜单 **「刷新用量」** 随时手动更新（不受时段限制）
- **「打开 Dashboard」** 跳转 Cursor 网页用量页
- Token 来源：`%APPDATA%\Cursor\auth.json`（CLI）或 `%APPDATA%\Cursor\User\globalStorage\state.vscdb`（桌面 Cursor）
- 新版 Cursor 会对 Token 使用 `cursor-safe-storage:v1:` 加密；本工具在 Windows 上通过 DPAPI + AES-GCM 本地解密（与浏览器读密码同源机制，密钥不出本机）

## 运行

1. 确保已在 **Cursor 桌面版登录**（或执行过 `agent login`）。
2. **双击 `run.vbs`**（无 CMD 黑窗口），或在项目目录执行：

```bat
python -m pip install -r requirements.txt
pythonw main.py
```

`run.bat` 会用 `pythonw` 启动，但从资源管理器双击时仍可能短暂出现命令行；日常请用 **`run.vbs`**。

启动后桌面右上会出现置顶悬浮框；托盘图标仍在任务栏右下角（若被折叠，请在「^」隐藏图标里拖到可见区域）。

## 开机自启（可选）

1. `Win + R` → 输入 `shell:startup` → 回车。
2. 为 **`run.vbs`** 创建快捷方式并放入该文件夹（无控制台窗口）。

## 说明

- 使用的是 Cursor 客户端同源内部接口，**非官方公开 API**，更新后可能失效。
- `accessToken` 仅在本机读取，不会上传到其他服务器。
- 若提示登录过期，重新打开 Cursor 或运行 `agent login` 后再刷新。

## 项目结构

| 文件 | 说明 |
|------|------|
| `main.py` | 悬浮框 / 托盘 UI 与刷新逻辑 |
| `float_window.py` | 置顶可拖动悬浮徽章 |
| `tray_icon.py` | 黑底粗体数字图标 |
| `cursor_safe_storage.py` | Windows 下解密 safeStorage |
| `cursor_api.py` | 请求用量并格式化显示 |
| `run.bat` | 一键安装依赖并启动 |
| `run.vbs` | 静默安装依赖并启动（推荐） |
| `run.bat` | 命令行/调试启动 |