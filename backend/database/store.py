# -*- coding: utf-8 -*-
"""
数据存储逻辑
"""
import os
import asyncio
from datetime import datetime
from typing import Dict, List
from .models import db
import config


class DouyinStore:
    """抖音数据存储类"""
    
    @staticmethod
    async def save_video(aweme_item: Dict, keyword: str = "") -> bool:
        """
        保存视频数据
        
        Args:
            aweme_item: 抖音视频信息字典
            keyword: 搜索关键词
        
        Returns:
            bool: 是否保存成功
        """
        try:
            aweme_id = aweme_item.get("aweme_id", "")
            if not aweme_id:
                return False
            
            # 检查是否已存在
            existing = db.fetchone("SELECT id FROM videos WHERE aweme_id = ?", (aweme_id,))
            
            # 提取视频信息
            author_info = aweme_item.get("author", {})
            statistics = aweme_item.get("statistics", {})
            
            video_data = {
                "aweme_id": aweme_id,
                "title": aweme_item.get("desc", "")[:200],  # 标题截取前200字符
                "desc": aweme_item.get("desc", ""),
                "author_name": author_info.get("nickname", ""),
                "author_id": author_info.get("sec_uid", ""),
                "video_url": DouyinStore._extract_video_download_url(aweme_item),
                "cover_url": aweme_item.get("video", {}).get("cover", {}).get("url_list", [""])[0],
                "like_count": statistics.get("digg_count", 0),
                "comment_count": statistics.get("comment_count", 0),
                "share_count": statistics.get("share_count", 0),
                "create_time": aweme_item.get("create_time", 0),
                "keyword": keyword,
            }
            
            if existing:
                # 更新
                sql = '''
                    UPDATE videos SET 
                        title=?, desc=?, author_name=?, author_id=?,
                        video_url=?, cover_url=?, like_count=?, comment_count=?,
                        share_count=?, create_time=?, keyword=?
                    WHERE aweme_id=?
                '''
                params = (
                    video_data["title"], video_data["desc"], video_data["author_name"],
                    video_data["author_id"], video_data["video_url"], video_data["cover_url"],
                    video_data["like_count"], video_data["comment_count"], video_data["share_count"],
                    video_data["create_time"], video_data["keyword"], aweme_id
                )
            else:
                # 插入
                sql = '''
                    INSERT INTO videos (
                        aweme_id, title, desc, author_name, author_id,
                        video_url, cover_url, like_count, comment_count,
                        share_count, create_time, keyword
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''
                params = (
                    video_data["aweme_id"], video_data["title"], video_data["desc"],
                    video_data["author_name"], video_data["author_id"], video_data["video_url"],
                    video_data["cover_url"], video_data["like_count"], video_data["comment_count"],
                    video_data["share_count"], video_data["create_time"], video_data["keyword"]
                )
            
            db.execute(sql, params)
            print(f"[DouyinStore] Saved video: {aweme_id} - {video_data['title'][:50]}")
            return True
            
        except Exception as e:
            print(f"[DouyinStore] Error saving video: {e}")
            return False
    
    @staticmethod
    async def save_creator(sec_user_id: str, creator_info: Dict) -> bool:
        """
        保存创作者信息
        
        Args:
            sec_user_id: 创作者ID
            creator_info: 创作者信息字典
        
        Returns:
            bool: 是否保存成功
        """
        try:
            if not sec_user_id:
                return False
            
            # 检查是否已存在
            existing = db.fetchone("SELECT id FROM creators WHERE sec_user_id = ?", (sec_user_id,))
            
            user = creator_info.get("user", {})
            
            creator_data = {
                "sec_user_id": sec_user_id,
                "nickname": user.get("nickname", ""),
                "signature": user.get("signature", ""),
                "avatar_url": user.get("avatar_larger", {}).get("url_list", [""])[0],
                "follower_count": user.get("follower_count", 0),
                "following_count": user.get("following_count", 0),
                "aweme_count": user.get("aweme_count", 0),
                "total_favorited": user.get("total_favorited", 0),
            }
            
            if existing:
                # 更新
                sql = '''
                    UPDATE creators SET
                        nickname=?, signature=?, avatar_url=?,
                        follower_count=?, following_count=?,
                        aweme_count=?, total_favorited=?
                    WHERE sec_user_id=?
                '''
                params = (
                    creator_data["nickname"], creator_data["signature"],
                    creator_data["avatar_url"], creator_data["follower_count"],
                    creator_data["following_count"], creator_data["aweme_count"],
                    creator_data["total_favorited"], sec_user_id
                )
            else:
                # 插入
                sql = '''
                    INSERT INTO creators (
                        sec_user_id, nickname, signature, avatar_url,
                        follower_count, following_count, aweme_count, total_favorited
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                '''
                params = (
                    creator_data["sec_user_id"], creator_data["nickname"],
                    creator_data["signature"], creator_data["avatar_url"],
                    creator_data["follower_count"], creator_data["following_count"],
                    creator_data["aweme_count"], creator_data["total_favorited"]
                )
            
            db.execute(sql, params)
            print(f"[DouyinStore] Saved creator: {sec_user_id} - {creator_data['nickname']}")
            return True
            
        except Exception as e:
            print(f"[DouyinStore] Error saving creator: {e}")
            return False
    
    @staticmethod
    async def save_video_file(aweme_id: str, content: bytes, file_type: str = "video") -> str:
        """
        保存视频/图片文件到本地
        
        Args:
            aweme_id: 视频ID
            content: 文件二进制内容
            file_type: 文件类型 (video/image)
        
        Returns:
            str: 保存的文件路径
        """
        try:
            save_dir = config.VIDEO_SAVE_DIR if file_type == "video" else config.IMAGE_SAVE_DIR
            os.makedirs(save_dir, exist_ok=True)
            
            ext = "mp4" if file_type == "video" else "jpg"
            file_path = os.path.join(save_dir, f"{aweme_id}.{ext}")
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            # 更新数据库中的文件路径
            db.execute("UPDATE videos SET video_path=? WHERE aweme_id=?", (file_path, aweme_id))
            
            print(f"[DouyinStore] Saved {file_type}: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"[DouyinStore] Error saving {file_type} file: {e}")
            return ""
    
    @staticmethod
    def _extract_video_download_url(aweme_item: Dict) -> str:
        """提取视频下载URL"""
        try:
            video = aweme_item.get("video", {})
            play_addr = video.get("play_addr", {})
            url_list = play_addr.get("url_list", [])
            return url_list[0] if url_list else ""
        except:
            return ""
    
    @staticmethod
    def _extract_note_image_list(aweme_item: Dict) -> List[str]:
        """提取图片列表（图文类型）"""
        try:
            images = aweme_item.get("images", [])
            if not images:
                return []
            url_list = []
            for img in images:
                url_list.append(img.get("url_list", [""])[0])
            return url_list
        except:
            return []


# 全局存储实例
douyin_store = DouyinStore()
