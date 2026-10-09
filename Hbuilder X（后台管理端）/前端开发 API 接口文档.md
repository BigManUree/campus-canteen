# 前端开发 API 接口文档

本文档面向前端开发者，提供所有后端 API 接口的详细说明，包括请求方法、路径、参数、响应格式和示例代码。

## 目录

1. [基础说明](#基础说明)
2. [认证相关](#认证相关)
3. [用户相关](#用户相关)
4. [地址管理](#地址管理)
5. [分类管理](#分类管理)
6. [档口管理](#档口管理)
7. [菜品管理](#菜品管理)
8. [购物车](#购物车)
9. [订单管理](#订单管理)
10. [优惠券](#优惠券)
11. [收藏](#收藏)
12. [评价](#评价)
13. [浏览历史](#浏览历史)
14. [消息](#消息)
15. [通知](#通知)
16. [退款](#退款)
17. [媒体文件](#媒体文件)
18. [位置与距离](#位置与距离)
19. [排队信息](#排队信息)
20. [FAQ](#faq)
21. [活动](#活动)
22. [数据统计](#数据统计)
23. [数据导出](#数据导出)

---

## 基础说明

### Base URL
```
开发环境: http://localhost:8000
生产环境: 根据实际部署地址配置
```

### 认证方式
所有需要认证的接口都需要在请求头中携带 JWT Token：
```
Authorization: Bearer {token}
```

### 响应格式
- **成功响应**: HTTP 状态码 200-299，响应体为 JSON 格式
- **错误响应**: HTTP 状态码 400+，响应体格式：
```json
{
  "detail": "错误信息"
}
```

### 分页响应格式
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

## 认证相关

### 1. 用户注册
**POST** `/api/auth/register`

**请求体**:
```json
{
  "username": "string",      // 用户名（必填）
  "password": "string",      // 密码（必填）
  "phone": "string",         // 手机号（必填）
  "nickname": "string"       // 昵称（可选）
}
```

**响应**:
```json
{
  "token": "jwt_token_string",
  "expireIn": 7200,
  "userInfo": {
    "user_id": 1,
    "username": "string",
    "nickname": "string",
    "phone": "string",
    "role": "user",
    "status": 1
  }
}
```

**错误码**:
- `400`: 用户名已存在

---

### 2. 用户登录
**POST** `/api/auth/login`

**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应**: 同注册接口

**错误码**:
- `400`: 账号或密码错误

---

### 3. 忘记密码
**POST** `/api/auth/forgot-password`

**查询参数**:
- `username` (string, 必填): 用户名

**响应**:
```json
{
  "success": true,
  "message": "验证码已发送"
}
```

**注意**: 开发环境（`ENV=development`）会在响应中返回验证码，生产环境需要通过短信/邮件获取。

---

### 4. 重置密码
**POST** `/api/auth/reset-password`

**查询参数**:
- `username` (string, 必填): 用户名
- `verification_code` (string, 必填): 验证码
- `new_password` (string, 必填): 新密码

**响应**:
```json
{
  "success": true,
  "message": "密码重置成功"
}
```

**错误码**:
- `400`: 验证码错误或已过期
- `404`: 用户不存在

---

## 用户相关

### 1. 获取当前用户信息
**GET** `/api/user/info`

**需要认证**: ✅

**响应**:
```json
{
  "user_id": 1,
  "username": "string",
  "nickname": "string",
  "phone": "string",
  "email": "string",
  "avatar": "string",
  "role": "user",
  "status": 1,
  "student_no": "string"
}
```

---

### 2. 更新用户信息
**PUT** `/api/user/info`

**需要认证**: ✅

**请求体**:
```json
{
  "nickname": "string",      // 可选
  "phone": "string",          // 可选
  "email": "string",          // 可选
  "avatar": "string",         // 可选
  "student_no": "string"      // 可选
}
```

**响应**: 同获取用户信息

---

### 3. 修改密码
**POST** `/api/user/change-password`

**需要认证**: ✅

**查询参数**:
- `old_password` (string, 必填): 旧密码
- `new_password` (string, 必填): 新密码

**响应**:
```json
{
  "success": true,
  "message": "密码修改成功"
}
```

**错误码**:
- `400`: 旧密码错误

---

## 地址管理

### 1. 获取地址列表
**GET** `/api/address/list`

**需要认证**: ✅

**响应**:
```json
[
  {
    "address_id": 1,
    "user_id": 1,
    "receiver": "收件人",
    "phone": "13900139000",
    "building": "1号楼",
    "room": "101",
    "is_default": 1
  }
]
```

---

### 2. 创建地址
**POST** `/api/address/create`

**需要认证**: ✅

**请求体**:
```json
{
  "receiver": "string",      // 收件人（必填）
  "phone": "string",          // 手机号（必填）
  "building": "string",      // 楼栋（必填）
  "room": "string",          // 房间号（必填）
  "is_default": 1            // 是否默认地址：0-否，1-是（可选）
}
```

**响应**: 返回创建的地址对象

---

### 3. 更新地址
**PUT** `/api/address/update/{address_id}`

**需要认证**: ✅

**路径参数**:
- `address_id` (int): 地址ID

**请求体**: 同创建地址（所有字段可选）

**响应**: 返回更新后的地址对象

---

### 4. 删除地址
**DELETE** `/api/address/delete/{address_id}`

**需要认证**: ✅

**路径参数**:
- `address_id` (int): 地址ID

**响应**:
```json
{
  "success": true
}
```

---

## 分类管理

### 1. 获取分类列表
**GET** `/api/category/list`

**响应**:
```json
[
  {
    "category_id": 1,
    "name": "分类名称",
    "sort_order": 0,
    "status": 1
  }
]
```

---

### 2. 获取所有分类（管理端）
**GET** `/api/category/all`

**需要认证**: ✅ (管理员)

**响应**: 同分类列表

---

### 3. 获取分类详情
**GET** `/api/category/detail/{category_id}`

**路径参数**:
- `category_id` (int): 分类ID

**响应**: 单个分类对象

---

## 档口管理

### 1. 获取档口列表
**GET** `/api/canteen/list`

**响应**:
```json
[
  {
    "canteen_id": 1,
    "canteen_name": "档口名称",
    "building": "A",
    "floor": "1F",
    "window_no": "01",
    "status": 1
  }
]
```

---

### 2. 获取档口详情
**GET** `/api/canteen/detail/{canteen_id}`

**路径参数**:
- `canteen_id` (int): 档口ID

**响应**: 单个档口对象（包含更多详细信息）

---

## 菜品管理

### 1. 获取菜品列表
**GET** `/api/dish/list`

**查询参数**:
- `page` (int, 默认1): 页码
- `page_size` (int, 默认20): 每页数量
- `canteen_id` (int, 可选): 档口ID筛选
- `category_id` (int, 可选): 分类ID筛选
- `keyword` (string, 可选): 搜索关键词（菜品名称、描述）
- `sort_by` (string, 默认"create_time"): 排序字段（price, view_count, favorite_count, create_time）
- `order` (string, 默认"desc"): 排序方向（asc, desc）

**响应**: 分页格式
```json
{
  "items": [
    {
      "dish_id": 1,
      "name": "菜品名称",
      "price": 15.0,
      "description": "菜品描述",
      "image": "图片URL",
      "canteen_id": 1,
      "category_id": 1,
      "status": 1,
      "stock": 100,
      "view_count": 0,
      "favorite_count": 0
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

### 2. 获取菜品详情
**GET** `/api/dish/detail/{dish_id}`

**路径参数**:
- `dish_id` (int): 菜品ID

**响应**: 单个菜品对象（包含更多详细信息）

**注意**: 访问详情会自动增加浏览量

---

## 购物车

### 1. 获取购物车列表
**GET** `/api/cart/list`

**需要认证**: ✅

**响应**:
```json
[
  {
    "item_id": 1,
    "user_id": 1,
    "dish_id": 1,
    "quantity": 2,
    "remark": "少辣",
    "dish": {
      "dish_id": 1,
      "name": "菜品名称",
      "price": 15.0
    }
  }
]
```

---

### 2. 添加购物车
**POST** `/api/cart/add`

**需要认证**: ✅

**请求体**:
```json
{
  "dish_id": 1,              // 菜品ID（必填）
  "quantity": 2,             // 数量（必填）
  "remark": "string"         // 备注（可选）
}
```

**响应**: 返回购物车项对象

**错误码**:
- `404`: 菜品不存在或已下架

---

### 3. 更新购物车
**PUT** `/api/cart/update/{item_id}`

**需要认证**: ✅

**路径参数**:
- `item_id` (int): 购物车项ID

**请求体**:
```json
{
  "quantity": 3,              // 数量（可选）
  "remark": "string"         // 备注（可选）
}
```

**响应**: 返回更新后的购物车项对象

**错误码**:
- `400`: 数量必须大于0
- `404`: 购物车商品不存在

---

### 4. 删除购物车项
**DELETE** `/api/cart/remove/{item_id}`

**需要认证**: ✅

**路径参数**:
- `item_id` (int): 购物车项ID

**响应**:
```json
{
  "success": true
}
```

---

## 订单管理

### 1. 创建订单
**POST** `/api/order/create`

**需要认证**: ✅

**请求体**:
```json
{
  "canteen_id": 1,           // 档口ID（必填）
  "order_type": "pickup",   // 订单类型：pickup-自提，delivery-配送（必填）
  "items": [                 // 订单项列表（必填）
    {
      "dish_id": 1,
      "quantity": 2
    }
  ],
  "address_id": 1,          // 配送地址ID（delivery时必填）
  "coupon_id": 1,           // 优惠券ID（可选，必须是已领取的优惠券）
  "remark": "string",       // 备注（可选）
  "pickup_time": "2024-01-01T12:00:00"  // 预约取餐时间（可选）
}
```

**响应**:
```json
{
  "order_id": 1,
  "order_no": "ORDER20240101001",
  "user_id": 1,
  "canteen_id": 1,
  "order_type": "pickup",
  "order_status": 1,
  "pay_status": 0,
  "total_amount": 30.0,
  "discount_amount": 0.0,
  "final_amount": 30.0,
  "pickup_code": "A001",
  "remark": "string",
  "create_time": "2024-01-01T10:00:00",
  "items": [
    {
      "order_item_id": 1,
      "dish_id": 1,
      "quantity": 2,
      "price": 15.0,
      "dish": {
        "name": "菜品名称"
      }
    }
  ]
}
```

**错误码**:
- `404`: 优惠券不存在或已使用
- `400`: 地址不存在（delivery类型时）
- `400`: 菜品不存在或已下架

---

### 2. 获取订单列表
**GET** `/api/order/list`

**需要认证**: ✅

**响应**:
```json
[
  {
    "order_id": 1,
    "order_no": "ORDER20240101001",
    "order_status": 1,
    "pay_status": 0,
    "final_amount": 30.0,
    "pickup_code": "A001",
    "create_time": "2024-01-01T10:00:00"
  }
]
```

---

### 3. 获取订单详情
**GET** `/api/order/detail/{order_id}`

**需要认证**: ✅

**路径参数**:
- `order_id` (int): 订单ID

**响应**: 完整的订单对象（包含订单项、档口信息等）

**错误码**:
- `404`: 订单不存在
- `403`: 无权访问此订单

---

### 4. 支付订单
**POST** `/api/order/pay/{order_id}`

**需要认证**: ✅

**路径参数**:
- `order_id` (int): 订单ID

**响应**: 更新后的订单对象

**错误码**:
- `404`: 订单不存在
- `400`: 订单已支付
- `400`: 订单已取消，无法支付
- `403`: 无权操作此订单

---

### 5. 取消订单
**POST** `/api/order/cancel/{order_id}`

**需要认证**: ✅

**路径参数**:
- `order_id` (int): 订单ID

**响应**: 更新后的订单对象

**错误码**:
- `404`: 订单不存在
- `400`: 订单状态不允许取消
- `403`: 无权操作此订单

---

### 6. 催单
**POST** `/api/order/remind/{order_id}`

**需要认证**: ✅

**路径参数**:
- `order_id` (int): 订单ID

**响应**:
```json
{
  "success": true,
  "message": "催单成功"
}
```

---

### 7. 再次下单
**POST** `/api/order/reorder/{order_id}`

**需要认证**: ✅

**路径参数**:
- `order_id` (int): 订单ID

**响应**: 新创建的订单对象

**说明**: 基于历史订单创建新订单，将历史订单的商品添加到购物车或直接创建订单

---

### 8. 更新订单状态（管理端）
**PUT** `/api/order/status/{order_id}`

**需要认证**: ✅ (管理员)

**路径参数**:
- `order_id` (int): 订单ID

**请求体**:
```json
{
  "order_status": 2  // 订单状态：1-待接单，2-制作中，3-待取餐，4-已完成，5-已取消
}
```

**响应**: 更新后的订单对象

**错误码**:
- `403`: 需要管理员权限
- `404`: 订单不存在

---

### 9. 验证取餐码（管理端）
**POST** `/api/order/verify/{order_id}`

**需要认证**: ✅ (管理员)

**路径参数**:
- `order_id` (int): 订单ID

**查询参数**:
- `pickup_code` (string, 必填): 取餐码

**响应**:
```json
{
  "success": true,
  "message": "取餐码验证成功"
}
```

**错误码**:
- `400`: 取餐码错误
- `404`: 订单不存在

---

## 优惠券

### 1. 获取优惠券列表
**GET** `/api/coupon/list`

**需要认证**: ✅

**响应**:
```json
[
  {
    "coupon_id": 1,
    "name": "优惠券名称",
    "description": "优惠券描述",
    "discount_type": "amount",  // amount-满减，percent-折扣
    "discount_value": 5.0,
    "min_amount": 20.0,
    "valid_start": "2024-01-01T00:00:00",
    "valid_end": "2024-12-31T23:59:59",
    "total_count": 1000,
    "used_count": 100,
    "status": 1
  }
]
```

---

### 2. 领取优惠券
**POST** `/api/coupon/claim/{coupon_id}`

**需要认证**: ✅

**路径参数**:
- `coupon_id` (int): 优惠券ID

**响应**:
```json
{
  "success": true,
  "message": "优惠券领取成功"
}
```

**错误码**:
- `404`: 优惠券不存在
- `400`: 优惠券已领取或已过期
- `400`: 优惠券已领完

---

### 3. 获取我的优惠券
**GET** `/api/coupon/my`

**需要认证**: ✅

**查询参数**:
- `status` (int, 可选): 状态筛选（0-未使用，1-已使用，2-已过期）

**响应**:
```json
[
  {
    "user_coupon_id": 1,
    "coupon_id": 1,
    "status": 0,
    "claim_time": "2024-01-01T10:00:00",
    "coupon": {
      "name": "优惠券名称",
      "discount_value": 5.0,
      "min_amount": 20.0
    }
  }
]
```

---

## 收藏

### 1. 添加收藏
**POST** `/api/favorite/add`

**需要认证**: ✅

**请求体**:
```json
{
  "dish_id": 1  // 菜品ID（必填）
}
```

**响应**: 返回收藏对象

**错误码**:
- `404`: 菜品不存在
- `400`: 已收藏

---

### 2. 获取收藏列表
**GET** `/api/favorite/list`

**需要认证**: ✅

**响应**:
```json
[
  {
    "favorite_id": 1,
    "user_id": 1,
    "dish_id": 1,
    "create_time": "2024-01-01T10:00:00",
    "dish": {
      "dish_id": 1,
      "name": "菜品名称",
      "price": 15.0,
      "image": "图片URL"
    }
  }
]
```

---

### 3. 取消收藏
**DELETE** `/api/favorite/remove`

**需要认证**: ✅

**请求体**:
```json
{
  "dish_id": 1  // 菜品ID（必填）
}
```

**响应**:
```json
{
  "success": true
}
```

---

## 评价

### 1. 创建菜品评价
**POST** `/api/review/create`

**需要认证**: ✅

**请求体**:
```json
{
  "order_id": 1,            // 订单ID（必填）
  "dish_id": 1,             // 菜品ID（必填）
  "rating": 5,              // 评分：1-5（必填）
  "content": "string",      // 评价内容（可选）
  "images": ["url1", "url2"] // 图片URL列表（可选）
}
```

**响应**: 返回评价对象

**错误码**:
- `404`: 订单或菜品不存在
- `400`: 订单未完成，无法评价
- `400`: 已评价过该菜品

---

### 2. 获取菜品评价列表
**GET** `/api/review/list/{dish_id}`

**路径参数**:
- `dish_id` (int): 菜品ID

**响应**:
```json
[
  {
    "review_id": 1,
    "user_id": 1,
    "dish_id": 1,
    "order_id": 1,
    "rating": 5,
    "content": "评价内容",
    "images": ["url1"],
    "create_time": "2024-01-01T10:00:00",
    "user": {
      "nickname": "用户昵称",
      "avatar": "头像URL"
    }
  }
]
```

---

### 3. 创建档口评价
**POST** `/api/review/canteen/create`

**需要认证**: ✅

**请求体**:
```json
{
  "order_id": 1,            // 订单ID（必填）
  "canteen_id": 1,          // 档口ID（必填）
  "rating": 5,              // 总体评分：1-5（必填）
  "service_rating": 5,      // 服务评分：1-5（必填）
  "speed_rating": 5,        // 速度评分：1-5（必填）
  "content": "string",      // 评价内容（可选）
  "images": null            // 图片JSON字符串或null（可选）
}
```

**响应**: 返回档口评价对象

**错误码**:
- `404`: 订单或档口不存在
- `400`: 订单未完成，无法评价

---

### 4. 获取档口评价列表
**GET** `/api/review/canteen/list/{canteen_id}`

**路径参数**:
- `canteen_id` (int): 档口ID

**响应**:
```json
[
  {
    "review_id": 1,
    "user_id": 1,
    "canteen_id": 1,
    "order_id": 1,
    "rating": 5,
    "service_rating": 5,
    "speed_rating": 5,
    "content": "评价内容",
    "create_time": "2024-01-01T10:00:00"
  }
]
```

---

## 浏览历史

### 1. 添加浏览历史
**POST** `/api/history/add/{dish_id}`

**需要认证**: ✅

**路径参数**:
- `dish_id` (int): 菜品ID

**响应**:
```json
{
  "success": true
}
```

---

### 2. 获取浏览历史列表
**GET** `/api/history/list`

**需要认证**: ✅

**响应**:
```json
[
  {
    "history_id": 1,
    "user_id": 1,
    "dish_id": 1,
    "browse_time": "2024-01-01T10:00:00",
    "dish": {
      "dish_id": 1,
      "name": "菜品名称",
      "price": 15.0,
      "image": "图片URL"
    }
  }
]
```

---

## 消息

### 1. 发送站内消息
**POST** `/api/message/send`

**需要认证**: ✅

**请求体**:
```json
{
  "to_user_id": 2,         // 接收用户ID（必填）
  "order_id": 1,           // 关联订单ID（可选）
  "content": "string",     // 消息内容（必填）
  "type": 1                // 消息类型：1-普通消息，2-订单消息（必填）
}
```

**响应**: 返回消息对象

---

### 2. 获取消息列表
**GET** `/api/message/list`

**需要认证**: ✅

**响应**:
```json
[
  {
    "message_id": 1,
    "from_user_id": 1,
    "to_user_id": 2,
    "order_id": 1,
    "content": "消息内容",
    "type": 1,
    "is_read": 0,
    "create_time": "2024-01-01T10:00:00"
  }
]
```

---

## 通知

### 1. 获取未读通知数量
**GET** `/api/notification/unread/count`

**需要认证**: ✅

**响应**:
```json
{
  "count": 5
}
```

---

### 2. 获取最近通知
**GET** `/api/notification/recent`

**需要认证**: ✅

**响应**:
```json
[
  {
    "message_id": 1,
    "user_id": 1,
    "order_id": 1,
    "type": "order_status",
    "title": "订单状态更新",
    "content": "您的订单已开始制作",
    "is_read": 0,
    "create_time": "2024-01-01T10:00:00"
  }
]
```

---

### 3. 标记通知为已读
**POST** `/api/notification/read/{message_id}`

**需要认证**: ✅

**路径参数**:
- `message_id` (int): 通知ID

**响应**:
```json
{
  "success": true
}
```

---

### 4. 标记所有通知为已读
**POST** `/api/notification/read-all`

**需要认证**: ✅

**响应**:
```json
{
  "success": true
}
```

---

### 5. 获取订单相关通知
**GET** `/api/notification/order/{order_id}`

**需要认证**: ✅

**路径参数**:
- `order_id` (int): 订单ID

**响应**: 订单相关的通知列表

---

### 6. 发送系统通知（管理端）
**POST** `/api/notification/send`

**需要认证**: ✅ (管理员)

**请求体**:
```json
{
  "user_id": 1,            // 用户ID（可选，不填则发送给所有用户）
  "title": "系统通知",
  "content": "通知内容",
  "type": "system"
}
```

**响应**:
```json
{
  "success": true,
  "message": "通知发送成功"
}
```

---

## 退款

### 1. 创建退款申请
**POST** `/api/refund/create`

**需要认证**: ✅

**请求体**:
```json
{
  "order_id": 1,           // 订单ID（必填）
  "reason": "string"        // 退款原因（必填）
}
```

**响应**: 返回退款申请对象

**错误码**:
- `404`: 订单不存在
- `400`: 订单状态不允许退款
- `400`: 已申请退款

---

### 2. 获取退款列表
**GET** `/api/refund/list`

**需要认证**: ✅

**响应**:
```json
[
  {
    "refund_id": 1,
    "order_id": 1,
    "refund_status": 0,    // 0-待处理，1-已同意，2-已拒绝
    "reason": "退款原因",
    "create_time": "2024-01-01T10:00:00",
    "order": {
      "order_no": "ORDER20240101001",
      "final_amount": 30.0
    }
  }
]
```

---

### 3. 更新退款状态（管理端）
**PUT** `/api/refund/status/{refund_id}`

**需要认证**: ✅ (管理员)

**路径参数**:
- `refund_id` (int): 退款ID

**请求体**:
```json
{
  "refund_status": 1,      // 1-已同意，2-已拒绝
  "admin_remark": "string" // 管理员备注（可选）
}
```

**响应**: 返回更新后的退款对象

---

## 媒体文件

### 1. 上传媒体文件
**POST** `/api/media/upload`

**需要认证**: ✅

**请求格式**: `multipart/form-data`

**表单字段**:
- `file` (file, 必填): 文件（支持图片、音频、视频）
- `type` (string, 可选): 文件类型（dish-菜品，review-评价）

**响应**:
```json
{
  "file_id": 1,
  "file_url": "http://example.com/media/file.jpg",
  "file_type": "image",
  "file_size": 1024000
}
```

---

### 2. 获取媒体文件
**GET** `/api/media/{file_id}`

**路径参数**:
- `file_id` (int): 文件ID

**响应**: 文件流（直接返回文件内容）

---

### 3. 流式播放媒体
**GET** `/api/media/stream/{file_id}`

**路径参数**:
- `file_id` (int): 文件ID

**响应**: 文件流（支持断点续传）

---

### 4. 获取菜品媒体列表
**GET** `/api/media/dish/{dish_id}`

**路径参数**:
- `dish_id` (int): 菜品ID

**响应**:
```json
[
  {
    "file_id": 1,
    "file_url": "http://example.com/media/file.jpg",
    "file_type": "image",
    "sort_order": 0
  }
]
```

---

## 位置与距离

### 1. 获取档口位置
**GET** `/api/location/canteen/{canteen_id}`

**查询参数**:
- `user_lat` (float, 可选): 用户纬度
- `user_lon` (float, 可选): 用户经度

**路径参数**:
- `canteen_id` (int): 档口ID

**响应**:
```json
{
  "canteen_id": 1,
  "latitude": 30.0,
  "longitude": 120.0,
  "building": "A",
  "floor": "1F",
  "distance": 500.0  // 单位：米（如果提供了用户位置）
}
```

---

### 2. 获取取餐点列表
**GET** `/api/location/pickup`

**响应**:
```json
[
  {
    "pickup_point_id": 1,
    "name": "取餐点1",
    "latitude": 30.0,
    "longitude": 120.0,
    "building": "A",
    "floor": "1F"
  }
]
```

---

### 3. 计算距离
**GET** `/api/location/distance`

**查询参数**:
- `lat1` (float, 必填): 起点纬度
- `lon1` (float, 必填): 起点经度
- `lat2` (float, 必填): 终点纬度
- `lon2` (float, 必填): 终点经度

**响应**:
```json
{
  "distance": 500.0  // 单位：米
}
```

---

## 排队信息

### 1. 获取排队信息
**GET** `/api/canteen/queue/{canteen_id}`

**路径参数**:
- `canteen_id` (int): 档口ID

**响应**:
```json
{
  "canteen_id": 1,
  "current_queue_number": 10,
  "estimated_wait_time": 15,  // 单位：分钟
  "status": "normal"          // normal-正常，busy-繁忙，closed-关闭
}
```

---

### 2. 更新排队信息（管理端）
**POST** `/api/canteen/queue/update`

**需要认证**: ✅ (管理员)

**查询参数**:
- `canteen_id` (int, 必填): 档口ID

**请求体**:
```json
{
  "current_queue_number": 10,
  "estimated_wait_time": 15,
  "status": "normal"
}
```

**响应**: 返回更新后的排队信息

---

## FAQ

### 1. 获取FAQ列表
**GET** `/api/faq/list`

**响应**: 分页格式
```json
{
  "items": [
    {
      "faq_id": 1,
      "question": "常见问题",
      "answer": "问题答案",
      "sort_order": 0,
      "status": 1
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

---

### 2. 获取FAQ详情
**GET** `/api/faq/detail/{faq_id}`

**路径参数**:
- `faq_id` (int): FAQ ID

**响应**: 单个FAQ对象

---

## 活动

### 1. 获取活动列表
**GET** `/api/activity/list`

**响应**:
```json
[
  {
    "activity_id": 1,
    "name": "活动名称",
    "description": "活动描述",
    "activity_type": "discount",  // discount-折扣，full_reduction-满减
    "discount_value": 10.0,
    "min_amount": 50.0,
    "start_time": "2024-01-01T00:00:00",
    "end_time": "2024-12-31T23:59:59",
    "status": 1
  }
]
```

---

## 数据统计

### 1. 获取菜品销量统计
**GET** `/api/statistics/dish/sales`

**需要认证**: ✅ (管理员)

**查询参数**:
- `start_date` (string, 可选): 开始日期（YYYY-MM-DD）
- `end_date` (string, 可选): 结束日期（YYYY-MM-DD）
- `canteen_id` (int, 可选): 档口ID筛选

**响应**:
```json
[
  {
    "dish_id": 1,
    "dish_name": "菜品名称",
    "sales_count": 100,
    "sales_amount": 1500.0
  }
]
```

---

### 2. 获取时段热度统计
**GET** `/api/statistics/time/heat`

**需要认证**: ✅ (管理员)

**查询参数**:
- `date` (string, 可选): 日期（YYYY-MM-DD），默认今天

**响应**:
```json
[
  {
    "hour": 12,
    "order_count": 50,
    "sales_amount": 750.0
  }
]
```

---

### 3. 获取用户偏好统计
**GET** `/api/user/preference`

**需要认证**: ✅

**响应**:
```json
{
  "favorite_categories": [
    {
      "category_id": 1,
      "category_name": "分类名称",
      "count": 10
    }
  ],
  "favorite_dishes": [
    {
      "dish_id": 1,
      "dish_name": "菜品名称",
      "count": 5
    }
  ]
}
```

---

### 4. 获取管理端概览统计
**GET** `/api/statistics/overview`

**需要认证**: ✅ (管理员)

**查询参数**:
- `date` (string, 可选): 日期（YYYY-MM-DD），默认今天

**响应**:
```json
{
  "today_orders": 100,
  "today_sales": 5000.0,
  "today_users": 50,
  "pending_orders": 10
}
```

---

## 数据导出

### 1. 导出订单数据
**GET** `/api/export/orders`

**需要认证**: ✅ (管理员)

**查询参数**:
- `start_date` (string, 可选): 开始日期（YYYY-MM-DD）
- `end_date` (string, 可选): 结束日期（YYYY-MM-DD）
- `format` (string, 可选): 导出格式（csv, excel），默认excel

**响应**: 文件流（Excel或CSV文件）

---

### 2. 导出销售数据
**GET** `/api/export/sales`

**需要认证**: ✅ (管理员)

**查询参数**:
- `start_date` (string, 可选): 开始日期（YYYY-MM-DD）
- `end_date` (string, 可选): 结束日期（YYYY-MM-DD）
- `format` (string, 可选): 导出格式（csv, excel），默认excel

**响应**: 文件流（Excel或CSV文件）

---

## 前端开发建议

### 1. 请求封装
建议封装统一的请求函数，自动处理Token和错误：

```javascript
// 示例：使用 axios
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000
});

// 请求拦截器：自动添加Token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：统一处理错误
api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      // Token过期，跳转登录
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error.response?.data || error.message);
  }
);

export default api;
```

### 2. Token管理
- 登录成功后，将Token存储到`localStorage`或`sessionStorage`
- 每次请求自动携带Token
- Token过期（401）时，清除Token并跳转登录页

### 3. 错误处理
- 统一处理HTTP错误码
- 显示友好的错误提示
- 网络错误时提示用户检查网络连接

### 4. 分页处理
- 使用分页组件统一处理分页逻辑
- 注意分页响应格式：`{items, total, page, page_size}`

### 5. 文件上传
- 使用`FormData`上传文件
- 显示上传进度
- 处理上传失败的情况

### 6. 状态码说明
- `200-299`: 成功
- `400`: 请求参数错误
- `401`: 未认证（Token无效或过期）
- `403`: 无权限（需要管理员权限）
- `404`: 资源不存在
- `422`: 请求参数验证失败
- `500`: 服务器内部错误

---

## 常见问题

### Q1: Token过期怎么办？
A: 当收到401响应时，清除本地Token并跳转到登录页。

### Q2: 如何判断是否需要管理员权限？
A: 如果接口返回403错误，说明需要管理员权限。普通用户无法访问管理端接口。

### Q3: 分页接口的响应格式是什么？
A: 分页接口返回格式为：
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

### Q4: 文件上传如何实现？
A: 使用`multipart/form-data`格式，将文件作为`file`字段上传。

### Q5: 如何获取用户信息？
A: 登录或注册成功后，响应中会返回`userInfo`字段，同时Token存储在响应中的`token`字段。

---

