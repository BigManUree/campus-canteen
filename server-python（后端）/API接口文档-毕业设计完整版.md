# 校园食堂点餐系统后端接口文档

## 1. 文档说明

### 1.1 项目名称
校园食堂点餐系统

### 1.2 后端技术栈
- FastAPI
- SQLAlchemy
- MySQL
- Pydantic
- JWT 鉴权

### 1.3 接口基础地址
本项目后端统一前缀为：

```text
/api
```

例如：
- 用户登录：`/api/auth/login`
- 菜品列表：`/api/dish/list`
- 订单创建：`/api/order/create`

### 1.4 数据格式
- 请求格式：`application/json`
- 返回格式：`application/json`
- 文件上传：`multipart/form-data`

### 1.5 鉴权方式
除公开接口外，大多数接口需要在请求头中携带 Token：

```http
Authorization: Bearer <token>
```

### 1.6 角色说明
系统用户角色主要包括：

- `student`：学生用户
- `merchant`：商家
- `canteen_admin`：食堂管理员
- `admin` / `sys_admin`：系统管理员

### 1.7 通用状态码说明

| 状态码 | 含义 |
|---|---|
| 200 | 请求成功 |
| 400 | 请求参数错误/业务错误 |
| 401 | 未登录或 Token 无效 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 422 | 参数校验失败 |
| 500 | 服务器内部错误 |

### 1.8 文件上传与静态资源访问说明
本项目的上传文件由后端统一保存，并通过 FastAPI 挂载为静态资源目录对外访问。

#### 1）上传文件访问前缀
后端上传目录统一挂载到：

```text
/uploads
```

当上传接口返回文件相对路径后，前端应按以下规则拼接访问地址：

```text
/uploads/{path}
```

例如上传接口返回：

```json
{
  "path": "activities/banner1.png",
  "url": "/uploads/activities/banner1.png"
}
```

则图片实际访问地址为：

```text
/uploads/activities/banner1.png
```

如果带上服务域名，则完整访问地址示例为：

```text
http://127.0.0.1:8000/uploads/activities/banner1.png
```

#### 2）静态资源访问前缀
项目静态资源目录还挂载到：

```text
/static
```

例如：
- 网站图标：`/static/favicon.ico`
- 其他静态资源：`/static/...`

#### 3）图片字段返回规则说明
项目中与图片相关的字段，实际存在两种返回形式，前后端联调时应注意区分：

**第一类：返回相对路径字段**
- 典型字段：`avatar`、`path`、`paths`、部分表模型中的 `images`、`media_path`
- 典型格式：`avatar_1/xxx.png`、`activities/banner1.png`
- 前端使用方式：需自行拼接 `/uploads/` 前缀，或拼接完整域名后访问

**第二类：返回可直接访问的 URL 字段**
- 典型字段：`url`、`urls`、`image_urls`
- 典型格式：`/uploads/activities/banner1.png`
- 前端使用方式：可直接用于图片展示；如果需要完整网络地址，可再拼接服务域名

**第三类：返回完整 URL 的场景**
部分工具函数会将文件路径转换为带域名的完整地址，例如：

```text
http://127.0.0.1:8000/uploads/dishes/demo.png
```

这类完整地址通常出现在图片转换工具函数处理后的结果中，适合前端直接展示。

#### 4）当前项目中常见图片/媒体字段说明

| 字段名 | 所属模块 | 返回形式 | 说明 |
|---|---|---|---|
| `avatar` | 用户信息 | `/uploads/...` 相对访问路径 | 用户头像字段，序列化后会自动补成 `/uploads/` 前缀 |
| `images` | 菜品、评价 | 原始存储字段 | 通常是 JSON 字符串，保存的是相对路径列表，不建议前端直接渲染 |
| `image_urls` | 菜品详情 | 完整 URL 列表 | 由后端计算生成，适合前端直接展示 |
| `image` | 订单评价辅助信息 | 完整 URL | 订单待评价接口中返回的菜品首图 |
| `media_path` | 菜品、评价 | 原始相对路径 | 音视频存储路径，通常需结合下载/播放接口使用 |
| `url` | 上传接口返回 | `/uploads/...` 路径 | 单文件上传后常见返回字段 |
| `urls` | 批量上传接口返回 | `/uploads/...` 列表 | 多文件上传后常见返回字段 |
| `path` / `paths` | 上传接口返回 | 原始相对路径 | 用于数据库存储或后续提交业务接口 |

#### 5）与图片/媒体直接相关的接口

**活动图片上传**
- `POST /api/activity/upload/image`
- `POST /api/activity/upload/images`
- 返回：`path` / `url` 或 `paths` / `urls`

**用户头像上传**
- `POST /api/media/upload/avatar`
- 返回：`path`、`url`

**菜品图片上传**
- `POST /api/media/upload/images`
- 返回：`paths`、`urls`

