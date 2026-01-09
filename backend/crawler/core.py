# -*- coding: utf-8 -*-
"""
抖音爬虫核心类 - 包含三种爬取模式
"""
import asyncio
import os
import random
from typing import Dict, List

from playwright.async_api import BrowserType, BrowserContext, Page, Playwright, async_playwright

import config
from database import douyin_store
from utils import logger, parse_video_info_from_url, parse_creator_info_from_url, convert_cookies
from crawler import DouYinClient, DouYinLogin, PublishTimeType, DataFetchError


class DouYinCrawler:
    """抖音爬虫主类"""
    
    def __init__(self):
        self.index_url = "https://www.douyin.com"
        self.browser_context: BrowserContext = None
        self.context_page: Page = None
        self.dy_client: DouYinClient = None
    
    async def start(self):
        """启动爬虫"""
        logger.info("[DouYinCrawler] 启动抖音爬虫...")
        
        async with async_playwright() as playwright:
            # 启动浏览器
            chromium = playwright.chromium
            self.browser_context = await self.launch_browser(
                chromium,
                headless=config.HEADLESS
            )
            
            # 添加反检测脚本
            stealth_js_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'libs',
                'stealth.min.js'
            )
            await self.browser_context.add_init_script(path=stealth_js_path)
            
            # 创建页面
            self.context_page = await self.browser_context.new_page()
            await self.context_page.goto(self.index_url)
            
            # 创建客户端
            self.dy_client = await self.create_douyin_client()
            
            # 检查登录状态
            if not await self.dy_client.pong(browser_context=self.browser_context):
                login_obj = DouYinLogin(
                    login_type=config.LOGIN_TYPE,
                    browser_context=self.browser_context,
                    context_page=self.context_page,
                    cookie_str=config.COOKIES
                )
                await login_obj.begin()
                await self.dy_client.update_cookies(browser_context=self.browser_context)
            
            logger.info(f"[DouYinCrawler] 登录成功！开始执行爬取任务...")
            
            # 使用配置中的值
            crawler_type = config.CRAWLER_TYPE
            logger.info(f"[DouYinCrawler] 当前爬取类型: {crawler_type}")
            
            # 根据配置执行不同的爬取模式
            if crawler_type == "search":
                await self.search()
            elif crawler_type == "detail":
                await self.get_specified_awemes()
            elif crawler_type == "creator":
                await self.get_creators_and_videos()
            else:
                logger.error(f"[DouYinCrawler] 不支持的爬取类型: {crawler_type}")
            
            logger.info("[DouYinCrawler] 爬取任务完成！")
    
    async def search(self):
        """模式1: 关键词搜索"""
        logger.info("[DouYinCrawler] 开始关键词搜索模式...")
        
        dy_limit_count = 10  # 抖音每页固定返回10条
        if config.CRAWLER_MAX_NOTES_COUNT < dy_limit_count:
            config.CRAWLER_MAX_NOTES_COUNT = dy_limit_count
        
        start_page = config.START_PAGE
        
        for keyword in config.KEYWORDS.split(","):
            keyword = keyword.strip()
            logger.info(f"[DouYinCrawler] 当前搜索关键词: {keyword}")
            
            aweme_list: List[str] = []
            page = 0
            dy_search_id = ""
            
            while (page - start_page + 1) * dy_limit_count <= config.CRAWLER_MAX_NOTES_COUNT:
                if page < start_page:
                    logger.info(f"[DouYinCrawler] 跳过第 {page} 页")
                    page += 1
                    continue
                
                try:
                    logger.info(f"[DouYinCrawler] 搜索关键词: {keyword}, 第 {page} 页")
                    posts_res = await self.dy_client.search_info_by_keyword(
                        keyword=keyword,
                        offset=page * dy_limit_count - dy_limit_count,
                        publish_time=PublishTimeType(config.PUBLISH_TIME_TYPE),
                        search_id=dy_search_id
                    )
                    
                    if not posts_res.get("data"):
                        logger.info(f"[DouYinCrawler] 第 {page} 页无数据，结束搜索")
                        break
                
                except DataFetchError:
                    logger.error(f"[DouYinCrawler] 搜索失败: {keyword}")
                    break
                
                page += 1
                
                if "data" not in posts_res:
                    logger.error(f"[DouYinCrawler] 搜索失败，可能账号被风控")
                    break
                
                dy_search_id = posts_res.get("extra", {}).get("logid", "")
                
                # 处理搜索结果
                for post_item in posts_res.get("data", []):
                    try:
                        aweme_info: Dict = (
                            post_item.get("aweme_info") or
                            post_item.get("aweme_mix_info", {}).get("mix_items", [{}])[0]
                        )
                    except (TypeError, IndexError):
                        continue
                    
                    aweme_id = aweme_info.get("aweme_id", "")
                    if aweme_id:
                        aweme_list.append(aweme_id)
                        # 保存视频数据
                        await douyin_store.save_video(aweme_info, keyword=keyword)
                        # 下载媒体文件
                        await self.get_aweme_media(aweme_info)
                
                # 页面间隔
                await asyncio.sleep(config.CRAWLER_MAX_SLEEP_SEC)
                logger.info(f"[DouYinCrawler] 等待 {config.CRAWLER_MAX_SLEEP_SEC} 秒后继续...")
            
            logger.info(f"[DouYinCrawler] 关键词 {keyword} 爬取完成，共 {len(aweme_list)} 个视频")
    
    async def get_specified_awemes(self):
        """模式2: 指定视频ID/URL爬取"""
        logger.info("[DouYinCrawler] 开始指定视频爬取模式...")
        
        aweme_id_list = []
        
        for video_url in config.DY_SPECIFIED_ID_LIST:
            try:
                video_info = parse_video_info_from_url(video_url)
                
                # 处理短链接
                if video_info.url_type == "short":
                    logger.info(f"[DouYinCrawler] 解析短链接: {video_url}")
                    resolved_url = await self.dy_client.resolve_short_url(video_url)
                    
                    if resolved_url:
                        video_info = parse_video_info_from_url(resolved_url)
                        logger.info(f"[DouYinCrawler] 短链接解析成功: {video_info.aweme_id}")
                    else:
                        logger.error(f"[DouYinCrawler] 短链接解析失败: {video_url}")
                        continue
                
                aweme_id_list.append(video_info.aweme_id)
                logger.info(f"[DouYinCrawler] 解析视频ID: {video_info.aweme_id}")
                
            except ValueError as e:
                logger.error(f"[DouYinCrawler] 解析视频URL失败: {e}")
                continue
        
        # 并发获取视频详情
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
        tasks = [
            self.get_aweme_detail(aweme_id=aweme_id, semaphore=semaphore)
            for aweme_id in aweme_id_list
        ]
        aweme_details = await asyncio.gather(*tasks)
        
        # 保存数据
        for aweme_detail in aweme_details:
            if aweme_detail:
                await douyin_store.save_video(aweme_detail)
                await self.get_aweme_media(aweme_detail)
        
        logger.info(f"[DouYinCrawler] 指定视频爬取完成，共 {len(aweme_id_list)} 个视频")
    
    async def get_creators_and_videos(self):
        """模式3: 创作者主页爬取"""
        logger.info("[DouYinCrawler] 开始创作者主页爬取模式...")
        
        for creator_url in config.DY_CREATOR_ID_LIST:
            try:
                creator_info_parsed = parse_creator_info_from_url(creator_url)
                sec_user_id = creator_info_parsed.sec_user_id
                logger.info(f"[DouYinCrawler] 解析创作者ID: {sec_user_id}")
                
            except ValueError as e:
                logger.error(f"[DouYinCrawler] 解析创作者URL失败: {e}")
                continue
            
            # 获取创作者信息
            creator_info: Dict = await self.dy_client.get_user_info(sec_user_id)
            if creator_info:
                await douyin_store.save_creator(sec_user_id, creator_info)
            
            # 获取创作者所有视频
            all_video_list = await self.dy_client.get_all_user_aweme_posts(
                sec_user_id=sec_user_id,
                callback=self.fetch_creator_video_detail
            )
            
            logger.info(f"[DouYinCrawler] 创作者 {sec_user_id} 爬取完成，共 {len(all_video_list)} 个视频")
    
    async def fetch_creator_video_detail(self, video_list: List[Dict]):
        """并发获取创作者视频详情"""
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
        tasks = [
            self.get_aweme_detail(post_item.get("aweme_id"), semaphore)
            for post_item in video_list
        ]
        
        note_details = await asyncio.gather(*tasks)
        
        for aweme_item in note_details:
            if aweme_item:
                await douyin_store.save_video(aweme_item)
                await self.get_aweme_media(aweme_item)
    
    async def get_aweme_detail(self, aweme_id: str, semaphore: asyncio.Semaphore):
        """获取视频详情"""
        async with semaphore:
            try:
                result = await self.dy_client.get_video_by_id(aweme_id)
                await asyncio.sleep(config.CRAWLER_MAX_SLEEP_SEC)
                logger.info(f"[DouYinCrawler] 获取视频详情成功: {aweme_id}")
                return result
            except DataFetchError as ex:
                logger.error(f"[DouYinCrawler] 获取视频详情失败: {ex}")
                return None
            except KeyError as ex:
                logger.error(f"[DouYinCrawler] 视频不存在: {aweme_id}, {ex}")
                return None
    
    async def get_aweme_media(self, aweme_item: Dict):
        """下载视频/图片"""
        if not config.ENABLE_GET_MEDIA:
            return
        
        aweme_id = aweme_item.get("aweme_id", "")
        if not aweme_id:
            return
        
        # 判断是图片还是视频
        images = aweme_item.get("images", [])
        
        if images:
            # 下载图片
            await self.get_aweme_images(aweme_item)
        else:
            # 下载视频
            await self.get_aweme_video(aweme_item)
    
    async def get_aweme_images(self, aweme_item: Dict):
        """下载图片"""
        aweme_id = aweme_item.get("aweme_id", "")
        images = aweme_item.get("images", [])
        
        if not images:
            return
        
        for idx, img in enumerate(images):
            url = img.get("url_list", [""])[0]
            if not url:
                continue
            
            content = await self.dy_client.get_aweme_media(url)
            await asyncio.sleep(random.random())
            
            if content:
                await douyin_store.save_video_file(
                    aweme_id=f"{aweme_id}_{idx}",
                    content=content,
                    file_type="image"
                )
    
    async def get_aweme_video(self, aweme_item: Dict):
        """下载视频"""
        aweme_id = aweme_item.get("aweme_id", "")
        video = aweme_item.get("video", {})
        play_addr = video.get("play_addr", {})
        url = play_addr.get("url_list", [""])[0]
        
        if not url:
            return
        
        content = await self.dy_client.get_aweme_media(url)
        await asyncio.sleep(random.random())
        
        if content:
            await douyin_store.save_video_file(
                aweme_id=aweme_id,
                content=content,
                file_type="video"
            )
    
    async def create_douyin_client(self) -> DouYinClient:
        """创建抖音客户端"""
        cookie_str, cookie_dict = convert_cookies(await self.browser_context.cookies())
        
        douyin_client = DouYinClient(
            timeout=60,
            proxy=None,
            headers={
                "User-Agent": await self.context_page.evaluate("() => navigator.userAgent"),
                "Cookie": cookie_str,
                "Host": "www.douyin.com",
                "Origin": "https://www.douyin.com/",
                "Referer": "https://www.douyin.com/",
                "Content-Type": "application/json;charset=UTF-8",
            },
            playwright_page=self.context_page,
            cookie_dict=cookie_dict
        )
        return douyin_client
    
    async def launch_browser(
        self,
        chromium: BrowserType,
        headless: bool = True
    ) -> BrowserContext:
        """启动浏览器"""
        if config.SAVE_LOGIN_STATE:
            user_data_dir = os.path.join(os.getcwd(), config.USER_DATA_DIR)
            browser_context = await chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                accept_downloads=True,
                headless=headless,
                viewport={"width": 1920, "height": 1080}
            )
            return browser_context
        else:
            browser = await chromium.launch(headless=headless)
            browser_context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            return browser_context
    
    async def close(self):
        """关闭浏览器"""
        if self.browser_context:
            await self.browser_context.close()
            logger.info("[DouYinCrawler] 浏览器已关闭")
