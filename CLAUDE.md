# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库构成

本仓库是毕业设计「校园食堂订餐系统」的单体工作区，包含三个相互独立、通过 HTTP/WebSocket 通信的子项目。目录名含中文和全角括号，shell 中引用路径时必须加引号。

| 目录 | 角色 | 技术栈 |
|---|---|---|
| `server-python（后端）/` | API 服务 | FastAPI + SQLAlchemy + MySQL 8 + Alembic + APScheduler |
| `Hbuilder X（后台管理端）/` | Web 管理后台（仅目录名沿用 HBuilder X，实际与 HBuilder 无关） | Vue 3 + Vite + Element Plus + Pinia |
| `微信小程序端（前端）/` | 学生端原生微信小程序 | 原生小程序（无构建步骤），用微信开发者工具打开 |

接口契约的唯一权威来源是两份 `campus_canteen_apifox.json`（后端、管理端各一份，可用 Apifox 导入）；后端运行时另提供 `/docs`（Swagger UI）。各目录下的 `*接口文档*.md` 是人工维护的辅助文档。仓库未配置测试框架，不要臆造测试命令。

## 常用命令

### 后端（在 `server-python（后端）/` 下，先激活 `.venv`：`.venv\Scripts\activate`）

```bash
pip install -r requirements.txt
python run_server.py                       # 启动（同时是 PyInstaller 打包入口）
# 或开发模式：uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
alembic revision --autogenerate -m "描述"  # 改完 model 后生成迁移
alembic upgrade head                       # 应用迁移；回滚：alembic downgrade -1
```

Windows 下可直接双击 `启动服务器.bat` / `start.bat`。配置从 `.env` 读取（模板为 `env.example`、`config.example.env`，优先级：环境变量 > `.env` > 默认值）。MySQL 数据库名 `campus_canteen_order`，需提前手动 `CREATE DATABASE`。`scripts/` 下是菜品数据的播种/修复脚本（如 `reset_and_seed_dishes.py`）。

### 管理后台（在 `Hbuilder X（后台管理端）/` 下）

```bash
npm install
npm run dev      # http://localhost:5173，/api 与 /uploads 由 Vite 代理到 http://localhost:8000
npm run build    # 产物在 dist/
```

### 小程序

用微信开发者工具打开 `微信小程序端（前端）/` 目录，无命令行构建。后端地址在 `utils/config.js` 顶部通过 `ENV = 'dev' | 'lan' | 'prod'` 切换；真机调试选 `lan` 并把其中 IP 改成本机局域网 IP，同时在开发者工具中勾选「不校验合法域名」。

## 后端架构要点

- **分层**：`app/api/v1/*.py`（路由）→ `app/services/*.py`（业务逻辑）→ `app/crud/*.py`（数据访问，统一继承 `crud/base.py` 的泛型 CRUD）→ `app/models/*.py`（SQLAlchemy）；`app/schemas/` 为 Pydantic 模型。路由全部在 `app/main.py` 中手动 `include_router`，多数挂在 `/api` 前缀下，但 notification/refund/search 等有各自的二级前缀（如 `/api/notification`、`/api/refund`），新增路由时注意核对。
- **认证与角色**：JWT（HS256，见 `app/core/security.py`）通过 `Authorization: Bearer` 传递；统一依赖在 `app/api/deps.py`：`get_current_user`、`get_current_user_optional`、`require_admin`、`require_merchant`。角色为字符串 `user` / `merchant` / `admin`。注册管理员需 `.env` 中的 `ADMIN_REGISTER_KEY`。
- **订单状态机**：`orders.order_status` 和 `pay_status` 均为整数编码（如 order_status：1=制作中，2=待取餐，4=已完成，5=已取消；状态文案映射散落在 `api/v1/orders.py`、`crud/order.py` 等处，改动时需全局同步）。状态每次流转写入 `order_status_log`，并触发站内通知 + WebSocket 推送。下单有库存预扣（`services/inventory_service.py`），取消/退款时回滚。
- **定时任务**：`services/scheduler_service.py` 在 startup 时由 APScheduler 注册——每 5 分钟自动取消超时未支付订单（超时见 `core/order_config.py`，默认 30 分钟）、每 10 分钟检查待取餐超时、退款审批超时检查、旧通知清理。
- **实时通道**：`api/v1/websocket.py` 的 `ConnectionManager` 按 user_id（及管理员集合）维护连接，端点 `/api/ws`，用于订单状态实时推送；前端两端均有「WebSocket + 轮询兜底」双通道。
- **文件与导出**：上传文件固定存到项目根的 `uploads/`（忽略 `.env` 中路径的盘符差异，见 `app/storage/media.py`），以 `/uploads` 挂载提供访问；`/static` 同理。`api/v1/export.py` 用 pandas/openpyxl 导出 Excel 到 `exports/`。

## 前端架构要点

- **小程序**：`app.js` 的 `globalData` 是全局状态中心（token、userInfo、wsManager、未读数、结算暂存 `checkoutItems`），启动时做登录态检查、消息轮询（60s 拉未读数并写 tabBar 角标）和 WebSocket 连接。所有请求走 `utils/api.js` 的 `request()` 封装（GET 默认重试 1 次、自动 loading/toast、统一错误提取），页面只调用其上的业务方法而不直接 `wx.request`。`components/admin-alert-overlay` 是管理员强提醒浮层（商家端排队/告警），通过 `app.js` 的 `updateAdminAlertOverlay` 与页面数据同步。
- **管理后台**：`src/utils/request.js` 是 axios 实例（401 自动清 localStorage 并跳 `/login`），`BASE_URL` 默认空字符串即走 Vite 代理；接口按模块组织在 `src/api/modules/`，页面在 `src/views/`。路由与菜单分别在 `src/router/index.js`、`menu.js`。部分模块（用户、菜品、排队等）仍是 `PlaceholderView` 骨架页，开发前先确认目标页面是否已实现。图片等资源的绝对地址前缀使用 `ASSET_BASE_URL`（默认 `http://localhost:8000`）。

## 注意事项

- 后端目录内同时存在 `venv/` 和 `.venv/` 两套虚拟环境，以 `.venv` 为准（启动脚本使用它）。
- 仓库 `.env` 含真实开发库口令且已被提交，仅适用于本机演示；涉及部署改动时不要把生产密钥写入该文件。
- 根目录的 `.docx` 是毕业论文定稿，`.remember/`、`.ccgui/` 为工具目录，与业务代码无关。
