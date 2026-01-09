# -*- coding: utf-8 -*-
"""
登录模块（简化版）
"""
import asyncio
from playwright.async_api import BrowserContext, Page
from utils import logger
import config


class DouYinLogin:
    """抖音登录类"""
    
    def __init__(
        self,
        login_type: str,
        browser_context: BrowserContext,
        context_page: Page,
        cookie_str: str = ""
    ):
        self.login_type = login_type
        self.browser_context = browser_context
        self.context_page = context_page
        self.cookie_str = cookie_str
    
    async def begin(self):
        """开始登录流程"""
        logger.info(f"[DouYinLogin] 开始登录，登录方式: {self.login_type}")
        
        if self.login_type == "qrcode":
            await self.login_by_qrcode()
        elif self.login_type == "cookie":
            await self.login_by_cookies()
        else:
            raise ValueError(f"不支持的登录类型: {self.login_type}")
    
    async def login_by_qrcode(self):
        """二维码登录"""
        logger.info("[DouYinLogin] 请使用抖音APP扫描二维码登录...")
        
        # 等待用户扫码登录
        try:
            # 等待登录成功的标志
            await self.context_page.wait_for_function(
                "() => window.localStorage.getItem('HasUserLogin') === '1'",
                timeout=120000  # 2分钟超时
            )
            logger.info("[DouYinLogin] 二维码登录成功！")
        except Exception as e:
            logger.error(f"[DouYinLogin] 二维码登录失败: {e}")
            raise
    
    async def login_by_cookies(self):
        """Cookie登录"""
        if not self.cookie_str:
            raise ValueError("Cookie登录需要提供cookie_str")
        
        logger.info("[DouYinLogin] 使用Cookie登录...")
        
        # 解析cookie字符串并添加到浏览器
        cookies = []
        for item in self.cookie_str.split(";"):
            item = item.strip()
            if "=" in item:
                name, value = item.split("=", 1)
                cookies.append({
                    "name": name.strip(),
                    "value": value.strip(),
                    "domain": ".douyin.com",
                    "path": "/"
                })
        
        await self.browser_context.add_cookies(cookies)
        await self.context_page.reload()
        
        logger.info("[DouYinLogin] Cookie登录完成")
