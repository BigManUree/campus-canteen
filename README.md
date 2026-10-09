# 校园食堂订餐系统

基于微信小程序的校园食堂订餐系统，支持学生在线浏览菜品、下单支付、取餐核销，以及商家/管理员对订单、菜品、退款等进行后台管理。系统由 **微信小程序端（学生端）**、**Web 管理后台** 和 **Python 后端服务** 三部分组成。

## 技术栈

| 模块 | 技术 |
|---|---|
| 小程序端 | 微信小程序原生框架（WXML / WXSS / JavaScript） |
| 管理后台 | Vue 3 + Vite + Element Plus + Pinia + Vue Router + ECharts |
| 后端 | Python + FastAPI + SQLAlchemy + Pydantic |
| 数据库 | MySQL 8.0 |
| 数据库迁移 | Alembic |
| 实时通信 | WebSocket（订单状态推送） |
| 定时任务 | APScheduler（超时订单自动取消等） |

## 功能特性

### 学生端（微信小程序）

- 用户注册、登录、忘记密码，个人资料维护与密码修改
- 浏览食堂、档口与菜品，按分类查看、关键词搜索
- 菜品详情、收藏、浏览历史
- 购物车管理与下单结算
- 订单全流程管理：下单 → 支付 → 制作中 → 待取餐 → 完成（取餐核销）
- 订单取消、退款申请与退款进度查询
- 订单评价、食堂评价
- 收货地址管理
- 优惠券、活动、常见问题（FAQ）
- 站内消息通知，订单状态 WebSocket 实时推送 + 轮询兜底

### 管理后台（Web）

- 管理员登录与鉴权
- 数据看板
- 订单管理（接单、状态流转、核销等）
- 退款管理
- 全局订单通知（WebSocket 实时通知）

> 说明：用户管理、菜品管理、档口管理、分类管理、优惠券、活动、评价、通知、FAQ、统计分析、报表导出、排队管理等模块已完成菜单路由与页面骨架，可在现有骨架上继续开发。接口对接以 `campus_canteen_apifox.json` 为准。

### 后端服务

- RESTful API，统一前缀 `/api`，JWT（Bearer Token）鉴权
- 三类角色：普通用户（学生）、商家（merchant）、管理员（admin）
- 订单状态流转记录（状态日志）
- 下单库存预扣，取消/退款时回滚
- 未支付订单超时自动取消（默认 30 分钟，每 5 分钟检查）
- 待取餐超时提醒、退款审批超时检查、旧通知定时清理
- 图片等文件上传与静态资源访问（`/uploads`）
- 订单数据 Excel 导出

## 系统架构

```
┌──────────────────────┐       HTTP / WebSocket       ┌──────────────────────┐
│   微信小程序（学生端）  │ ───────────────────────────▶ │                      │
└──────────────────────┘                               │                      │
                                                       │   FastAPI 后端服务     │
┌──────────────────────┐       HTTP / WebSocket       │   （端口 8000）       │
│  Web 管理后台（Vue3）  │ ───────────────────────────▶ │                      │
└──────────────────────┘                               └─────────┬────────────┘
                                                                 │ SQLAlchemy
                                                                 ▼
                                                        ┌──────────────────────┐
                                                        │   MySQL 数据库        │
                                                        └──────────────────────┘
```

## 项目结构