**评价图片上传**
- `POST /api/media/upload/review`
- 创建评价前上传图片
- 返回：`paths`、`urls`

- `POST /api/media/review/upload/images`
- 评价创建后继续上传图片
- 返回：`paths`、`count`

**菜品媒体文件上传**
- `POST /api/media/upload`
- 上传菜品音频/视频文件
- 返回：`path`

**评价媒体文件上传**
- `POST /api/media/review/upload`
- 上传评价音频/视频文件
- 返回：`path`

**菜品图片获取**
- `GET /api/media/dish/{dish_id}/images`
- 返回：`images`，为可直接访问的图片 URL 列表

**媒体下载与播放**
- `GET /api/media/download/{file_path}`：下载文件
- `GET /api/media/stream/{file_path}`：在线播放音视频

#### 6）前端对接建议
- 数据库存储时优先使用 `path` 或 `paths`
- 页面展示图片时优先使用 `url`、`urls`、`image_urls`、`image`
- 若接口只返回原始相对路径，应手动补全为 `/uploads/{path}`
- 对于 `images` 这类 JSON 字符串字段，前端应先解析后再渲染

### 1.9 全局异常返回格式
参数校验失败时，后端统一可能返回：

```json
{
  "code": "VALIDATION_ERROR",
  "message": "请求参数验证失败",
  "errors": [
    "body -> username: Field required"
  ]
}
```

系统异常时可能返回：

```json
{
  "code": "INTERNAL_ERROR",
  "message": "服务器内部错误，请稍后重试"
}
```

---

# 2. 公共接口

---

## 2.1 根路径
### 接口地址
`GET /`

### 功能说明
访问根路径时自动跳转到在线文档页面 `/docs`。

---

## 2.2 健康检查
### 接口地址
`GET /health`

### 功能说明
用于检查服务是否正常运行。

### 返回示例
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

# 3. 认证模块

模块前缀：`/api/auth`

---

## 3.1 用户注册
### 接口地址
`POST /api/auth/register`

### 功能说明
用户注册接口。默认注册为学生角色；如果系统内尚无管理员，则第一个注册用户自动成为管理员。

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |
| phone | string | 否 | 手机号 |
| email | string | 否 | 邮箱 |
| nickname | string | 否 | 昵称 |

### 请求示例
```json
{
  "username": "zhangsan",
  "password": "123456",
  "phone": "13800138000",
  "email": "zhangsan@qq.com",
  "nickname": "张三"
}
```

### 返回参数

| 参数名 | 类型 | 说明 |
|---|---|---|
| token | string | 登录令牌 |
| expireIn | int | 过期时间，单位秒 |
| userInfo | object | 用户信息 |

### 返回示例
```json
{
  "token": "eyJhbGciOi...",
  "expireIn": 7200,
  "userInfo": {
    "user_id": 1,
    "username": "zhangsan",
    "role": "student"
  }
}
```

---

## 3.2 用户登录
### 接口地址
`POST /api/auth/login`

### 功能说明
用户使用用户名和密码进行登录。

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

### 请求示例
```json
{
  "username": "zhangsan",
  "password": "123456"
}
```

### 返回示例
```json
{
  "token": "eyJhbGciOi...",
  "expireIn": 7200,
  "userInfo": {
    "user_id": 1,
    "username": "zhangsan",
    "role": "student"
  }
}
```

---

## 3.3 忘记密码
### 接口地址
`POST /api/auth/forgot-password`

### 功能说明
根据用户名发送密码重置验证码。

### 请求参数
查询参数：

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| username | string | 是 | 用户名 |

### 返回示例
```json
{
  "success": true,
  "message": "验证码已发送"
}
```

---

## 3.4 重置密码
### 接口地址
`POST /api/auth/reset-password`

### 功能说明
通过验证码重置密码。

### 请求参数
查询参数：

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| username | string | 是 | 用户名 |
| verification_code | string | 是 | 验证码 |
| new_password | string | 是 | 新密码 |

### 返回示例
```json
{
  "success": true,
  "message": "密码重置成功"
}
```

---

## 3.5 创建商家账号
### 接口地址
`POST /api/auth/create-merchant`

### 权限
管理员

### 功能说明
管理员创建商家账号，可选同时绑定档口。

### 请求参数
请求体同用户注册，另有查询参数：

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| canteen_id | int | 否 | 绑定的档口ID |

### 返回示例
```json
{
  "token": "eyJhbGciOi...",
  "expireIn": 7200,
  "userInfo": {
    "user_id": 10,
    "username": "merchant01",
    "role": "merchant"
  }
}
```

---

## 3.6 注册管理员
### 接口地址
`POST /api/auth/register-admin`

### 功能说明
通过管理员密钥注册管理员账号。

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| admin_key | string | 是 | 管理员注册密钥 |

