# -*- coding: utf-8 -*-
"""
抖音平台特定配置
"""

# ==================== 搜索配置 ====================
# 搜索关键词（多个关键词用逗号分隔）
KEYWORDS = "编程,Python,AI"

# 发布时间类型
# 0: 不限, 1: 一天内, 7: 一周内, 182: 半年内
PUBLISH_TIME_TYPE = 0

# ==================== 指定视频配置 ====================
# 支持格式:
# 1. 完整视频URL: "https://www.douyin.com/video/7525538910311632128"
# 2. 带modal_id的URL: "https://www.douyin.com/user/xxx?modal_id=7525538910311632128"
# 3. 搜索页带modal_id: "https://www.douyin.com/root/search/python?modal_id=7525538910311632128"
# 4. 短链接: "https://v.douyin.com/drIPtQ_WPWY/"
# 5. 纯视频ID: "7280854932641664319"
DY_SPECIFIED_ID_LIST = [
    "https://www.douyin.com/video/7525538910311632128",
    # 添加更多视频URL或ID...
]

# ==================== 创作者配置 ====================
# 支持格式:
# 1. 完整创作者主页URL: "https://www.douyin.com/user/MS4wLjABAAAATJPY7LAlaa5X-c8uNdWkvz0jUGgpw4eeXIwu_8BhvqE"
# 2. sec_user_id: "MS4wLjABAAAATJPY7LAlaa5X-c8uNdWkvz0jUGgpw4eeXIwu_8BhvqE"
DY_CREATOR_ID_LIST = [
    "https://www.douyin.com/user/MS4wLjABAAAATJPY7LAlaa5X-c8uNdWkvz0jUGgpw4eeXIwu_8BhvqE",
    # 添加更多创作者URL或ID...
]
