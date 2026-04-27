# Changelog

## [0.1.1] - 2026-04-27

### Changed
- 增强反爬措施：客户端初始化时主动补充 buvid3/buvid4/b_lsid/b_nut/_uuid 追踪 Cookie，降低 412 风控触发概率
- 会话预热由被动（遇到 412 才触发）改为主动（客户端创建时立即执行）

## [0.1.0] - 2026-04-20

### Added
- 初始版本，基于 Python 3.11 + PySide6 + requests
- 通过 UID 查询 Bilibili 用户空间动态与评论区发言
- 自动提取 Cookie 中的 SESSDATA
- 后台线程抓取（QThread），避免界面卡死
- 结果表格展示，支持点击表头排序
- 导出为 CSV / JSON
- 基础反爬策略：随机 User-Agent + 随机请求间隔
- 完整错误处理：网络超时、UID 无效、Cookie 无效、风控拦截（412）
- 本地日志记录：logs/bili_viewer.log
