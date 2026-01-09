# -*- coding: utf-8 -*-
"""
SQLite 数据库模型定义
"""
import sqlite3
from datetime import datetime
from typing import Optional
import config


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        self.conn: Optional[sqlite3.Connection] = None
        self.init_db()
    
    def init_db(self):
        """初始化数据库，创建表"""
        # 确保数据库目录存在
        import os
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        
        # 创建视频表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aweme_id TEXT UNIQUE NOT NULL,
                title TEXT,
                desc TEXT,
                author_name TEXT,
                author_id TEXT,
                video_url TEXT,
                cover_url TEXT,
                like_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                share_count INTEGER DEFAULT 0,
                create_time TIMESTAMP,
                crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                keyword TEXT,
                video_path TEXT
            )
        ''')
        
        # 创建创作者表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS creators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sec_user_id TEXT UNIQUE NOT NULL,
                nickname TEXT,
                signature TEXT,
                avatar_url TEXT,
                follower_count INTEGER DEFAULT 0,
                following_count INTEGER DEFAULT 0,
                aweme_count INTEGER DEFAULT 0,
                total_favorited INTEGER DEFAULT 0,
                crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_aweme_id ON videos(aweme_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_author_id ON videos(author_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sec_user_id ON creators(sec_user_id)')
        
        self.conn.commit()
        print(f"[Database] Database initialized: {self.db_path}")
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("[Database] Database connection closed")
    
    def execute(self, sql: str, params: tuple = None):
        """执行SQL语句"""
        cursor = self.conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        self.conn.commit()
        return cursor
    
    def fetchone(self, sql: str, params: tuple = None):
        """查询单条记录"""
        cursor = self.conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor.fetchone()
    
    def fetchall(self, sql: str, params: tuple = None):
        """查询多条记录"""
        cursor = self.conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor.fetchall()


# 全局数据库实例
db = Database()
