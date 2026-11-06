# CursorUsageTray

[English](README.md) | [简体中文](README.zh-CN.md)

Windows **纯 Python** 轻量用量监视器：桌面**置顶悬浮框** + **系统托盘**。读取本机 Cursor 登录态，调用内部接口 `GetCurrentPeriodUsage`，显示当前套餐已用百分比。

> 非 Cursor 官方产品。依赖客户端内部接口，Cursor 升级后可能失效。

## 功能

- **置顶悬浮框** — 无边框、始终置顶，默认靠近屏幕右上。文案格式：`Cursor Usage : xx.x%`。左键拖动；右键打开菜单（刷新用量 / 打开 Dashboard / 退出）。
- **穿透模式** — 在**托盘图标**右键菜单中开关。开启后，鼠标点击会穿透悬浮框，作用于下方窗口；悬浮框会略变透明作为提示。关闭穿透后可再拖动或右键操作悬浮框。
- **托盘图标** — 黑底半粗数字（Segoe UI Semibold）。不足 100 显示一位小数（如 `12.3`）；满额显示 `100`。颜色随用量由绿 → 黄 → 红渐变。
- **悬停提示** — 托盘 tip 可查看已用百分比及 Auto / API 等明细（若有）。
- **自动刷新** — 周一至周五 **8:00–22:00**，每 **30 分钟**（整点 / 半点）。周末与夜间不自动请求；若在此时段内启动，会立刻刷新一次。
- **手动刷新** — 悬浮框或托盘菜单中的 **「刷新用量」** 随时可用（不受时段限制）。
- **打开 Dashboard** — 跳转 Cursor 网页用量页。
- **仅本机鉴权** — Token 来自 `%APPDATA%\Cursor\auth.json`（CLI）或 `%APPDATA%\Cursor\User\globalStorage\state.vscdb`（桌面版）。新版 Cursor 可能将 Token 加密为 `cursor-safe-storage:v1:`；本工具在 Windows 上通过 DPAPI + AES-GCM **本地解密**（密钥不出本机）。

## 环境要求

- Windows 10/11
- Python **3.10+**（已在 3.13 验证）
- 已登录 Cursor 桌面版，或已执行 `agent login`

## 快速开始

1. 确保已在 **Cursor 桌面版登录**（或执行过 `agent login`）。
2. **双击 `run.vbs`**（无 CMD 黑窗口），或在项目目录执行：

```bat
python -m pip install -r requirements.txt
pythonw main.py
```

- 日常推荐 **`run.vbs`**（静默安装依赖并以 `pythonw` 启动）。
- **`run.bat`** 同样用 `pythonw` 启动，但从资源管理器双击时可能短暂闪一下控制台。给 `run.bat` 传任意参数可走 bat 自身启动逻辑（例如 `run.bat go`）。

启动后，屏幕右上附近会出现置顶悬浮框；托盘图标在任务栏通知区域（若被折叠，请从「^」溢出区拖出）。

## 开机自启（可选）

1. `Win + R` → 输入 `shell:startup` → 回车。
2. 为 **`run.vbs`** 创建快捷方式并放入该文件夹。

## 操作说明

| 操作 | 位置 |
|------|------|
| 拖动悬浮框 | 左键按住拖动 |
| 悬浮框菜单 | 右键点击悬浮框 |
| 刷新 / Dashboard / 退出 | 悬浮框菜单或托盘菜单 |
| 开关穿透模式 | **托盘**菜单 → **穿透模式** |

## 说明与隐私

- 使用的是 Cursor 客户端同源内部接口，**非官方公开 API**。
- `accessToken` 仅在本机读取，不会上传到其他服务器。
- 若提示登录过期，重新打开 Cursor 或运行 `agent login` 后再刷新。

## 项目结构

| 文件 | 说明 |
|------|------|
| `main.py` | 入口：悬浮框 / 托盘 UI、定时与刷新 |
| `float_window.py` | 置顶可拖动悬浮徽章与穿透模式 |
| `tray_icon.py` | 数字托盘 / 图标绘制 |
| `cursor_api.py` | 请求用量并格式化文案 |
| `cursor_auth.py` | 查找并读取 access token |
| `cursor_safe_storage.py` | Windows 下解密 Cursor safeStorage |
| `requirements.txt` | Python 依赖 |
| `run.vbs` | 静默安装依赖并启动（推荐） |
| `run.bat` | 安装依赖并启动（便于调试） |

## 许可

个人使用与修改均可，不提供任何担保。