请求体同用户注册。

---

# 4. 用户模块

模块前缀：`/api/user`

---

## 4.1 获取当前用户信息
### 接口地址
`GET /api/user/info`

### 权限
已登录用户

### 返回说明
返回当前登录用户完整信息。

---

## 4.2 修改当前用户信息
### 接口地址
`PUT /api/user/info`

### 权限
已登录用户

### 请求参数
`UserUpdate`，通常包括：

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| nickname | string | 否 | 昵称 |
| phone | string | 否 | 手机号 |
| email | string | 否 | 邮箱 |
| avatar | string | 否 | 头像 |
| gender | int/string | 否 | 性别 |
| student_no | string | 否 | 学号 |
| department | string | 否 | 院系 |

---

## 4.3 用户列表
### 接口地址
`GET /api/user/list`

### 权限
管理员

### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| pageNum | int | 否 | 页码，默认1 |
| pageSize | int | 否 | 每页数量，默认20 |
| keyword | string | 否 | 搜索关键词 |
| role | string | 否 | 角色筛选 |
| status | int | 否 | 状态筛选：0禁用，1启用 |

### 返回说明
返回后台分页格式，包含：
- 用户ID
- 用户名
- 手机号
- 邮箱
- 角色
- 状态
- 订单数量
- 创建时间等

---

## 4.4 用户详情
### 接口地址
`GET /api/user/detail/{user_id}`

### 权限
管理员

---

## 4.5 更新指定用户
### 接口地址
`PUT /api/user/update/{user_id}`

### 权限
管理员

---

## 4.6 修改用户状态
### 接口地址
`PUT /api/user/status/{user_id}`

### 权限
管理员

### 请求参数
```json
{
  "status": 1
}
```

### 说明
- `0`：禁用
- `1`：启用

---

## 4.7 修改用户角色
### 接口地址
`PUT /api/user/role/{user_id}`

### 权限
管理员

### 请求参数
```json
{
  "role": "merchant"
}
```

---

## 4.8 修改密码
### 接口地址
`POST /api/user/change-password`

### 权限
已登录用户

### 请求参数
查询参数：

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| old_password | string | 是 | 原密码 |
| new_password | string | 是 | 新密码 |

---

## 4.9 删除用户
### 接口地址
`DELETE /api/user/{user_id}`

### 权限
管理员

---

# 5. 档口模块

模块前缀：`/api/canteen`

---

## 5.1 获取当前商家绑定档口
### 接口地址
`GET /api/canteen/my`

### 权限
商家

### 功能说明
商家获取自己所管理的档口信息。

---

## 5.2 获取档口列表
### 接口地址
`GET /api/canteen/list`

### 功能说明
支持分页、关键词搜索、状态筛选。

### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| keyword | string | 否 | 档口名称关键词 |
| status | int | 否 | 0禁用，1启用 |

### 返回示例
```json
{
  "items": [],
  "total": 20,
  "page": 1,
  "page_size": 20
}
```

---

## 5.3 获取档口详情
### 接口地址
`GET /api/canteen/detail/{canteen_id}`

---

## 5.4 绑定商家账号到档口
### 接口地址
`POST /api/canteen/assign-merchant/{canteen_id}`

### 权限
管理员

### 参数
查询参数：

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| merchant_user_id | int | 是 | 商家用户ID |

---

## 5.5 创建档口
### 接口地址
`POST /api/canteen/create`

### 权限
管理员

### 请求体
`CanteenCreate`

常见字段包括：
- `canteen_name`
- `address`
- `building`
- `floor`
- `window_no`
- `latitude`
- `longitude`
- `status`

---

## 5.6 更新档口
### 接口地址
`PUT /api/canteen/update/{canteen_id}`

### 权限
管理员

---

## 5.7 修改档口状态
### 接口地址
`PUT /api/canteen/status/{canteen_id}`

### 权限
管理员

### 参数
查询参数：
- `status=0/1`

---

## 5.8 删除档口
### 接口地址
`DELETE /api/canteen/delete/{canteen_id}`

### 权限
管理员

### 说明
删除档口及其关联数据。

---

## 5.9 批量修改档口状态
### 接口地址
`POST /api/canteen/batch/status`

### 请求示例
```json
{
  "canteen_ids": [1, 2, 3],
  "status": 1
}
```

---

## 5.10 批量删除档口
### 接口地址
`POST /api/canteen/batch/delete`

### 请求示例
```json
{
  "canteen_ids": [1, 2, 3]
}
```

---

# 6. 菜品模块

模块前缀：`/api/dish`

---

## 6.1 获取菜品列表
### 接口地址
`GET /api/dish/list`

### 功能说明
支持分页、筛选、排序。

### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| canteen_id | int | 否 | 档口ID |
| category_id | int | 否 | 分类ID |
| keyword | string | 否 | 搜索关键词 |
| status | int | 否 | 状态：0下架，1上架 |
| sort_by | string | 否 | 排序字段 |
| order | string | 否 | asc / desc |
| _t | int | 否 | 时间戳，防缓存 |

### 排序字段支持
- `sales`
- `sales_count`
- `price`
- `view_count`
- `favorite_count`
- `create_time`

---

## 6.2 获取菜品详情
### 接口地址
`GET /api/dish/detail/{dish_id}`

### 功能说明
- 返回菜品详情
- 自动增加浏览量
- 登录状态下自动记录浏览历史

---

## 6.3 创建菜品
### 接口地址
`POST /api/dish/create`

### 权限
商家/管理员

### 请求体
`DishCreate`

常见字段包括：
- `name`
- `price`
- `original_price`
- `description`
- `images`
- `canteen_id`
- `category_id`
- `stock`
- `status`

---

## 6.4 更新菜品
### 接口地址
`PUT /api/dish/update/{dish_id}`

### 权限
商家/管理员

---

## 6.5 修改菜品状态
### 接口地址
`PUT /api/dish/status/{dish_id}`

### 权限
商家/管理员

### 请求示例
```json
{
  "status": 1
}
```

---

## 6.6 管理端菜品列表
### 接口地址
`GET /api/dish/admin/list`

### 权限
商家/管理员

### 查询参数
- `page`
- `page_size`
- `canteen_id`
- `category_id`
- `status`
- `keyword`

---

## 6.7 删除菜品
### 接口地址
`DELETE /api/dish/delete/{dish_id}`

---

## 6.8 库存预警
### 接口地址
`GET /api/dish/stock/warning`

### 权限
商家/管理员

---

## 6.9 批量更新菜品状态
### 接口地址
`POST /api/dish/batch/status`

---

## 6.10 批量删除菜品
### 接口地址
`POST /api/dish/batch/delete`

---

## 6.11 批量调整菜品价格
### 接口地址
`POST /api/dish/batch/price`

---

## 6.12 批量导出菜品
### 接口地址
`POST /api/dish/batch/export`

---

# 7. 订单模块

模块前缀：`/api/order`

---

## 7.1 创建订单
### 接口地址
`POST /api/order/create`

### 权限
已登录用户

### 请求体
`OrderCreate`

一般包含：
- 档口ID
- 订单类型
- 菜品列表
- 收货地址/自提点
- 优惠券信息
- 备注

### 返回
`OrderOut`

---

## 7.2 获取我的订单列表
### 接口地址
`GET /api/order/list`

### 权限
已登录用户

---

## 7.3 管理端订单列表
### 接口地址
`GET /api/order/admin/list`

### 权限
商家/管理员

### 查询参数

| 参数名 | 类型 | 说明 |
|---|---|---|
| pageNum | int | 页码 |
| pageSize | int | 每页数量 |
| orderNo | string | 订单号 |
| userId | int | 用户ID |
| stallId | int | 档口ID |
| status | int | 订单状态 |
| paymentStatus | int | 支付状态 |
| startTime | datetime | 开始时间 |
| endTime | datetime | 结束时间 |

---

## 7.4 获取订单详情
### 接口地址
`GET /api/order/detail/{order_id}`

### 权限
订单本人/商家/管理员

---

## 7.5 获取订单时间线
### 接口地址
`GET /api/order/timeline/{order_id}`

### 功能说明
展示订单从创建到完成或取消的流转过程。

### 状态说明

| 状态值 | 状态名称 |
|---|---|
| 0 | 待确认 |
| 1 | 制作中 |
| 2 | 待取餐 |
| 3 | 配送中 |
| 4 | 已完成 |
| 5 | 已取消 |

---

## 7.6 更新订单状态
### 接口地址
`PUT /api/order/status/{order_id}`

### 权限
商家/管理员

### 请求体
```json
{
  "order_status": 1
}
```

### 状态流转规则
- 待确认 → 制作中 / 已取消
- 制作中 → 待取餐 / 已取消
- 待取餐 → 配送中 / 已完成
- 配送中 → 已完成

---

## 7.7 取消订单
### 接口地址
`POST /api/order/cancel/{id}`

### 请求体
```json
{
  "reason": "临时不需要了"
}
```

---

# 8. 购物车模块

模块前缀：`/api/cart`

---

## 8.1 获取购物车列表
### 接口地址
`GET /api/cart/list`

---

## 8.2 添加购物车商品
### 接口地址
`POST /api/cart/add`

### 请求体
```json
{
  "dish_id": 1,
  "quantity": 2,
  "remark": "少辣"
}
```

---

## 8.3 更新购物车商品
### 接口地址
`PUT /api/cart/update/{item_id}`

