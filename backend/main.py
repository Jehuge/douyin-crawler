# -*- coding: utf-8 -*-
"""
抖音视频爬虫 - 主程序入口
"""
import asyncio
import argparse
import sys

from crawler.core import DouYinCrawler
from database import db
from utils import logger
import config


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="抖音视频爬虫")
    
    parser.add_argument(
        "--type",
        type=str,
        choices=["search", "detail", "creator"],
        help="爬取类型: search(关键词搜索) | detail(指定视频) | creator(创作者主页)"
    )
    
    parser.add_argument(
        "--keywords",
        type=str,
        help="搜索关键词，多个关键词用逗号分隔"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="是否启用无头模式（不显示浏览器窗口）"
    )
    
    return parser.parse_args()


async def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 应用命令行参数
    if args.type:
        config.CRAWLER_TYPE = args.type
    
    if args.keywords:
        config.KEYWORDS = args.keywords
    
    if args.headless:
        config.HEADLESS = True
    
    # 打印配置信息
    logger.info("=" * 60)
    logger.info("抖音视频爬虫启动")
    logger.info("=" * 60)
    logger.info(f"爬取模式: {config.CRAWLER_TYPE}")
    
    if config.CRAWLER_TYPE == "search":
        logger.info(f"搜索关键词: {config.KEYWORDS}")
    elif config.CRAWLER_TYPE == "detail":
        logger.info(f"指定视频数量: {len(config.DY_SPECIFIED_ID_LIST)}")
    elif config.CRAWLER_TYPE == "creator":
        logger.info(f"指定创作者数量: {len(config.DY_CREATOR_ID_LIST)}")
    
    logger.info(f"无头模式: {config.HEADLESS}")
    logger.info(f"下载媒体: {config.ENABLE_GET_MEDIA}")
    logger.info(f"数据库: {config.DATABASE_PATH}")
    logger.info("=" * 60)
    
    # 创建爬虫实例
    crawler = DouYinCrawler()
    
    try:
        # 启动爬虫
        await crawler.start()
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"爬虫运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭浏览器和数据库
        await crawler.close()
        db.close()
        logger.info("程序结束")


if __name__ == "__main__":
    # Windows系统需要设置事件循环策略
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行主程序
    asyncio.run(main())
