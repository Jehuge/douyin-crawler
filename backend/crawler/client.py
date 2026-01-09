# -*- coding: utf-8 -*-
"""
抖音API客户端
"""
import asyncio
import copy
import json
import urllib.parse
from typing import Any, Callable, Dict, Optional, Union

import httpx
from playwright.async_api import BrowserContext, Page

import config
from utils import logger, get_web_id, get_a_bogus, convert_cookies
from crawler.exception import DataFetchError
from crawler.field import SearchChannelType, SearchSortType, PublishTimeType


class DouYinClient:
    """抖音API客户端类"""
    
    def __init__(
        self,
        timeout: int = 60,
        proxy: str = None,
        headers: Dict = None,
        playwright_page: Page = None,
        cookie_dict: Dict = None
    ):
        self.proxy = proxy
        self.timeout = timeout
        self.headers = headers or {}
        self._host = "https://www.douyin.com"
        self.playwright_page = playwright_page
        self.cookie_dict = cookie_dict or {}
    
    async def _process_request_params(
        self,
        uri: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        request_method: str = "GET"
    ):
        """处理请求参数，添加通用参数和签名"""
        if not params:
            return
        
        headers = headers or self.headers
        
        # 获取localStorage，添加重试机制
        local_storage = {}
        max_retries = 3
        for attempt in range(max_retries):
            try:
                local_storage = await self.playwright_page.evaluate("() => window.localStorage")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"获取localStorage失败，重试 {attempt + 1}/{max_retries}: {e}")
                    await asyncio.sleep(1)
                else:
                    logger.error(f"获取localStorage失败，使用空值: {e}")
                    local_storage = {}
        
        # 通用参数
        common_params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "version_code": "190600",
            "version_name": "19.6.0",
            "pc_client_type": "1",
            "cookie_enabled": "true",
            "browser_language": "zh-CN",
            "browser_platform": "MacIntel",
            "browser_name": "Chrome",
            "browser_version": "125.0.0.0",
            "platform": "PC",
            "webid": get_web_id(),
            "msToken": local_storage.get("xmst", ""),
        }
        params.update(common_params)
        query_string = urllib.parse.urlencode(params)
        
        # 生成 a-bogus 签名
        post_data = params if request_method == "POST" else {}
        if "/v1/web/general/search" not in uri:
            try:
                a_bogus = await get_a_bogus(uri, query_string, post_data, headers.get("User-Agent", ""), self.playwright_page)
                params["a_bogus"] = a_bogus
            except Exception as e:
                logger.warning(f"生成a_bogus失败，跳过签名: {e}")
    
    async def request(self, method: str, url: str, **kwargs):
        """发送HTTP请求"""
        async with httpx.AsyncClient(proxy=self.proxy) as client:
            response = await client.request(method, url, timeout=self.timeout, **kwargs)
        
        try:
            if response.text == "" or response.text == "blocked":
                logger.error(f"请求被封禁，响应: {response.text}")
                raise Exception("账号被封禁")
            return response.json()
        except Exception as e:
            raise DataFetchError(f"{e}, {response.text}")
    
    async def get(self, uri: str, params: Optional[Dict] = None, headers: Optional[Dict] = None):
        """GET请求"""
        await self._process_request_params(uri, params, headers)
        headers = headers or self.headers
        return await self.request(method="GET", url=f"{self._host}{uri}", params=params, headers=headers)
    
    async def post(self, uri: str, data: dict, headers: Optional[Dict] = None):
        """POST请求"""
        await self. _process_request_params(uri, data, headers, request_method="POST")
        headers = headers or self.headers
        return await self.request(method="POST", url=f"{self._host}{uri}", data=data, headers=headers)
    
    async def pong(self, browser_context: BrowserContext) -> bool:
        """检查登录状态"""
        try:
            local_storage = await self.playwright_page.evaluate("() => window.localStorage")
            if local_storage.get("HasUserLogin", "") == "1":
                return True
        except Exception as e:
            logger.warning(f"检查localStorage登录状态失败: {e}")
        
        try:
            _, cookie_dict = convert_cookies(await browser_context.cookies())
            return cookie_dict.get("LOGIN_STATUS") == "1"
        except Exception as e:
            logger.error(f"检查Cookie登录状态失败: {e}")
            return False
    
    async def update_cookies(self, browser_context: BrowserContext):
        """更新cookies"""
        cookie_str, cookie_dict = convert_cookies(await browser_context.cookies())
        self.headers["Cookie"] = cookie_str
        self.cookie_dict = cookie_dict
    
    async def search_info_by_keyword(
        self,
        keyword: str,
        offset: int = 0,
        search_channel: SearchChannelType = SearchChannelType.GENERAL,
        sort_type: SearchSortType = SearchSortType.GENERAL,
        publish_time: PublishTimeType = PublishTimeType.UNLIMITED,
        search_id: str = ""
    ):
        """关键词搜索"""
        query_params = {
            'search_channel': search_channel.value,
            'enable_history': '1',
            'keyword': keyword,
            'search_source': 'tab_search',
            'query_correct_type': '1',
            'is_filter_search': '0',
            'offset': offset,
            'count': '15',
            'search_id': search_id,
        }
        
        if sort_type.value != SearchSortType.GENERAL.value or publish_time.value != PublishTimeType.UNLIMITED.value:
            query_params["filter_selected"] = json.dumps({
                "sort_type": str(sort_type.value),
                "publish_time": str(publish_time.value)
            })
            query_params["is_filter_search"] = 1
        
        referer_url = f"https://www.douyin.com/search/{keyword}?type=general"
        headers = copy.copy(self.headers)
        headers["Referer"] = urllib.parse.quote(referer_url, safe=':/')
        
        return await self.get("/aweme/v1/web/general/search/single/", query_params, headers=headers)
    
    async def get_video_by_id(self, aweme_id: str) -> Any:
        """获取视频详情"""
        params = {"aweme_id": aweme_id}
        headers = copy.copy(self.headers)
        if "Origin" in headers:
            del headers["Origin"]
        res = await self.get("/aweme/v1/web/aweme/detail/", params, headers)
        return res.get("aweme_detail", {})
    
    async def get_user_info(self, sec_user_id: str):
        """获取用户信息"""
        uri = "/aweme/v1/web/user/profile/other/"
        params = {
            "sec_user_id": sec_user_id,
            "publish_video_strategy_type": 2,
            "personal_center_strategy": 1,
        }
        return await self.get(uri, params)
    
    async def get_user_aweme_posts(self, sec_user_id: str, max_cursor: str = "") -> Dict:
        """获取用户作品列表"""
        uri = "/aweme/v1/web/aweme/post/"
        params = {
            "sec_user_id": sec_user_id,
            "count": 18,
            "max_cursor": max_cursor,
            "locate_query": "false",
            "publish_video_strategy_type": 2,
        }
        return await self.get(uri, params)
    
    async def get_all_user_aweme_posts(
        self,
        sec_user_id: str,
        callback: Optional[Callable] = None
    ):
        """获取用户所有作品"""
        posts_has_more = 1
        max_cursor = ""
        result = []
        
        while posts_has_more == 1:
            aweme_post_res = await self.get_user_aweme_posts(sec_user_id, max_cursor)
            posts_has_more = aweme_post_res.get("has_more", 0)
            max_cursor = aweme_post_res.get("max_cursor", "")
            aweme_list = aweme_post_res.get("aweme_list", [])
            
            logger.info(f"获取用户 {sec_user_id} 的视频数量: {len(aweme_list)}")
            
            if callback:
                await callback(aweme_list)
            
            result.extend(aweme_list)
            await asyncio.sleep(config.CRAWLER_MAX_SLEEP_SEC)
        
        return result
    
    async def get_aweme_media(self, url: str) -> Union[bytes, None]:
        """下载视频/图片"""
        headers = {
            "User-Agent": self.headers.get("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"),
            "Referer": "https://www.douyin.com/",
        }
        
        async with httpx.AsyncClient(proxy=self.proxy, headers=headers) as client:
            try:
                response = await client.get(url, timeout=self.timeout, follow_redirects=True)
                response.raise_for_status()
                
                if response.reason_phrase != "OK":
                    logger.error(f"下载媒体失败: {url}")
                    return None
                
                return response.content
            except httpx.HTTPError as exc:
                logger.error(f"下载媒体异常: {exc}")
                return None
    
    async def resolve_short_url(self, short_url: str) -> str:
        """解析短链接"""
        async with httpx.AsyncClient(proxy=self.proxy, follow_redirects=False) as client:
            try:
                logger.info(f"正在解析短链接: {short_url}")
                response = await client.get(short_url, timeout=10)
                
                if response.status_code in [301, 302, 303, 307, 308]:
                    redirect_url = response.headers.get("Location", "")
                    logger.info(f"短链接解析成功: {redirect_url}")
                    return redirect_url
                else:
                    logger.warning(f"短链接状态码异常: {response.status_code}")
                    return ""
            except Exception as e:
                logger.error(f"解析短链接失败: {e}")
                return ""