### 请求体
```json
{
  "quantity": 3,
  "remark": "不要香菜"
}
```

---

## 8.4 删除购物车商品
### 接口地址
`DELETE /api/cart/remove/{item_id}`

---

# 9. 地址模块

模块前缀：`/api/address`

---

## 9.1 地址列表
### 接口地址
`GET /api/address/list`

---

## 9.2 新增地址
### 接口地址
`POST /api/address/create`

### 请求体
常见字段：
- `receiver_name`
- `phone`
- `address`
- `detail`
- `is_default`

---

## 9.3 修改地址
### 接口地址
`PUT /api/address/update/{address_id}`

---

## 9.4 删除地址
### 接口地址
`DELETE /api/address/delete/{address_id}`

---

# 10. 分类模块

模块前缀：`/api/category`

---

## 10.1 分类分页列表
### 接口地址
`GET /api/category/list`

### 查询参数
- `parent_id`
- `page`
- `page_size`

---

## 10.2 所有分类树结构
### 接口地址
`GET /api/category/all`

---

## 10.3 分类详情
### 接口地址
`GET /api/category/detail/{category_id}`

---

## 10.4 创建分类
### 接口地址
`POST /api/category/create`

### 权限
管理员

### 请求体
```json
{
  "category_name": "盖浇饭",
  "parent_id": 0,
  "sort_order": 1
}
```

---

## 10.5 更新分类
### 接口地址
`PUT /api/category/update/{category_id}`

---

## 10.6 删除分类
### 接口地址
`DELETE /api/category/delete/{category_id}`

### 说明
若存在子分类，不允许删除。

---

# 11. 优惠券模块

模块前缀：`/api/coupon`

---

## 11.1 获取可领取优惠券列表
### 接口地址
`GET /api/coupon/list`

---

## 11.2 获取我的优惠券
### 接口地址
`GET /api/coupon/my`

### 查询参数

| 参数值 | 说明 |
|---|---|
| available / 0 | 可用 |
| used / 1 | 已使用 |
| expired / 2 | 已过期 |

---

## 11.3 领取优惠券
### 接口地址
`POST /api/coupon/claim/{coupon_id}`

---

## 11.4 创建优惠券
### 接口地址
`POST /api/coupon/create`

### 权限
管理员

---

## 11.5 更新优惠券
### 接口地址
`PUT /api/coupon/update/{coupon_id}`

---

## 11.6 修改优惠券状态
### 接口地址
`PUT /api/coupon/status/{coupon_id}`

### 请求示例
```json
{
  "status": 1
}
```

---

## 11.7 删除优惠券
### 接口地址
`DELETE /api/coupon/delete/{coupon_id}`

---

# 12. 收藏模块

模块前缀：`/api/favorite`

---

## 12.1 添加收藏
### 接口地址
`POST /api/favorite/add`

### 请求体
```json
{
  "dish_id": 1
}
```

---

## 12.2 取消收藏
### 支持以下三种方式

#### 方式1
`DELETE /api/favorite/remove/{dish_id}`

#### 方式2
`DELETE /api/favorite/remove?dish_id=1`

#### 方式3
`POST /api/favorite/remove`

请求体：
```json
{
  "dish_id": 1
}
```

---

## 12.3 检查收藏状态
### 接口地址
`GET /api/favorite/check/{dish_id}`

### 返回示例
```json
{
  "is_favorite": true,
  "favorite_id": 15
}
```

---

## 12.4 获取收藏列表
### 接口地址
`GET /api/favorite/list`

### 查询参数
- `page`
- `page_size`

---

# 13. 菜品评价模块

模块前缀：`/api/review`

---

## 13.1 创建评价
### 接口地址
`POST /api/review/create`

### 权限
已登录用户

### 请求体
```json
{
  "order_id": 1,
  "dish_id": 2,
  "rating": 5,
  "content": "很好吃",
  "images": "a.jpg,b.jpg",
  "media_path": "",
  "media_type": ""
}
```

### 业务规则
- 必须是本人订单
- 订单中必须包含该菜品
- 同一订单下同一菜品不能重复评价

---

## 13.2 菜品评价列表
### 接口地址
`GET /api/review/list/{dish_id}`

### 查询参数
- `page`
- `page_size`
- `rating`

---

## 13.3 获取订单待评价信息
### 接口地址
`GET /api/review/order/{order_id}`

### 功能说明
返回订单下的菜品列表及是否已评价状态。

---

## 13.4 管理端评价列表
### 接口地址
`GET /api/review/admin/list`

### 权限
管理员

### 查询参数
- `page`
- `page_size`
- `dish_id`
- `user_id`
- `rating`
- `keyword`

---

## 13.5 管理端删除评价
### 接口地址
`DELETE /api/review/admin/{review_id}`

### 权限
管理员

---

# 14. 档口评价模块

模块前缀：`/api/review/canteen`

