# -*- coding: utf-8 -*-
"""
数据库模块入口
"""
from .models import db, Database
from .store import douyin_store, DouyinStore

__all__ = ['db', 'Database', 'douyin_store', 'DouyinStore']
