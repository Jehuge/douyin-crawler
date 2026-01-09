# -*- coding: utf-8 -*-
"""
字段定义
"""
from enum import Enum


class SearchChannelType(Enum):
    """搜索频道类型"""
    GENERAL = "aweme_general"  # 综合
    VIDEO = "aweme_video_web"  # 视频
    USER = "aweme_user_web"  # 用户
    LIVE = "aweme_live"  # 直播


class SearchSortType(Enum):
    """搜索排序类型"""
    GENERAL = 0  # 综合排序
    MOST_LIKE = 1  # 最多点赞
    LATEST = 2  # 最新发布


class PublishTimeType(Enum):
    """发布时间类型"""
    UNLIMITED = 0  # 不限
    ONE_DAY = 1  # 一天内
    ONE_WEEK = 7  # 一周内
    SIX_MONTH = 180  # 半年内


class VideoUrlInfo:
    """视频URL信息"""
    def __init__(self, aweme_id: str, url_type: str = "normal"):
        self.aweme_id = aweme_id
        self.url_type = url_type  # normal | modal | short
    
    def __repr__(self):
        return f"VideoUrlInfo(aweme_id={self.aweme_id}, url_type={self.url_type})"


class CreatorUrlInfo:
    """创作者URL信息"""
    def __init__(self, sec_user_id: str):
        self.sec_user_id = sec_user_id
    
    def __repr__(self):
        return f"CreatorUrlInfo(sec_user_id={self.sec_user_id})"