---

## 14.1 创建档口评价
### 接口地址
`POST /api/review/canteen/create`

### 请求体
```json
{
  "order_id": 1,
  "canteen_id": 2,
  "rating": 5,
  "content": "服务很好"
}
```

---

## 14.2 获取档口评价列表
### 接口地址
`GET /api/review/canteen/list/{canteen_id}`

---

# 15. 消息模块

模块前缀：`/api/message`

---

## 15.1 获取消息列表
### 接口地址
`GET /api/message/list`

---

## 15.2 获取未读消息数
### 接口地址
`GET /api/message/unread-count`

### 返回示例
```json
{
  "unread_count": 5
}
```

---

## 15.3 标记单条消息已读
### 接口地址
`PUT /api/message/{message_id}/read`

---

## 15.4 全部消息标记已读
### 接口地址
`PUT /api/message/read-all`

---

## 15.5 删除单条消息
### 接口地址
`DELETE /api/message/{message_id}`

---

## 15.6 批量删除消息
### 接口地址
`DELETE /api/message/batch/delete`

### 参数
- `message_ids: list[int]`

---

## 15.7 清空全部消息
### 接口地址
`DELETE /api/message/clear`

---

## 15.8 发送消息
### 接口地址
`POST /api/message/send`

### 请求体
一般包括：
- `to_user_id`
- `title`
- `content`
- `message_type`

---

# 16. 通知模块

模块前缀：`/api/notification`

---

## 16.1 获取最近通知
### 接口地址
`GET /api/notification/recent`

### 查询参数
- `page`
- `page_size`
- `is_read`

---

## 16.2 获取通知列表
### 接口地址
`GET /api/notification/list`

### 查询参数
- `pageNum`
- `pageSize`
- `readStatus`
- `notification_type`
- `category`

---

## 16.3 获取未读通知数量
### 接口地址
`GET /api/notification/unread-count`

---

## 16.4 获取通知统计
### 接口地址
`GET /api/notification/statistics`

### 返回内容
- 总数
- 未读数
- 已读数
- 今日新增
- 分类统计

---

## 16.5 标记通知为已读
### 接口地址
`POST /api/notification/mark-read`

### 请求示例
```json
{
  "notification_ids": [1, 2, 3]
}
```

如果传空或 `null`，表示全部已读。

---

## 16.6 删除通知
### 接口地址
`DELETE /api/notification/{notification_id}`

---

## 16.7 管理员发送通知
### 接口地址
`POST /api/notification/send`

### 权限
管理员

### 请求示例
```json
{
  "user_ids": [1, 2],
  "role": "student",
  "title": "系统通知",
  "message": "系统将于今晚维护",
  "notification_type": "normal",
  "category": "system",
  "related_id": 0,
  "priority": 0
}
```

---

# 17. 退款模块

模块前缀：`/api/refund`

---

## 17.1 创建退款申请
### 接口地址
`POST /api/refund/create`

### 请求体
```json
{
  "order_id": 1,
  "reason": "菜品质量问题",
  "reason_category": "quality",
  "refund_items": [
    {
      "dish_id": 2,
      "quantity": 1
    }
  ]
}
```

### 说明
- 不传 `refund_items`：整单退款
- 传 `refund_items`：部分退款

---

## 17.2 管理端退款列表
### 接口地址
`GET /api/refund/admin/list`

### 权限
管理员/商家

### 查询参数
- `pageNum`
- `pageSize`
- `refundStatus`
- `orderNo`
- `userId`
- `startTime`
- `endTime`

---

## 17.3 管理端退款详情
### 接口地址
`GET /api/refund/admin/detail/{refund_id}`

---

## 17.4 审核退款
### 接口地址
`POST /api/refund/admin/audit/{refund_id}`

### 请求示例
```json
{
  "action": "approve",
  "admin_remark": "同意退款"
}
```

### `action` 取值
- `approve`
- `reject`

---

## 17.5 获取我的退款列表
### 接口地址
`GET /api/refund/list`

### 查询参数
- `status`
- `limit`
- `offset`

---

## 17.6 获取退款统计
### 接口地址
`GET /api/refund/statistics`

### 查询参数
- `days`

---

## 17.7 获取退款详情
### 接口地址
`GET /api/refund/{refund_id}`

---

# 18. 统计模块

模块前缀：`/api/statistics`

---

## 18.1 后台看板汇总
### 接口地址
`GET /api/statistics/dashboard`

### 权限
商家/管理员

### 返回内容
- 今日订单数
- 今日销售额
- 今日新增用户数
- 待处理订单数
- 待退款数
- 启用档口数

---

## 18.2 后台销售趋势
### 接口地址
`GET /api/statistics/sales/trend-admin`

### 查询参数
- `mode`：`day/week/month`
- `startTime`
- `endTime`

