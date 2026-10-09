# 校园食堂点餐系统 - Python 后端服务

基于 FastAPI + SQLAlchemy + MySQL 的后端 API 服务。

## 📋 前置要求

- **Python**: 3.8 或更高版本
- **MySQL**: 8.0 或更高版本（已安装并运行）
- **操作系统**: Windows / Linux / macOS

## 🚀 快速开始

### 步骤 1: 检查 Python 环境

打开命令行（Windows: PowerShell 或 CMD，Mac/Linux: Terminal），检查 Python 版本：

```bash
python --version
# 或
python3 --version
```

如果未安装 Python，请访问 [python.org](https://www.python.org/downloads/) 下载安装。

### 步骤 2: 创建虚拟环境（推荐）

在项目根目录 `server-python` 下执行：

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

激活成功后，命令行提示符前会显示 `(venv)`。

### 步骤 3: 安装依赖

确保虚拟环境已激活，执行：

```bash
pip install -r requirements.txt
```

**注意**: 如果安装 `mysqlclient` 失败（Windows 常见），可以：

1. 先安装 MySQL 客户端库：
   - 下载 [MySQL Connector/C](https://dev.mysql.com/downloads/connector/c/)
   - 或使用替代方案：修改 `requirements.txt` 中的 `mysqlclient` 为 `pymysql`，并在代码中调整连接字符串

2. 使用 `pymysql` 替代（推荐 Windows 用户）：
   ```bash
   pip install pymysql
   ```
   然后修改 `.env` 中的 `DATABASE_URL` 为：
   ```
   DATABASE_URL=mysql+pymysql://root:password@localhost:3306/campus_canteen_order
   ```

### 步骤 4: 配置数据库

#### 4.1 创建数据库

登录 MySQL（命令行或 Navicat/MySQL Workbench），执行：

```sql
CREATE DATABASE IF NOT EXISTS campus_canteen_order CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 4.2 配置环境变量

在 `server-python` 目录下创建 `.env` 文件（复制 `.env.example` 并修改）：

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Mac/Linux
cp .env.example .env
```

编辑 `.env` 文件，修改以下配置：

```env
DATABASE_URL=mysql+mysqlclient://root:你的MySQL密码@localhost:3306/campus_canteen_order
JWT_SECRET=你的随机密钥（建议32位以上）
JWT_EXPIRE=7200
MEDIA_UPLOAD_PATH=uploads
```

**重要提示**:
- 将 `你的MySQL密码` 替换为实际 MySQL root 密码
- `JWT_SECRET` 建议使用随机字符串生成器生成
- `MEDIA_UPLOAD_PATH` 默认固定为项目根目录下的 `uploads` 文件夹，推荐保持默认值

### 步骤 5: 创建媒体上传目录

在项目根目录下确保存在 `uploads` 文件夹：

**Windows:**
```bash
mkdir uploads
```

**Mac/Linux:**
```bash
mkdir -p uploads
```

默认会固定使用项目根目录下的 `uploads` 目录，避免因系统盘符或权限差异导致上传失败。

### 步骤 6: 数据库迁移（创建表结构）

在 `server-python` 目录下执行：

```bash
# 生成迁移文件（自动扫描 models 生成 SQL）
alembic revision --autogenerate -m "init schema"

# 执行迁移（在数据库中创建表）
alembic upgrade head
```

**如果遇到错误**:
- 确保 MySQL 服务已启动
- 检查 `.env` 中的 `DATABASE_URL` 是否正确
- 确保数据库 `campus_canteen_order` 已创建

### 步骤 7: 启动服务

在 `server-python` 目录下执行：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**参数说明**:
- `--reload`: 代码修改后自动重启（开发模式）
- `--host 0.0.0.0`: 允许外部访问（小程序可连接）
- `--port 8000`: 监听端口

启动成功后，你会看到类似输出：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 步骤 8: 测试接口

#### 8.1 访问 API 文档（Swagger UI）

浏览器打开：
```
http://localhost:8000/docs
```

这是 FastAPI 自动生成的交互式 API 文档，可以直接测试接口。

#### 8.2 健康检查

```bash
curl http://localhost:8000/health
```

或浏览器访问：`http://localhost:8000/health`

应该返回：
```json
{"status": "ok"}
```

#### 8.3 测试注册接口

使用 Postman 或 `curl`：

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test001",
    "password": "123456",
    "nickname": "测试用户"
  }'
```

## 📱 小程序配置

在微信小程序中，将 API 基础地址配置为：

```javascript
// utils/api.js
const BASE_URL = 'http://localhost:8000/api'
// 或你的本机 IP（局域网访问）：
// const BASE_URL = 'http://192.168.1.100:8000/api'
```

**注意**: 
- 小程序真机调试需要使用局域网 IP，不能使用 `localhost`
- 在微信开发者工具中，需要在“设置 -> 项目设置 -> 本地设置”中勾选“不校验合法域名”

## 🔧 常见问题

### 1. `mysqlclient` 安装失败（Windows）

**解决方案**: 使用 `pymysql` 替代，修改 `.env`：
```
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/campus_canteen_order
```

### 2. 数据库连接失败

- 检查 MySQL 服务是否启动
- 检查 `.env` 中的用户名、密码、数据库名是否正确
- 检查 MySQL 是否允许本地连接

### 3. Alembic 迁移失败

- 确保数据库已创建
- 检查 `alembic/env.py` 中是否正确导入了所有模型
- 手动检查 `alembic/versions/` 目录下是否有迁移文件

### 4. 端口被占用

如果 8000 端口被占用，可以修改端口：
```bash
uvicorn app.main:app --reload --port 8001
```

### 5. 媒体文件上传失败

- 检查 `MEDIA_UPLOAD_PATH` 路径是否存在
- 检查文件夹权限（Linux/Mac 需要写权限）

## 📂 项目结构

```
server-python/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── core/                 # 核心配置（config, security, errors, logging）
│   ├── db/                   # 数据库会话
│   ├── models/               # SQLAlchemy 模型
│   ├── schemas/              # Pydantic 模型（请求/响应）
│   ├── crud/                 # 数据访问层
│   ├── api/v1/               # API 路由
│   ├── services/             # 业务逻辑层
│   └── storage/              # 文件存储
├── alembic/                  # 数据库迁移
├── alembic.ini               # Alembic 配置
├── requirements.txt          # Python 依赖
├── .env                      # 环境变量（需自行创建）
└── README.md                 # 本文档
```

## 🛠️ 开发命令

### 创建新的数据库迁移

```bash
alembic revision --autogenerate -m "描述信息"
alembic upgrade head
```

### 回滚迁移

```bash
alembic downgrade -1
```

### 查看迁移历史

```bash
alembic history
```

## 📝 下一步

1. ✅ 后端服务已启动
2. 📱 配置小程序前端，连接后端 API
3. 🧪 使用 Postman 或 Swagger UI 测试所有接口
4. 📊 在数据库中插入测试数据（档口、菜品等）
5. 🚀 部署到生产环境（可选）

## 📞 技术支持

如有问题，请检查：
- 日志输出（控制台）
- MySQL 错误日志
- FastAPI 自动生成的 API 文档：`http://localhost:8000/docs`

---

**版本**: 1.0.0  
**最后更新**: 2025-01-06

