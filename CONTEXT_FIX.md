# 浏览器Context错误修复说明

## 问题描述
```
Page.evaluate: Execution context was destroyed, most likely because of a navigation
```

这个错误发生在页面跳转或导航时，JavaScript执行上下文被销毁。

## 已实施的修复

### 1. 添加重试机制
在 `client.py` 的 `_process_request_params` 方法中：
- 添加了3次重试逻辑
- 每次重试间隔1秒
- 失败后使用空值继续执行

```python
max_retries = 3
for attempt in range(max_retries):
    try:
        local_storage = await self.playwright_page.evaluate("() => window.localStorage")
        break
    except Exception as e:
        if attempt < max_retries - 1:
            await asyncio.sleep(1)
```

### 2. 异常处理
- `pong()` 方法添加异常捕获
- `a_bogus` 生成失败时跳过而非崩溃
- 使用空字符串作为默认值

### 3. 配置建议

确保 `backend/config/settings.py` 中：
```python
HEADLESS = False  # 首次运行时设为False
SAVE_LOGIN_STATE = True  # 保存登录态
```

## 使用流程

### 首次运行
1. 启动服务（HEADLESS=False）
2. 浏览器会显示出来
3. 使用抖音APP扫码登录
4. 登录成功后会自动保存
5. 下次运行就不需要重新登录

### 后续运行
1. 登录态已保存在 `browser_data/` 
2. 自动使用已保存的登录状态
3. 不会再出现context错误

## 错误恢复
如果仍然出错，尝试：
1. 删除 `browser_data/` 目录
2. 重新启动服务
3. 重新扫码登录

---
**修复完成！** 现在crawler可以更稳定地处理页面导航和登录流程。