---

## 18.3 菜品销量排行
### 接口地址
`GET /api/statistics/ranking/dishes`

### 查询参数
- `limit`
- `startTime`
- `endTime`

---

## 18.4 档口销量排行
### 接口地址
`GET /api/statistics/ranking/stalls`

### 查询参数
- `limit`
- `startTime`
- `endTime`

---

## 18.5 用户增长统计
### 接口地址
`GET /api/statistics/users/growth`

---

## 18.6 退款汇总
### 接口地址
`GET /api/statistics/refund/summary`

---

## 18.7 系统总览
### 接口地址
`GET /api/statistics/overview`

---

## 18.8 菜品销量统计
### 接口地址
`GET /api/statistics/dish/sales`

### 查询参数
- `start_date`
- `end_date`
- `limit`

---

## 18.9 时间热度统计
### 接口地址
`GET /api/statistics/time/heat`

### 查询参数
- `date`

---

## 18.10 用户偏好统计
### 接口地址
`GET /api/statistics/user/preference`

### 查询参数
- `limit`

---

## 18.11 销售趋势统计
### 接口地址
`GET /api/statistics/sales/trend`

### 查询参数
- `days`

---

# 19. 导出模块

模块前缀：`/api/statistics/export`

> 说明：代码中该模块存在缩进异常，但从实现意图看接口设计如下。

---

## 19.1 导出订单数据
### 接口地址
`GET /api/statistics/export/orders`

### 查询参数

| 参数名 | 类型 | 说明 |
|---|---|---|
| start_date | string | 开始日期，格式 YYYY-MM-DD |
| end_date | string | 结束日期，格式 YYYY-MM-DD |
| order_status | int | 订单状态 |
| pay_status | int | 支付状态 |
| canteen_id | int | 档口ID |
| format | string | 导出格式：csv / excel |

### 返回说明
返回文件流下载。

---

# 20. 活动模块

模块前缀：`/api/activity`

---

## 20.1 获取活动列表
### 接口地址
`GET /api/activity/list`

### 说明
- 普通用户：仅返回启用活动
- 管理员：返回全部活动

---

## 20.2 管理端活动列表
### 接口地址
`GET /api/activity/admin/list`

---

## 20.3 创建活动
### 接口地址
`POST /api/activity/create`

### 权限
管理员

---

## 20.4 更新活动
### 接口地址
`PUT /api/activity/update/{activity_id}`

---

## 20.5 修改活动状态
### 接口地址
`PUT /api/activity/status/{activity_id}`

### 请求示例
```json
{
  "status": 1
}
```

---

## 20.6 删除活动
### 接口地址
`DELETE /api/activity/delete/{activity_id}`

---

## 20.7 上传活动图片
### 接口地址
`POST /api/activity/upload/image`

### 请求格式
`multipart/form-data`

### 参数
- `file`
- `activity_id` 可选

---

## 20.8 批量上传活动图片
### 接口地址
`POST /api/activity/upload/images`

### 请求格式
`multipart/form-data`

### 参数
- `files`
- `activity_id` 可选

---

# 21. FAQ 模块

模块前缀：`/api/faq`

---

## 21.1 FAQ 列表
### 接口地址
`GET /api/faq/list`

### 查询参数
- `category`
- `page`
- `page_size`

---

## 21.2 FAQ 详情
### 接口地址
`GET /api/faq/detail/{faq_id}`

### 功能说明
查看详情时自动增加浏览次数。

---

## 21.3 创建 FAQ
### 接口地址
`POST /api/faq/create`

### 权限
管理员

---

## 21.4 更新 FAQ
### 接口地址
`PUT /api/faq/update/{faq_id}`

---

## 21.5 删除 FAQ
### 接口地址
`DELETE /api/faq/delete/{faq_id}`

---

# 22. 排队信息模块

模块前缀：`/api/canteen/queue`

---

## 22.1 获取排队信息
### 接口地址
`GET /api/canteen/queue/{canteen_id}`

### 功能说明
获取指定档口当前排队信息。若不存在记录，则返回默认值。

---

## 22.2 更新排队信息
### 接口地址
`POST /api/canteen/queue/update`

### 权限
商家/管理员

### 请求参数
请求体中或查询参数中提供 `canteen_id`。

### 请求示例
```json
{
  "canteen_id": 1,
  "current_queue_number": 25,
  "estimated_wait_time": 15,
  "status": "normal"
}
```

---

## 22.3 路径方式更新排队信息
### 接口地址
`PUT /api/canteen/queue/update/{canteen_id}`

---

# 23. 搜索模块

模块前缀：`/api/search`

---

## 23.1 综合搜索
### 接口地址
`GET /api/search/all`

### 查询参数

