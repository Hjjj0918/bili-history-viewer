# BiliViewer

一个基于 Python + PySide6 的桌面工具，用于通过 Bilibili 用户 UID 查询其历史发言（空间动态 + 评论区筛选），并支持结果导出。

## 功能特性

- 输入目标 UID 查询发言记录
- 输入登录态 Cookie（支持仅 SESSDATA 或整串 Cookie 自动提取）
- 后台线程抓取（QThread），避免界面卡死
- 表格展示结果，支持点击表头排序
- 导出为 CSV / JSON
- 基础反爬策略：随机 User-Agent + 随机请求间隔
- 完整错误处理：网络超时、UID 无效、Cookie 无效、风控拦截（412）等
- 本地日志记录：请求 URL、状态码、异常堆栈

## 技术栈

- Python 3.11+
- PySide6
- requests

## 项目结构

```text
BiliViewer/
├─ main.py                       # 程序入口
├─ requirements.txt              # 依赖列表
├─ .gitignore
├─ logs/                         # 运行后自动创建
│  └─ bili_viewer.log
└─ bili_viewer/
	├─ bilibili_client.py         # B站接口请求与数据抓取逻辑
	├─ controller.py              # 控制器：连接界面与业务
	├─ view.py                    # 主界面（PySide6）
	├─ worker.py                  # 后台抓取线程
	├─ models.py                  # 数据模型与导出
	└─ logging_utils.py           # 日志初始化
```

## 安装与运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动程序

```bash
python main.py
```

## 使用说明

1. 在界面中输入目标 UID
2. 输入自己的 SESSDATA（或整串 Cookie）
3. 点击“开始查询”
4. 查询完成后可点击“导出 CSV”或“导出 JSON”

## 如何获取 SESSDATA

1. 浏览器登录 Bilibili
2. 按 F12 打开开发者工具
3. 进入 Application（或 存储） -> Cookies -> https://www.bilibili.com
4. 找到名为 SESSDATA 的项并复制其值

建议：

- 最稳妥是只粘贴 SESSDATA 的值本体
- 也可粘贴整串 Cookie，程序会自动提取 SESSDATA
- 不要粘贴中文说明、全角符号、引号或换行

## 日志与排障

程序启动后会自动创建日志文件：

- logs/bili_viewer.log

日志包含：

- 请求 URL
- HTTP 状态码
- 异常堆栈信息

可通过日志快速定位问题，例如：

- 412：风控拦截
- -101：Cookie 无效
- latin-1 编码异常：输入了非 ASCII 的 Cookie 内容

## 常见问题

### 1) 点击查询后无反应

- 确认 UID 为纯数字
- 确认 SESSDATA 不为空
- 查看 logs/bili_viewer.log 是否有异常堆栈

### 2) 报错“接口返回异常状态码：412”

- 这是 B 站风控拦截
- 更换最新 SESSDATA 后重试
- 尽量在常用网络环境下查询，避免频繁请求

### 3) 报错“latin-1 codec can't encode characters ...”

- 输入的 Cookie 中包含中文或特殊字符
- 只粘贴浏览器中的原始 Cookie 值

## 说明与限制

- B 站未公开“按 UID 全站检索全部历史评论”的官方接口。
- 本工具采用“空间动态 + 投稿视频评论区按 UID 筛选”的方式进行近似检索。
- 结果并不保证覆盖该用户在全站所有发言。

## 免责声明

- 本项目仅用于学习与技术研究。
- 请遵守 Bilibili 平台规则及相关法律法规，勿用于任何违规用途。
