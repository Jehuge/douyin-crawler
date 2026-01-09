# -*- coding: utf-8 -*-
"""
工具辅助函数
"""
import os
import random
import re
import urllib.parse
from typing import Dict
import execjs
from playwright.async_api import Page
from crawler.field import VideoUrlInfo, CreatorUrlInfo


# 加载 douyin.js - 使用绝对路径
_current_dir = os.path.dirname(os.path.abspath(__file__))
_douyin_js_path = os.path.join(os.path.dirname(_current_dir), 'libs', 'douyin.js')
douyin_sign_obj = execjs.compile(open(_douyin_js_path, encoding='utf-8-sig').read())


def get_web_id():
    """
    生成随机webid
    
    Returns:
        str: webid
    """
    def e(t):
        if t is not None:
            return str(t ^ (int(16 * random.random()) >> (t // 4)))
        else:
            return ''.join(
                [str(int(1e7)), '-', str(int(1e3)), '-', str(int(4e3)), '-', str(int(8e3)), '-', str(int(1e11))]
            )
    
    web_id = ''.join(
        e(int(x)) if x in '018' else x for x in e(None)
    )
    return web_id.replace('-', '')[:19]


async def get_a_bogus(url: str, params: str, post_data: dict, user_agent: str, page: Page = None):
    """
    获取 a_bogus 参数
    
    Args:
        url: 请求URL
        params: 请求参数
        post_data: POST数据
        user_agent: User-Agent
        page: Playwright页面对象
    
    Returns:
        str: a_bogus值
    """
    return get_a_bogus_from_js(url, params, user_agent)


def get_a_bogus_from_js(url: str, params: str, user_agent: str):
    """
    通过JS获取 a_bogus 参数
    
    Args:
        url: 请求URL
        params: 请求参数  
        user_agent: User-Agent
    
    Returns:
        str: a_bogus值
    """
    sign_js_name = "sign_datail"
    if "/reply" in url:
        sign_js_name = "sign_reply"
    return douyin_sign_obj.call(sign_js_name, params, user_agent)


def parse_video_info_from_url(url: str) -> VideoUrlInfo:
    """
    从抖音视频URL中解析视频ID
    支持格式:
    1. 普通视频链接: https://www.douyin.com/video/7525082444551310602
    2. 带 modal_id 参数的链接:
       - https://www.douyin.com/user/MS4wLjABAAAATJPY7LAlaa5X-c8uNdWkvz0jUGgpw4eeXIwu_8BhvqE?modal_id=7525082444551310602
       - https://www.douyin.com/root/search/python?modal_id=7471165520058862848
    3. 短链接: https://v.douyin.com/iF12345ABC/ (需要客户端解析)
    4. 纯ID: 7525082444551310602
    
    Args:
        url: 抖音视频链接或ID
    
    Returns:
        VideoUrlInfo: 包含视频ID的对象
    """
    # 如果是纯数字ID，直接返回
    if url.isdigit():
        return VideoUrlInfo(aweme_id=url, url_type="normal")
    
    # 检查是否为短链接
    if "v.douyin.com" in url or (url.startswith("http") and len(url) < 50 and "video" not in url):
        return VideoUrlInfo(aweme_id="", url_type="short")  # 需要客户端解析
    
    # 尝试从URL参数中提取 modal_id
    params = extract_url_params_to_dict(url)
    modal_id = params.get("modal_id")
    if modal_id:
        return VideoUrlInfo(aweme_id=modal_id, url_type="modal")
    
    # 从标准视频URL中提取ID: /video/数字
    video_pattern = r'/video/(\d+)'
    match = re.search(video_pattern, url)
    if match:
        aweme_id = match.group(1)
        return VideoUrlInfo(aweme_id=aweme_id, url_type="normal")
    
    raise ValueError(f"无法解析视频ID: {url}")


def parse_creator_info_from_url(url: str) -> CreatorUrlInfo:
    """
    从抖音创作者主页URL中解析创作者ID (sec_user_id)
    支持格式:
    1. 创作者主页: https://www.douyin.com/user/MS4wLjABAAAATJPY7LAlaa5X-c8uNdWkvz0jUGgpw4eeXIwu_8BhvqE?from_tab_name=main
    2. 纯ID: MS4wLjABAAAATJPY7LAlaa5X-c8uNdWkvz0jUGgpw4eeXIwu_8BhvqE
    
    Args:
        url: 抖音创作者主页链接或 sec_user_id
    
    Returns:
        CreatorUrlInfo: 包含创作者ID的对象
    """
    # 如果是纯ID格式，直接返回
    if url.startswith("MS4wLjABAAAA") or (not url.startswith("http") and "douyin.com" not in url):
        return CreatorUrlInfo(sec_user_id=url)
    
    # 从创作者主页URL中提取 sec_user_id: /user/xxx
    user_pattern = r'/user/([^/?]+)'
    match = re.search(user_pattern, url)
    if match:
        sec_user_id = match.group(1)
        return CreatorUrlInfo(sec_user_id=sec_user_id)
    
    raise ValueError(f"无法解析创作者ID: {url}")


def extract_url_params_to_dict(url: str) -> Dict:
    """
    从URL中提取参数并转换为字典
    
    Args:
        url: URL字符串
    
    Returns:
        Dict: 参数字典
    """
    parsed_url = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed_url.query)
    # 将列表值转换为单个值
    return {k: v[0] if len(v) == 1 else v for k, v in params.items()}


def convert_cookies(cookies: list) -> tuple:
    """
    将cookie列表转换为字符串和字典格式
    
    Args:
        cookies: cookie列表
    
    Returns:
        tuple: (cookie字符串, cookie字典)
    """
    cookie_str = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
    cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    return cookie_str, cookie_dict
