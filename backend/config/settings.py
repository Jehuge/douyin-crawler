# -*- coding: utf-8 -*-
"""
抖音爬虫主配置文件
"""

# ==================== 基础配置 ====================
PLATFORM = "douyin"
LOGIN_TYPE = "qrcode"  # qrcode | cookie
COOKIES = ""  # Cookie 登录时填写
CRAWLER_TYPE = "search"  # search | detail | creator

# ==================== 浏览器配置 ====================
# 是否启用无头模式（不显示浏览器窗口）
HEADLESS = False

# 是否保存登录状态
SAVE_LOGIN_STATE = True

# 用户数据目录（用于保存登录态）
USER_DATA_DIR = "browser_data/douyin"

# ==================== CDP 模式配置 ====================
# 是否启用 CDP 模式（使用本地 Chrome/Edge）
ENABLE_CDP_MODE = True

# CDP 调试端口
CDP_DEBUG_PORT = 9222

# 自定义浏览器路径（为空则自动检测）
# Windows: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
# macOS: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CUSTOM_BROWSER_PATH = ""

# CDP 模式下是否启用无头模式
CDP_HEADLESS = False

# 浏览器启动超时时间（秒）
BROWSER_LAUNCH_TIMEOUT = 60

# 是否自动关闭浏览器
AUTO_CLOSE_BROWSER = True

# ==================== 爬取控制 ====================
# 开始页数
START_PAGE = 1

# 最大爬取视频数量
CRAWLER_MAX_NOTES_COUNT = 15

# 最大并发数
MAX_CONCURRENCY_NUM = 1

# 爬取间隔时间（秒）
CRAWLER_MAX_SLEEP_SEC = 2

# ==================== 功能开关 ====================
# 是否下载媒体文件（视频/图片）
ENABLE_GET_MEDIA = False

# 是否启用 IP 代理
ENABLE_IP_PROXY = False

# 代理 IP 池数量
IP_PROXY_POOL_COUNT = 2

# 代理 IP 提供商
# kuaidaili | wandouhttp
IP_PROXY_PROVIDER_NAME = "kuaidaili"

# ==================== 数据存储 ====================
# 数据库文件路径
DATABASE_PATH = "data/douyin.db"

# 视频保存目录
VIDEO_SAVE_DIR = "data/videos"

# 图片保存目录
IMAGE_SAVE_DIR = "data/images"
