# 校园食堂点餐系统 - API接口文档（完整版）

> **项目名称**: 校园食堂点餐系统  
> **后端框架**: FastAPI + Python 3.9+  
> **数据库**: MySQL 8.0  
> **文档版本**: v2.0  
> **生成时间**: 2026-03-03

---

## 📋 目录

1. [接口概览](#接口概览)
2. [认证授权](#认证授权)
3. [用户模块](#用户模块)
4. [档口管理](#档口管理)
5. [菜品管理](#菜品管理)
6. [分类管理](#分类管理)
7. [购物车](#购物车)
8. [订单管理](#订单管理)
9. [优惠券](#优惠券)
10. [活动管理](#活动管理)
11. [收藏功能](#收藏功能)
12. [评价系统](#评价系统)
13. [搜索功能](#搜索功能)
14. [统计分析](#统计分析)
15. [消息通知](#消息通知)
16. [媒体上传](#媒体上传)
17. [其他功能](#其他功能)

---

## 🌐 接口概览

### 基础信息

- **Base URL**: `http://localhost:8000`
- **API 前缀**: `/api`
- **API 文档**: `http://localhost:8000/docs`
- **认证方式**: JWT Bearer Token
- **响应格式**: JSON

### 通用响应格式

#### 成功响应
```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

#### 错误响应
```json
{
  "detail": "错误信息"
}
```

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（未登录或token过期） |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 422 | 参数验证失败 |
| 500 | 服务器内部错误 |

---

## 🔐 认证授权

### 1. 用户注册

**接口**: `POST /api/auth/register`

**说明**: 用户注册，如果系统中没有管理员，第一个注册的用户将自动成为系统管理员

**请求参数**:
```json
{
  "username": "string",      // 用户名（必填，唯一）
  "password": "string",      // 密码（必填，6-20位）
  "nickname": "string",      // 昵称（可选）
  "phone": "string",         // 手机号（可选）
  "email": "string",         // 邮箱（可选）
  "student_no": "string",    // 学号（可选）
  "role": "user"             // 角色（默认user）
}
```

**响应示例**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expireIn": 7200,
  "userInfo": {
    "user_id": 1,
    "username": "testuser",
    "nickname": "测试用户",
    "role": "user",
    "status": 1
  }
}
```

---

### 2. 用户登录

**接口**: `POST /api/auth/login`

**请求参数**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应示例**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expireIn": 7200,
  "userInfo": {
    "user_id": 1,
    "username": "admin",
    "nickname": "管理员",
    "role": "sys_admin",
    "avatar": "/uploads/avatar_1/avatar.jpg"
  }
}
```

---

### 3. 忘记密码

**接口**: `POST /api/auth/forgot-password`

**请求参数**:
```json
{
  "username": "string"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "验证码已发送",
  "code": "123456"  // 仅开发环境返回
}
```

---

### 4. 重置密码

**接口**: `POST /api/auth/reset-password`

**请求参数**:
```json
{
  "username": "string",
  "verification_code": "string",
  "new_password": "string"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "密码重置成功"
}
```

---

### 5. 管理员注册

**接口**: `POST /api/auth/register-admin`

**说明**: 需要提供管理员注册密钥（环境变量 ADMIN_REGISTER_KEY）

**请求参数**:
```json
{
  "username": "string",
  "password": "string",
  "nickname": "string",
  "admin_key": "string"  // 管理员注册密钥
}
```

---

## 👤 用户模块

### 1. 获取当前用户信息

**接口**: `GET /api/user/info`

**权限**: 需要登录

**响应示例**:
```json
{
  "user_id": 1,
  "username": "testuser",
  "nickname": "测试用户",
  "avatar": "/uploads/avatar_1/avatar.jpg",
  "phone": "13800138000",
  "email": "test@example.com",
  "student_no": "2021001",
  "role": "user",
  "status": 1,
  "create_time": "2026-01-01 10:00:00"
}
```

---

### 2. 更新用户信息

**接口**: `PUT /api/user/info`

**权限**: 需要登录

**请求参数**:
```json
{
  "nickname": "string",
  "phone": "string",
  "email": "string",
  "avatar": "string"
}
```

---

### 3. 修改密码

**接口**: `POST /api/user/change-password`

**权限**: 需要登录

**请求参数**:
```json
{
  "old_password": "string",
  "new_password": "string"
}
```

---

### 4. 获取用户列表（管理端）

**接口**: `GET /api/user/list`

**权限**: 管理员

**查询参数**:
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20，最大1000）
- `keyword`: 搜索关键词（用户名、昵称、学号）
- `role`: 角色筛选
- `status`: 状态筛选（0=禁用，1=启用）

**响应示例**:
```json
{
  "items": [
    {
      "user_id": 1,
      "username": "user1",
      "nickname": "用户1",
      "role": "user",
      "status": 1
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

### 5. 更新用户状态（管理端）

**接口**: `PUT /api/user/status/{user_id}`

**权限**: 管理员

**请求参数**:
```json
{
  "status": 0  // 0=禁用，1=启用
}
```

---

### 6. 批量删除用户（管理端）

**接口**: `POST /api/user/batch-delete`

**权限**: 管理员

**请求参数**:
```json
{
  "user_ids": [1, 2, 3]
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "成功删除 3 个用户",
  "deleted_count": 3
}
```

---

### 7. 批量更新用户（管理端）

**接口**: `POST /api/user/batch-update`

**权限**: 管理员

**请求参数**:
```json
{
  "user_ids": [1, 2, 3],
  "status": 1,           // 可选
  "role": "user"         // 可选
}
```

---

## 🏪 档口管理

### 1. 获取档口列表

**接口**: `GET /api/canteen/list`

**查询参数**:
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20）
- `keyword`: 搜索关键词（档口名称）
- `status`: 状态筛选（0=禁用，1=启用，不传则返回所有）

**响应示例**:
```json
{
  "items": [
    {
      "canteen_id": 1,
      "canteen_name": "第一食堂",
      "building": "学生公寓",
      "floor": "1楼",
      "window_no": "A01",
      "status": 1,
      "latitude": 39.9042,
      "longitude": 116.4074
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

---

### 2. 获取档口详情

**接口**: `GET /api/canteen/detail/{canteen_id}`

**响应示例**:
```json
{
  "canteen_id": 1,
  "canteen_name": "第一食堂",
  "building": "学生公寓",
  "floor": "1楼",
  "window_no": "A01",
  "address": "学生公寓1楼A01窗口",
  "phone": "010-12345678",
  "business_hours": "07:00-20:00",
  "status": 1,
  "latitude": 39.9042,
  "longitude": 116.4074
}
```

---

### 3. 创建档口（管理端）

**接口**: `POST /api/canteen/create`

**权限**: 管理员

**请求参数**:
```json
{
  "canteen_name": "string",
  "building": "string",
  "floor": "string",
  "window_no": "string",
  "address": "string",
  "phone": "string",
  "business_hours": "string",
  "latitude": 39.9042,
  "longitude": 116.4074,
  "status": 1
}
```

---

### 4. 更新档口状态（管理端）

**接口**: `PUT /api/canteen/status/{canteen_id}`

**权限**: 管理员

**查询参数**:
- `status`: 状态值（0=禁用，1=启用）

---

### 5. 批量更新档口状态（管理端）

**接口**: `POST /api/canteen/batch/status`

**权限**: 管理员

**请求参数**:
```json
{
  "canteen_ids": [1, 2, 3],
  "status": 1
}
```

**响应示例**:
```json
{
  "success": true,
  "success_count": 3,
  "failed_count": 0,
  "failed_items": []
}
```

---

### 6. 批量删除档口（管理端）

**接口**: `POST /api/canteen/batch/delete`

**权限**: 管理员

**说明**: 级联删除档口的所有相关数据（菜品、评价、订单等）

**请求参数**:
```json
{
  "canteen_ids": [1, 2, 3]
}
```

---

## 🍜 菜品管理

### 1. 获取菜品列表

**接口**: `GET /api/dish/list`

**查询参数**:
- `page`: 页码
- `page_size`: 每页数量
- `canteen_id`: 档口ID筛选
- `category_id`: 分类ID筛选
- `keyword`: 搜索关键词
- `status`: 状态筛选（0=下架，1=上架）
- `sort_by`: 排序字段（price, view_count, favorite_count, create_time）
- `order`: 排序方向（asc, desc）

**响应示例**:
```json
{
  "items": [
    {
      "dish_id": 1,
      "name": "宫保鸡丁",
      "price": 15.00,
      "images": "/uploads/dishes/dish_1.jpg",
      "description": "经典川菜",
      "canteen_id": 1,
      "category_id": 1,
      "stock": 100,
      "status": 1,
      "view_count": 1000,
      "favorite_count": 50
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

### 2. 获取菜品详情

**接口**: `GET /api/dish/detail/{dish_id}`

**说明**: 自动增加浏览量

**响应示例**:
```json
{
  "dish_id": 1,
  "name": "宫保鸡丁",
  "price": 15.00,
  "images": ["/uploads/dishes/dish_1_1.jpg", "/uploads/dishes/dish_1_2.jpg"],
  "description": "经典川菜，香辣可口",
  "canteen_id": 1,
  "canteen_name": "第一食堂",
  "category_id": 1,
  "category_name": "热菜",
  "stock": 100,
  "status": 1,
  "view_count": 1001,
  "favorite_count": 50,
  "media_path": "/uploads/dishes/dish_1_video.mp4",
  "media_type": "video"
}
```

---

### 3. 创建菜品（管理端）

**接口**: `POST /api/dish/create`

**权限**: 管理员

**请求参数**:
```json
{
  "name": "string",
  "price": 15.00,
  "images": "string",
  "description": "string",
  "canteen_id": 1,
  "category_id": 1,
  "stock": 100,
  "status": 1
}
```

---

### 4. 更新菜品状态（管理端）

**接口**: `PUT /api/dish/status/{dish_id}`

**权限**: 管理员

**请求参数**:
```json
{
  "status": 1  // 0=下架，1=上架
}
```

---

### 5. 批量更新菜品状态（管理端）

**接口**: `POST /api/dish/batch/status`

**权限**: 管理员

**请求参数**:
```json
{
  "dish_ids": [1, 2, 3],
  "status": 1
}
```

---

### 6. 批量删除菜品（管理端）

**接口**: `POST /api/dish/batch/delete`

**权限**: 管理员

**说明**: 软删除，将状态设置为 -1

**请求参数**:
```json
{
  "dish_ids": [1, 2, 3]
}
```

---

### 7. 批量修改价格（管理端）

**接口**: `POST /api/dish/batch/price`

**权限**: 管理员

**请求参数**:
```json
{
  "dish_ids": [1, 2, 3],
  "price_type": "fixed",      // fixed=固定价格, increase=增加, decrease=减少, percent=百分比
  "price_value": 20.00
}
```

**price_type 说明**:
- `fixed`: 设置为固定价格
- `increase`: 增加指定金额
- `decrease`: 减少指定金额
- `percent`: 按百分比调整（如 10 表示增加10%，-10 表示减少10%）

---

### 8. 批量导出菜品（管理端）

**接口**: `POST /api/dish/batch/export`

**权限**: 管理员

**请求参数**:
```json
{
  "dish_ids": [1, 2, 3],     // 可选，不传则导出所有
  "format": "excel",          // excel 或 csv
  "fields": ["菜品ID", "菜品名称", "价格"]  // 可选，指定导出字段
}
```

**响应示例**:
```json
{
  "download_url": "/exports/dishes_20260303120000.xlsx",
  "file_name": "dishes_20260303120000.xlsx",
  "file_size": 102400,
  "record_count": 100
}
```

---

### 9. 库存预警（管理端）

**接口**: `GET /api/dish/stock/warning`

**权限**: 管理员

**查询参数**:
- `threshold`: 库存预警阈值（默认10）

**响应示例**:
```json
{
  "zero_stock": [
    {
      "dish_id": 1,
      "name": "宫保鸡丁",
      "stock": 0,
      "price": 15.00
    }
  ],
  "low_stock": [
    {
      "dish_id": 2,
      "name": "鱼香肉丝",
      "stock": 5,
      "price": 18.00
    }
  ],
  "total_dishes": 100,
  "warning_count": 2
}
```

---

## 📂 分类管理

### 1. 获取分类列表

**接口**: `GET /api/category/list`

**查询参数**:
- `parent_id`: 父分类ID（0表示顶级分类）
- `page`: 页码
- `page_size`: 每页数量

---

### 2. 获取所有分类（树形结构）

**接口**: `GET /api/category/all`

**响应示例**:
```json
[
  {
    "category_id": 1,
    "category_name": "热菜",
    "parent_id": 0,
    "sort_order": 1,
    "children": [
      {
        "category_id": 2,
        "category_name": "川菜",
        "parent_id": 1,
        "sort_order": 1
      }
    ]
  }
]
```

---

### 3. 创建分类（管理端）

**接口**: `POST /api/category/create`

**权限**: 管理员

**请求参数**:
```json
{
  "category_name": "string",
  "parent_id": 0,
  "sort_order": 1
}
```

---

## 🛒 购物车

### 1. 获取购物车列表

**接口**: `GET /api/cart/list`

**权限**: 需要登录

**响应示例**:
```json
[
  {
    "cart_id": 1,
    "user_id": 1,
    "dish_id": 1,
    "dish_name": "宫保鸡丁",
    "price": 15.00,
    "quantity": 2,
    "remark": "少辣",
    "create_time": "2026-03-03 10:00:00"
  }
]
```

---

### 2. 添加到购物车

**接口**: `POST /api/cart/add`

**权限**: 需要登录

**请求参数**:
```json
{
  "dish_id": 1,
  "quantity": 2,
  "remark": "少辣"
}
```

---

### 3. 更新购物车商品

**接口**: `PUT /api/cart/update/{item_id}`

**权限**: 需要登录

**请求参数**:
```json
{
  "quantity": 3,
  "remark": "不要辣"
}
```

---

### 4. 删除购物车商品

**接口**: `DELETE /api/cart/remove/{item_id}`

**权限**: 需要登录

---

详细内容请查看分卷文档：
- [订单管理模块](./API接口文档-订单模块.md)
- [优惠券和活动模块](./API接口文档-营销模块.md)
- [搜索和统计模块](./API接口文档-功能模块.md)

