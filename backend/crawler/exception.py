# -*- coding: utf-8 -*-
"""
异常定义
"""
from httpx import RequestError


class DataFetchError(RequestError):
    """数据获取错误"""
    pass


class IPBlockError(RequestError):
    """IP被封禁错误"""
    pass
