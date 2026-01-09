# -*- coding: utf-8 -*-
"""
FastAPI 后端服务
"""
import sys
import os

# 添加backend路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio

# 导入后端模块
from backend.database import db
from backend.utils import logger

app = FastAPI(title="抖音视频爬虫 API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# 爬虫状态
crawler_status = {
    "running": False,
    "current_task": None,
    "progress": 0,
    "total": 0
}


# ==================== 数据模型 ====================
class CrawlerConfig(BaseModel):
    crawler_type: str  # search | detail | creator
    keywords: Optional[str] = None
    video_urls: Optional[List[str]] = None
    creator_urls: Optional[List[str]] = None
    max_count: int = 15
    enable_media: bool = False


class VideoResponse(BaseModel):
    id: int
    aweme_id: str
    title: str
    author_name: str
    like_count: int
    video_url: str
    create_time: int
    keyword: str


class CreatorResponse(BaseModel):
    id: int
    sec_user_id: str
    nickname: str
    follower_count: int
    aweme_count: int


# ==================== API 路由 ====================

@app.get("/")
async def read_root():
    """主页"""
    return FileResponse("frontend/index.html")


@app.get("/api/status")
async def get_status():
    """获取爬虫状态"""
    return crawler_status


@app.post("/api/start")
async def start_crawler(config_data: CrawlerConfig, background_tasks: BackgroundTasks):
    """启动爬虫"""
    if crawler_status["running"]:
        raise HTTPException(status_code=400, detail="爬虫正在运行中")
    
    try:
        # 使用与 core.py 相同的模块路径 'config' 来更新配置
        import config
        import config.settings
        import config.douyin_config
        
        # 更新配置
        config.CRAWLER_TYPE = config_data.crawler_type
        config.settings.CRAWLER_TYPE = config_data.crawler_type
        
        if config_data.crawler_type == "search":
            if config_data.keywords:
                config.KEYWORDS = config_data.keywords
                config.douyin_config.KEYWORDS = config_data.keywords
        elif config_data.crawler_type == "detail":
            if config_data.video_urls:
                config.DY_SPECIFIED_ID_LIST = config_data.video_urls
                config.douyin_config.DY_SPECIFIED_ID_LIST = config_data.video_urls
        elif config_data.crawler_type == "creator":
            if config_data.creator_urls:
                config.DY_CREATOR_ID_LIST = config_data.creator_urls
                config.douyin_config.DY_CREATOR_ID_LIST = config_data.creator_urls
        
        config.CRAWLER_MAX_NOTES_COUNT = config_data.max_count
        config.settings.CRAWLER_MAX_NOTES_COUNT = config_data.max_count
        
        config.ENABLE_GET_MEDIA = config_data.enable_media
        config.settings.ENABLE_GET_MEDIA = config_data.enable_media
        
        logger.info(f"[API] 配置已更新: type={config.CRAWLER_TYPE}, keywords={config.KEYWORDS}, videos={config.DY_SPECIFIED_ID_LIST}")
        
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        # 尝试使用 backend.config 作为备选
        import backend.config as backend_config
        backend_config.CRAWLER_TYPE = config_data.crawler_type
    
    # 后台启动爬虫
    background_tasks.add_task(run_crawler)
    
    crawler_status["running"] = True
    crawler_status["current_task"] = config_data.crawler_type
    
    return {"message": "爬虫已启动", "config": config_data.model_dump()}


@app.post("/api/stop")
async def stop_crawler():
    """停止爬虫"""
    crawler_status["running"] = False
    crawler_status["current_task"] = None
    return {"message": "爬虫已停止"}


@app.get("/api/videos", response_model=List[VideoResponse])
async def get_videos(limit: int = 20, offset: int = 0):
    """获取视频列表"""
    try:
        sql = "SELECT * FROM videos ORDER BY crawl_time DESC LIMIT ? OFFSET ?"
        rows = db.fetchall(sql, (limit, offset))
        
        videos = []
        for row in rows:
            videos.append({
                "id": row[0],
                "aweme_id": row[1],
                "title": row[2] or "",
                "author_name": row[4] or "",
                "like_count": row[8] or 0,
                "video_url": row[6] or "",
                "create_time": row[11] or 0,
                "keyword": row[13] or ""
            })
        
        return videos
    except Exception as e:
        logger.error(f"获取视频列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/videos/count")
async def get_videos_count():
    """获取视频总数"""
    try:
        row = db.fetchone("SELECT COUNT(*) FROM videos")
        return {"count": row[0] if row else 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/creators", response_model=List[CreatorResponse])
async def get_creators(limit: int = 20, offset: int = 0):
    """获取创作者列表"""
    try:
        sql = "SELECT * FROM creators ORDER BY crawl_time DESC LIMIT ? OFFSET ?"
        rows = db.fetchall(sql, (limit, offset))
        
        creators = []
        for row in rows:
            creators.append({
                "id": row[0],
                "sec_user_id": row[1],
                "nickname": row[2] or "",
                "follower_count": row[4] or 0,
                "aweme_count": row[6] or 0
            })
        
        return creators
    except Exception as e:
        logger.error(f"获取创作者列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/videos/clear")
async def clear_videos():
    """清空视频数据"""
    try:
        db.execute("DELETE FROM videos")
        return {"message": "视频数据已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 后台任务 ====================

async def run_crawler():
    """后台运行爬虫"""
    try:
        logger.info("[API] 开始执行爬虫任务...")
        
        # 导入爬虫模块
        from backend.crawler.core import DouYinCrawler
        
        crawler = DouYinCrawler()
        await crawler.start()
        # await crawler.close()  # start方法中使用上下文管理器自动关闭，无需手动调用
        
        logger.info("[API] 爬虫任务完成")
    except Exception as e:
        logger.error(f"[API] 爬虫任务失败: {e}")
    finally:
        crawler_status["running"] = False
        crawler_status["current_task"] = None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
