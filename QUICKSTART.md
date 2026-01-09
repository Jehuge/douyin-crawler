# 快速开始指南

## 1. 创建虚拟环境（已完成）

```bash
python3 -m venv venv
```

## 2. 安装依赖

```bash
# 升级pip
./venv/bin/pip install --upgrade pip

# 安装所有依赖
./venv/bin/pip install fastapi uvicorn[standard] pydantic playwright httpx PyExecJS

# 安装浏览器
./venv/bin/python -m playwright install chromium
```

## 3. 启动服务

```bash
# 方式1: 使用启动脚本
./start.sh

# 方式2: 直接运行
./venv/bin/python api.py
```

## 4. 访问Web界面

打开浏览器访问: **http://localhost:8000**

## 5. 开始使用

1. 选择爬取模式（搜索/指定视频/创作者）
2. 填写相应参数
3. 点击"开始爬取"
4. 等待爬取完成
5. 查看数据列表

## 常见问题

### Q: 如何激活虚拟环境？
```bash
source venv/bin/activate  # macOS/Linux
```

### Q: 如何停止服务？
按 `Ctrl+C` 停止服务

### Q: 第一次运行需要做什么？
首次运行会打开浏览器，需要使用抖音APP扫码登录。登录后会自动保存登录态。

## 项目结构

```
douyin-crawler/
├── api.py           # FastAPI后端
├── start.sh         # 启动脚本
├── venv/            # 虚拟环境
├── backend/         # 后端代码
└── frontend/        # 前端界面
```