```
校园点餐小程序/
├── server-python（后端）/        # FastAPI 后端服务
│   ├── app/
│   │   ├── main.py              # 应用入口、中间件、路由注册
│   │   ├── api/v1/              # API 路由
│   │   ├── services/            # 业务逻辑（订单、退款、库存、定时任务等）
│   │   ├── crud/                # 数据访问层
│   │   ├── models/              # SQLAlchemy 模型
│   │   ├── schemas/             # Pydantic 模型
│   │   ├── core/                # 配置、安全、日志
│   │   └── storage/             # 文件存储
│   ├── alembic/                 # 数据库迁移
│   ├── scripts/                 # 数据播种/修复脚本
│   ├── requirements.txt
│   └── run_server.py            # 启动入口（亦为 PyInstaller 打包入口）
├── Hbuilder X（后台管理端）/      # Vue 3 + Vite 管理后台
│   ├── src/
│   │   ├── api/modules/         # 按模块组织的接口
│   │   ├── views/               # 页面
│   │   ├── router/              # 路由与菜单
│   │   ├── stores/              # Pinia 状态
│   │   └── utils/               # axios 封装等
│   └── package.json
└── 微信小程序端（前端）/           # 原生微信小程序
    ├── pages/                   # 页面
    ├── components/              # 组件
    ├── utils/                   # 请求封装、配置、WebSocket
    ├── app.js
    └── app.json
```

## 快速开始

### 1. 启动后端服务

环境要求：Python 3.8+、MySQL 8.0+。

```bash
cd "server-python（后端）"

# 创建并激活虚拟环境
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 安装依赖
pip install -r requirements.txt
```

创建数据库：

```sql
CREATE DATABASE IF NOT EXISTS campus_canteen_order CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

复制并编辑环境配置（`env.example` 为配置模板），将数据库密码等改为本机实际值：

```env
DATABASE_URL=mysql+pymysql://root:你的密码@localhost:3306/campus_canteen_order
JWT_SECRET=你的随机密钥
JWT_EXPIRE=7200
```

执行数据库迁移并启动服务：

```bash
alembic upgrade head
python run_server.py
# 或开发模式：uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Windows 下也可直接双击 `启动服务器.bat`。服务启动后：

- API 文档（Swagger UI）：<http://localhost:8000/docs>
- 健康检查：<http://localhost:8000/health>

### 2. 启动管理后台

```bash
cd "Hbuilder X（后台管理端）"
npm install
npm run dev
```

浏览器访问 <http://localhost:5173>。开发服务器已配置代理，`/api` 与 `/uploads` 请求会自动转发到 `http://localhost:8000`。

构建生产包：`npm run build`（产物在 `dist/`）。

### 3. 运行微信小程序

1. 使用微信开发者工具打开 `微信小程序端（前端）` 目录。
2. 在 `utils/config.js` 顶部通过 `ENV` 切换后端地址：
   - `dev`：`http://127.0.0.1:8000`（模拟器调试）
   - `lan`：将其中 IP 改为电脑的局域网 IP（真机调试）
3. 真机调试时需在开发者工具「本地设置」中勾选「不校验合法域名」。

## 接口文档

- 后端启动后访问 Swagger UI：<http://localhost:8000/docs>
- 完整接口集合可使用 Apifox 导入 `campus_canteen_apifox.json`
- 另有 Markdown 格式的接口文档：`server-python（后端）/API接口文档-毕业设计完整版.md`、`Hbuilder X（后台管理端）/管理端接口文档.md`

## 效果截图

### 学生端小程序

| | | |
|---|---|---|
| ![登录](docs/screenshots/mini-login.png) | ![首页](docs/screenshots/mini-home.png) | ![分类点餐](docs/screenshots/mini-category.png) |
| ![菜品详情](docs/screenshots/mini-dish.png) | ![购物车](docs/screenshots/mini-cart.png) | ![确认订单](docs/screenshots/mini-checkout.png) |
| ![我的订单](docs/screenshots/mini-orders.png) | ![订单详情](docs/screenshots/mini-order-detail.png) | |

### 管理后台

| | |
|---|---|
| ![订单管理](docs/screenshots/admin-orders.png) | ![食堂管理](docs/screenshots/admin-canteens.png) |
| ![优惠券管理](docs/screenshots/admin-coupons.png) | ![活动管理](docs/screenshots/admin-activities.png) |

## 补充说明

- 当前支付环节为**模拟支付**，未接入真实微信支付，支付后订单直接进入后续状态。
- 菜品测试数据可通过 `server-python（后端）/scripts/` 下的脚本进行播种。