| 参数名 | 类型 | 说明 |
|---|---|---|
| keyword | string | 搜索关键词 |
| type | string | `dish` / `canteen` / `all` |
| page | int | 页码 |
| page_size | int | 每页数量 |

### 功能说明
- 支持搜索菜品和档口
- 自动记录搜索历史
- 自动更新热门搜索

---

## 23.2 搜索建议
### 接口地址
`GET /api/search/suggest`

### 查询参数
- `keyword`
- `limit`

---

## 23.3 热门搜索
### 接口地址
`GET /api/search/hot`

### 查询参数
- `limit`

---

## 23.4 获取搜索历史
### 接口地址
`GET /api/search/history`

### 查询参数
- `limit`

---

## 23.5 添加搜索历史
### 接口地址
`POST /api/search/history`

### 请求示例
```json
{
  "keyword": "宫保鸡丁",
  "search_type": "dish"
}
```

---

## 23.6 清空搜索历史
### 接口地址
`DELETE /api/search/history`

---

# 24. 浏览历史模块

模块前缀：`/api/browse`

---

## 24.1 获取浏览历史
### 接口地址
`GET /api/browse/history`

### 查询参数
- `page`
- `page_size`

---

## 24.2 添加浏览历史
### 接口地址
`POST /api/browse/add/{dish_id}`

---

## 24.3 清空浏览历史
### 接口地址
`DELETE /api/browse/clear`

---

## 24.4 删除单条浏览记录
### 接口地址
`DELETE /api/browse/remove/{dish_id}`

---

# 25. 历史记录模块

模块前缀：`/api/history`

> 该模块与浏览历史存在部分功能重叠，疑似旧版接口。

---

## 25.1 获取历史记录
### 接口地址
`GET /api/history/list`

---

## 25.2 添加历史记录
### 接口地址
`POST /api/history/add/{dish_id}`

---

# 26. 定位模块

模块前缀：`/api/location`

---

## 26.1 获取档口位置信息
### 接口地址
`GET /api/location/canteen/{canteen_id}`

### 查询参数
- `user_lat`
- `user_lon`

### 返回内容
- 档口经纬度
- 地址
- 若传入用户位置则返回距离与距离文本

---

## 26.2 获取自提点列表
### 接口地址
`GET /api/location/pickup`

---

## 26.3 计算两点间距离
### 接口地址
`GET /api/location/distance`

### 查询参数
- `lat1`
- `lon1`
- `lat2`
- `lon2`

---

# 27. 权限说明汇总

## 27.1 公开接口
无需登录即可访问的典型接口有：
- 健康检查
- 档口列表/详情
- 菜品列表/详情
- 分类列表
- FAQ 列表/详情
- 定位接口
- 活动列表

## 27.2 普通用户接口
需登录：
- 个人信息
- 地址管理
- 购物车
- 订单创建/查询
- 收藏
- 评价
- 消息通知
- 优惠券领取
- 退款申请
- 搜索历史
- 浏览历史

## 27.3 商家接口
需商家或管理员权限：
- 我的档口
- 菜品管理
- 订单管理
- 排队信息维护
- 商家统计
- 退款审核

## 27.4 管理员接口
仅管理员：
- 用户管理
- 档口管理
- 分类管理
- 优惠券管理
- FAQ 管理
- 活动管理
- 全局统计
- 发送系统通知
- 评价管理

---

# 28. 数据库业务状态说明

## 28.1 订单状态

| 值 | 说明 |
|---|---|
| 0 | 待确认 |
| 1 | 制作中 |
| 2 | 待取餐 |
| 3 | 配送中 |
| 4 | 已完成 |
| 5 | 已取消 |

## 28.2 支付状态

| 值 | 说明 |
|---|---|
| 0 | 未支付 |
| 1 | 已支付 |

## 28.3 菜品状态

| 值 | 说明 |
|---|---|
| 0 | 下架 |
| 1 | 上架 |
| -1 | 已删除（逻辑过滤） |

## 28.4 档口状态

| 值 | 说明 |
|---|---|
| 0 | 禁用 |
| 1 | 启用 |

## 28.5 优惠券状态

| 值 | 说明 |
|---|---|
| 0 | 禁用 |
| 1 | 启用 |

## 28.6 退款状态

| 值 | 说明 |
|---|---|
| pending | 待审核 |
| approved | 已通过 |
| rejected | 已拒绝 |
| completed | 已完成 |

---

# 29. 文档结论

本系统后端接口已覆盖校园食堂点餐业务中的主要功能模块，包括：

- 用户认证与权限管理
- 档口与菜品管理
- 购物车与订单处理
- 收藏、评价、浏览与搜索
- 消息通知与退款
- 数据统计与导出
- FAQ、活动、定位与排队管理

整体上形成了较完整的校园外卖/食堂点餐业务闭环，能够满足学生点餐、商家接单、管理员管理和系统统计分析等多角色业务需求。

